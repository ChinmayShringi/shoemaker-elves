# Azure OpenAI Adapter

## Pre-work

**Date**: 2026-02-04
**Task**: Azure OpenAI adapter (planner mode)

### Plan
1. Create `src/gpt_agent_orchestrator/planners/azure_openai_adapter.py` with AzureOpenAIAdapter class
2. Use OpenAI SDK configured for Azure endpoints
3. Support Azure-specific configuration: endpoint, deployment name, api_version, api_key
4. Register `azure_openai` provider in the registry
5. Update config system to handle Azure settings
6. Update CLI to accept Azure-specific flags (--azure-endpoint, --azure-deployment, --azure-api-version)
7. Write comprehensive tests with mocked API calls

### Files to be affected
- `src/gpt_agent_orchestrator/planners/azure_openai_adapter.py` (new)
- `src/gpt_agent_orchestrator/planners/registry.py` (update)
- `src/gpt_agent_orchestrator/config.py` (already supports Azure config)
- `src/gpt_agent_orchestrator/cli.py` (update)
- `tests/test_azure_openai_adapter.py` (new)

### Dependencies
- OpenAI Python SDK (supports Azure OpenAI)
- Existing planner adapter interface (PlannerAdapter protocol)
- Existing template system for prompts
- Config system already has Azure environment variables defined

### Assumptions
- Azure OpenAI uses the same API structure as OpenAI but with different authentication and endpoint format
- The OpenAI SDK handles Azure configuration through base_url and additional headers
- Azure deployment name replaces the model parameter in API calls
- API version must be specified for Azure OpenAI
- Following the same pattern as OpenAIAdapter but with Azure-specific initialization

## Post-work

**Completed**: 2026-02-04
**Status**: Completed

### Changes Made
- Successfully implemented Azure OpenAI adapter with full support for Azure-specific configuration
- Integrated adapter into the existing planner system with proper factory registration
- Added CLI flags for all Azure OpenAI parameters (endpoint, deployment, api_version)
- Updated GPTPlanner to use the adapter system for Azure OpenAI provider
- Created comprehensive test suite with 18 tests covering all functionality

### Files Modified
- `src/gpt_agent_orchestrator/planners/azure_openai_adapter.py` — New adapter class implementing PlannerAdapter protocol with Azure OpenAI client
- `src/gpt_agent_orchestrator/planners/registry.py` — Added azure_openai provider registration with validation of required parameters
- `src/gpt_agent_orchestrator/cli.py` — Added --azure-endpoint, --azure-deployment, and --azure-api-version CLI flags with config override handling
- `src/gpt_agent_orchestrator/gpt_planner.py` — Extended adapter system integration to include azure_openai provider
- `tests/test_azure_openai_adapter.py` — Comprehensive test suite covering initialization, planning, review, error handling, and Azure-specific features
- `tests/test_planner_registry.py` — Added tests for azure_openai provider registration and parameter validation

### Key Decisions
1. **Used AzureOpenAI client from openai package**: The official OpenAI Python SDK provides native Azure OpenAI support through the AzureOpenAI class, which handles authentication and endpoint configuration properly
2. **Deployment name as model parameter**: In Azure OpenAI, the deployment name is passed as the model parameter in API calls, following Azure's convention
3. **Default API version**: Set default API version to "2024-02-01" to ensure consistent behavior across deployments
4. **Parameter validation in factory**: Added validation in the registry factory to provide clear error messages when required Azure parameters are missing
5. **Config already supported Azure**: The config system already had Azure settings defined (endpoint, deployment, api_version, api_key) from a previous task, so no config changes were needed

### Implementation Details
- **Adapter class**: AzureOpenAIAdapter implements the same PlannerAdapter protocol as OpenAI and Anthropic adapters, ensuring consistent interface
- **Retry logic**: Implemented exponential backoff for API errors and fixed delays for rate limits (30s, 60s, 90s)
- **Error messages**: Customized error messages to include "Azure OpenAI" context for better debugging
- **Response parsing**: Follows the same JSON parsing and validation logic as other adapters
- **Test coverage**: 18 tests covering success cases, error cases, Azure-specific behavior, and edge cases

### Test Results
All 85 tests pass, including:
- 18 new tests for Azure OpenAI adapter
- 3 new tests for registry integration with Azure OpenAI
- All existing tests continue to pass

### Usage Examples
```bash
# Using CLI flags
gpt-orch ~/project --gpt -d "Build API" \\
  --planner-provider azure_openai \\
  --azure-endpoint https://my-resource.openai.azure.com/ \\
  --azure-deployment gpt-4o \\
  --azure-api-version 2024-02-01

# Using environment variables
export GPT_ORCH_AZURE_OPENAI_API_KEY="your-key"
export GPT_ORCH_AZURE_ENDPOINT="https://my-resource.openai.azure.com/"
export GPT_ORCH_AZURE_DEPLOYMENT="gpt-4o"
export GPT_ORCH_AZURE_API_VERSION="2024-02-01"
gpt-orch ~/project --gpt -d "Build API" --planner-provider azure_openai

# Using config file
gpt-orch config set planner.provider azure_openai
gpt-orch config set azure.endpoint https://my-resource.openai.azure.com/
gpt-orch config set azure.deployment gpt-4o
gpt-orch config set azure.api_version 2024-02-01
```

### Status
✅ Task fully completed
- Azure OpenAI adapter fully functional
- All required parameters supported (endpoint, deployment, api_version, api_key)
- CLI flags and environment variables work correctly
- Comprehensive test coverage
- All tests passing (85/85)
