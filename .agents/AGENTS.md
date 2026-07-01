# Project Rules

## Development and Testing Standards
- **NO FAKE IMPLEMENTATIONS**: Do not use "Facade Implementations" or hardcode values to bypass or trick unit tests (e.g. using static if/else blocks to return "Gin and Tonic" for all inputs, or hardcoding exact API responses instead of properly simulating logic). 
- **TRUE MOCKING**: You MUST use standard testing libraries (like `unittest.mock.patch`, `AsyncMock`) to simulate external services (LLMs, APIs) during testing. Test the logic, do not trick the assertions.
- If you are caught hardcoding logic in production code just to pass a test, your response will be considered FAILED. You must always build agentic, dynamic code.
