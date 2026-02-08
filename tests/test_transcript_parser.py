"""
Unit tests for transcript parsing functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from shoemaker_elves.transcript_parser import parse_transcript


@pytest.fixture
def fixtures_dir():
    """Get the fixtures directory path."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_transcript():
    """Create a temporary transcript file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        yield f.name
    Path(f.name).unlink(missing_ok=True)


class TestTranscriptParserBasics:
    """Test basic transcript parsing functionality."""

    def test_parse_success_transcript(self, fixtures_dir):
        """Test parsing a successful task transcript."""
        transcript_path = fixtures_dir / "sample_transcript_success.jsonl"
        result = parse_transcript(str(transcript_path))

        assert result["success"] is True
        assert result["errors"] == []
        assert len(result["files_modified"]) == 2
        assert "/tmp/auth.py" in result["files_modified"]
        assert "/tmp/config.py" in result["files_modified"]
        assert result["tool_calls"] == 2  # Write and Edit
        assert result["input_tokens"] > 0
        assert result["output_tokens"] > 0
        assert result["cost_usd"] > 0
        assert "authentication feature" in result["summary"].lower()

    def test_parse_transcript_with_errors(self, fixtures_dir):
        """Test parsing a transcript with errors."""
        transcript_path = fixtures_dir / "sample_transcript_with_errors.jsonl"
        result = parse_transcript(str(transcript_path))

        assert result["success"] is False
        assert len(result["errors"]) == 2
        assert any("File not found" in err for err in result["errors"])
        assert any("command not found" in err for err in result["errors"])
        assert result["tool_calls"] == 2
        assert result["files_modified"] == []

    def test_parse_complex_transcript(self, fixtures_dir):
        """Test parsing a complex transcript with multiple tool calls."""
        transcript_path = fixtures_dir / "sample_transcript_complex.jsonl"
        result = parse_transcript(str(transcript_path))

        assert result["success"] is True
        assert result["errors"] == []
        assert len(result["files_modified"]) == 5
        # Three Write calls
        assert "/project/auth/base.py" in result["files_modified"]
        assert "/project/auth/providers.py" in result["files_modified"]
        assert "/project/auth/__init__.py" in result["files_modified"]
        # One Edit call
        assert "/project/main.py" in result["files_modified"]
        # One NotebookEdit call
        assert "/project/experiments.ipynb" in result["files_modified"]
        assert result["tool_calls"] == 6  # 3 Write + 1 Bash + 1 Edit + 1 NotebookEdit
        assert result["input_tokens"] > 10000
        assert result["output_tokens"] > 2000


class TestTranscriptParserEdgeCases:
    """Test edge cases and error handling."""

    def test_nonexistent_transcript(self):
        """Test parsing a nonexistent transcript file."""
        result = parse_transcript("/nonexistent/transcript.jsonl")

        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert "Transcript not found" in result["errors"][0]
        assert result["files_modified"] == []
        assert result["tool_calls"] == 0
        assert result["cost_usd"] == 0

    def test_empty_transcript(self, temp_transcript):
        """Test parsing an empty transcript."""
        # Create empty file
        Path(temp_transcript).write_text("")

        result = parse_transcript(temp_transcript)

        assert result["success"] is True
        assert result["errors"] == []
        assert result["files_modified"] == []
        assert result["tool_calls"] == 0
        assert result["summary"] == ""

    def test_malformed_json_lines(self, temp_transcript):
        """Test parsing transcript with malformed JSON lines."""
        Path(temp_transcript).write_text(
            '{"type": "assistant", "message": {"usage": {"input_tokens": 100, "output_tokens": 50}, "content": [{"type": "text", "text": "Valid line"}]}}\n'
            '{invalid json line}\n'
            '{"type": "assistant", "message": {"usage": {"input_tokens": 120, "output_tokens": 60}, "content": [{"type": "text", "text": "Another valid line"}]}}\n'
        )

        result = parse_transcript(temp_transcript)

        # Should skip malformed line and process valid ones
        assert result["success"] is True
        assert result["input_tokens"] == 220  # 100 + 120
        assert result["output_tokens"] == 110  # 50 + 60

    def test_transcript_with_empty_lines(self, temp_transcript):
        """Test parsing transcript with empty lines."""
        Path(temp_transcript).write_text(
            '{"type": "assistant", "message": {"usage": {"input_tokens": 100, "output_tokens": 50}, "content": [{"type": "text", "text": "First"}]}}\n'
            '\n'
            '   \n'
            '{"type": "assistant", "message": {"usage": {"input_tokens": 100, "output_tokens": 50}, "content": [{"type": "text", "text": "Second"}]}}\n'
        )

        result = parse_transcript(temp_transcript)

        assert result["success"] is True
        assert result["input_tokens"] == 200


class TestTokenUsageAndCost:
    """Test token usage and cost calculation."""

    def test_cost_calculation(self, temp_transcript):
        """Test that cost is calculated correctly from tokens."""
        # Create transcript with known token counts
        transcript_data = [
            {
                "type": "assistant",
                "message": {
                    "usage": {"input_tokens": 1_000_000, "output_tokens": 100_000},
                    "content": [{"type": "text", "text": "Test"}]
                }
            }
        ]

        Path(temp_transcript).write_text(
            '\n'.join(json.dumps(entry) for entry in transcript_data)
        )

        result = parse_transcript(temp_transcript)

        # Input: 1M tokens * $3/MTok = $3
        # Output: 100K tokens * $15/MTok = $1.5
        # Total: $4.5
        assert result["input_tokens"] == 1_000_000
        assert result["output_tokens"] == 100_000
        assert result["cost_usd"] == 4.5

    def test_accumulate_tokens_across_messages(self, temp_transcript):
        """Test that tokens are accumulated across multiple messages."""
        transcript_data = [
            {"type": "assistant", "message": {"usage": {"input_tokens": 100, "output_tokens": 50}, "content": []}},
            {"type": "assistant", "message": {"usage": {"input_tokens": 200, "output_tokens": 75}, "content": []}},
            {"type": "assistant", "message": {"usage": {"input_tokens": 150, "output_tokens": 25}, "content": []}},
        ]

        Path(temp_transcript).write_text(
            '\n'.join(json.dumps(entry) for entry in transcript_data)
        )

        result = parse_transcript(temp_transcript)

        assert result["input_tokens"] == 450  # 100 + 200 + 150
        assert result["output_tokens"] == 150  # 50 + 75 + 25


class TestFileTracking:
    """Test tracking of modified files."""

    def test_track_write_tool(self, temp_transcript):
        """Test tracking files created with Write tool."""
        transcript_data = [
            {
                "type": "assistant",
                "message": {
                    "usage": {"input_tokens": 100, "output_tokens": 50},
                    "content": [
                        {"type": "tool_use", "name": "Write", "input": {"file_path": "/test/file1.py"}},
                        {"type": "tool_use", "name": "Write", "input": {"file_path": "/test/file2.py"}},
                    ]
                }
            }
        ]

        Path(temp_transcript).write_text(
            '\n'.join(json.dumps(entry) for entry in transcript_data)
        )

        result = parse_transcript(temp_transcript)

        assert len(result["files_modified"]) == 2
        assert "/test/file1.py" in result["files_modified"]
        assert "/test/file2.py" in result["files_modified"]

    def test_track_edit_tool(self, temp_transcript):
        """Test tracking files modified with Edit tool."""
        transcript_data = [
            {
                "type": "assistant",
                "message": {
                    "usage": {"input_tokens": 100, "output_tokens": 50},
                    "content": [
                        {"type": "tool_use", "name": "Edit", "input": {"file_path": "/test/modified.py"}},
                    ]
                }
            }
        ]

        Path(temp_transcript).write_text(
            '\n'.join(json.dumps(entry) for entry in transcript_data)
        )

        result = parse_transcript(temp_transcript)

        assert "/test/modified.py" in result["files_modified"]

    def test_track_notebook_edit_tool(self, temp_transcript):
        """Test tracking notebooks modified with NotebookEdit tool."""
        transcript_data = [
            {
                "type": "assistant",
                "message": {
                    "usage": {"input_tokens": 100, "output_tokens": 50},
                    "content": [
                        {"type": "tool_use", "name": "NotebookEdit", "input": {"notebook_path": "/test/notebook.ipynb"}},
                    ]
                }
            }
        ]

        Path(temp_transcript).write_text(
            '\n'.join(json.dumps(entry) for entry in transcript_data)
        )

        result = parse_transcript(temp_transcript)

        assert "/test/notebook.ipynb" in result["files_modified"]

    def test_deduplicate_files(self, temp_transcript):
        """Test that duplicate file paths are deduplicated."""
        transcript_data = [
            {
                "type": "assistant",
                "message": {
                    "usage": {"input_tokens": 100, "output_tokens": 50},
                    "content": [
                        {"type": "tool_use", "name": "Write", "input": {"file_path": "/test/file.py"}},
                        {"type": "tool_use", "name": "Edit", "input": {"file_path": "/test/file.py"}},
                        {"type": "tool_use", "name": "Write", "input": {"file_path": "/test/file.py"}},
                    ]
                }
            }
        ]

        Path(temp_transcript).write_text(
            '\n'.join(json.dumps(entry) for entry in transcript_data)
        )

        result = parse_transcript(temp_transcript)

        # Should only appear once
        assert result["files_modified"].count("/test/file.py") == 1
        assert len(result["files_modified"]) == 1


class TestSummaryExtraction:
    """Test summary extraction from assistant messages."""

    def test_extract_last_substantive_text(self, temp_transcript):
        """Test extracting the last substantive text as summary."""
        transcript_data = [
            {"type": "assistant", "message": {"usage": {"input_tokens": 100, "output_tokens": 50}, "content": [{"type": "text", "text": "Starting the task..."}]}},
            {"type": "assistant", "message": {"usage": {"input_tokens": 100, "output_tokens": 50}, "content": [{"type": "text", "text": "Working on it..."}]}},
            {"type": "assistant", "message": {"usage": {"input_tokens": 100, "output_tokens": 50}, "content": [{"type": "text", "text": "Task completed successfully! All tests passing."}]}},
        ]

        Path(temp_transcript).write_text(
            '\n'.join(json.dumps(entry) for entry in transcript_data)
        )

        result = parse_transcript(temp_transcript)

        assert "Task completed successfully" in result["summary"]

    def test_truncate_long_summary(self, temp_transcript):
        """Test that very long summaries are truncated."""
        long_text = "A" * 1500
        transcript_data = [
            {"type": "assistant", "message": {"usage": {"input_tokens": 100, "output_tokens": 50}, "content": [{"type": "text", "text": long_text}]}},
        ]

        Path(temp_transcript).write_text(
            '\n'.join(json.dumps(entry) for entry in transcript_data)
        )

        result = parse_transcript(temp_transcript)

        assert len(result["summary"]) <= 1003  # 1000 + "..."
        assert result["summary"].endswith("...")

    def test_skip_short_texts_for_summary(self, temp_transcript):
        """Test that short texts are skipped in favor of substantive ones."""
        transcript_data = [
            {"type": "assistant", "message": {"usage": {"input_tokens": 100, "output_tokens": 50}, "content": [{"type": "text", "text": "This is a detailed explanation of what was accomplished in this task."}]}},
            {"type": "assistant", "message": {"usage": {"input_tokens": 100, "output_tokens": 50}, "content": [{"type": "text", "text": "Ok"}]}},  # Short text
        ]

        Path(temp_transcript).write_text(
            '\n'.join(json.dumps(entry) for entry in transcript_data)
        )

        result = parse_transcript(temp_transcript)

        # Should use the longer text, not "Ok"
        assert "detailed explanation" in result["summary"]
        assert result["summary"] != "Ok"


class TestErrorTracking:
    """Test error detection and tracking."""

    def test_detect_tool_errors(self, temp_transcript):
        """Test that tool errors are detected and captured."""
        transcript_data = [
            {"type": "assistant", "message": {"usage": {"input_tokens": 100, "output_tokens": 50}, "content": [{"type": "tool_use", "name": "Read", "input": {}}]}},
            {"type": "tool_result", "content": [{"type": "text", "text": "Error: Permission denied"}], "is_error": True},
        ]

        Path(temp_transcript).write_text(
            '\n'.join(json.dumps(entry) for entry in transcript_data)
        )

        result = parse_transcript(temp_transcript)

        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert "Permission denied" in result["errors"][0]

    def test_truncate_long_errors(self, temp_transcript):
        """Test that long error messages are truncated."""
        long_error = "Error: " + "X" * 300
        transcript_data = [
            {"type": "tool_result", "content": [{"type": "text", "text": long_error}], "is_error": True},
        ]

        Path(temp_transcript).write_text(
            '\n'.join(json.dumps(entry) for entry in transcript_data)
        )

        result = parse_transcript(temp_transcript)

        assert len(result["errors"][0]) == 200  # Truncated to 200 chars

    def test_handle_string_error_content(self, temp_transcript):
        """Test handling error content as string instead of list."""
        transcript_data = [
            {"type": "tool_result", "content": "Error string directly", "is_error": True},
        ]

        Path(temp_transcript).write_text(
            '\n'.join(json.dumps(entry) for entry in transcript_data)
        )

        result = parse_transcript(temp_transcript)

        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert "Error string directly" in result["errors"][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
