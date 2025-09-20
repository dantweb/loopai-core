# Integration Tests

This directory contains integration tests for the LoopAI system.

## Test Suites

### `post_flow_tests/`
Integration tests and diagnostic tools for Agent RECEIVE_POST flow validation.

These tests help diagnose and fix issues with agent messaging system where:
- agent_post sends messages to LoopAI agents
- LoopAI processes the messages through HTTP → Lambda → Filesystem adapters
- Files should be created in agent inboxes for agent_post to find

**Key files:**
- `test_agent_receive_post_flow.py` - Main integration tests
- `sample_receive_post_lambda.py` - Reference WAKEUP.py implementation
- `run_agent_flow_tests.py` - Test runner script
- `diagnose_agent_setup.py` - Diagnostic tool
- `README.md` - Detailed documentation

**Usage:**
```bash
cd post_flow_tests/
python run_agent_flow_tests.py
```

### `validate_concurrent_fixes.py`
Validation tests for concurrent loop execution fixes.

These tests validate that the concurrent execution system works correctly:
- Session isolation between concurrent users
- Real-time logging to correct user channels
- Multiple users running loops simultaneously without interference

**Usage:**
```bash
python validate_concurrent_fixes.py
```

## Running All Integration Tests

```bash
# Run concurrent execution validation
python validate_concurrent_fixes.py

# Run agent flow tests
cd post_flow_tests/
python run_agent_flow_tests.py
```