# Manim API Capability Report

## Test Execution Summary

- **Total Tests**: 5
- **Passed**: 2
- **Failed**: 3
- **Overall Result**: ❌ FAIL (Stability issues identified)

## Capability Breakdown

| Capability                      | Status    | Details                                                          |
| :------------------------------ | :-------- | :--------------------------------------------------------------- |
| **Server Health**               | ✅ PASSED | Root endpoint responsive, returns expected metadata.             |
| **Manim Rendering**             | ✅ PASSED | Manual code rendering via `/render` works and returns valid MP4. |
| **AI Generation**               | ❌ FAILED | Endpoint `/generate` often returns `502 Bad Gateway`.            |
| **Error Handling (API Key)**    | ❌ FAILED | Returns `502` instead of `400` on invalid keys.                  |
| **Error Handling (Validation)** | ❌ FAILED | Returns `502` instead of `422` on missing fields.                |

## Detailed Issue Analysis

### 1. 502 Bad Gateway Errors

The most critical issue is that Render returns a `502 Bad Gateway` for several scenarios.

- **Cause**: This usually indicates that the FastAPI application process crashed or failed to send a response within Render's gateway timeout (typically 60-120 seconds).
- **Observation**: During AI generation, the process involves LLM calls, TTS generation, and Manim rendering. The combination can be heavy. Even simple validation failures (like a missing field) are triggering 502s, suggesting that certain exceptions are causing the Uvicorn process to crash or hang.

### 2. LLM Hallucinations

Previous logs showed the LLM trying to import `manif` instead of `manimlib`.

- **Status**: Partially mitigated by a stricter system prompt and a code validation step.
- **Residual Risk**: LLMs remain non-deterministic. Without a retry loop in the orchestration service, a single bad generation will cause a request to fail.

### 3. Asset Resolution

- **Status**: ✅ RESOLVED. The `working_directory` context manager successfully allowed Manim to find `narration.mp3` in the temporary directory.

## Recommendations for Improvement

1. **Async Orchestration**: Move the generation/rendering process to Background Tasks. Return a `task_id` immediately to the client to avoid gateway timeouts (502/504).
2. **Exception Shielding**: Wrap the `/generate` endpoint in a broad `try-except` block that explicitly returns a `JSONResponse` even for unexpected errors, preventing the gateway from seeing a process crash.
3. **Retry Logic**: Implement a "2-try" limit for LLM generation. If the first code block fails validation (e.g., syntax error or bad imports), the server should automatically ask the LLM to fix it before giving up.
4. **Local Resource Check**: Monitor RAM usage on Render. Manim rendering can be memory-intensive and might be hitting the free tier limits, causing a SIGKILL (another source of 502s).
