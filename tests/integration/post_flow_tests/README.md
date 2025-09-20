# Agent RECEIVE_POST Flow Integration Tests

This directory contains comprehensive integration tests and diagnostic tools for validating the Agent RECEIVE_POST flow that `agent_post` tests expect to work.

## Problem Statement

The `agent_post` service tests are failing because the expected flow isn't working correctly:

1. **agent_post** sends POST request to `/api/public/agent/X/action/RECEIVE_POST/`
2. **LoopAI** should execute the agent's `RECEIVE_POST.yaml` loop
3. **Lambda executor** should process the message data from `WAKEUP.py`
4. **Filesystem adapter** should create a file in the agent's inbox
5. **agent_post** should find the created file and validate its content

The tests are timing out because the file is never created, indicating a break in this flow.

## Files in This Directory

### 1. `test_agent_receive_post_flow.py`
Comprehensive integration test that validates the entire HTTP → Lambda → Filesystem flow.

**Tests included:**
- ✅ HTTP Adapter captures POST request data correctly
- ✅ Lambda Executor processes message data
- ✅ Filesystem Adapter creates files in agent inbox
- ✅ End-to-end flow simulation
- ✅ Agent_post compatibility validation

### 2. `sample_receive_post_lambda.py`
Reference implementation for `WAKEUP.py` that properly handles `RECEIVE_POST` actions.

**Features:**
- Extracts message data from nested request structure
- Validates message format and content
- Creates proper file output for filesystem adapter
- Handles errors gracefully
- Matches exactly what agent_post expects

### 3. `run_agent_flow_tests.py`
Test runner that executes all flow validation tests and provides troubleshooting guidance.

### 4. `diagnose_agent_setup.py`
Diagnostic tool that analyzes current agent configuration to identify specific issues.

**Checks:**
- Agent database/filesystem structure
- `RECEIVE_POST.yaml` configurations
- `WAKEUP.py` lambda implementations
- Filesystem directory structure
- Integration points between components

## Usage

### Running Integration Tests

```bash
# From loopai_src/core/tests/integration/
python test_agent_receive_post_flow.py

# Or use the test runner
python run_agent_flow_tests.py
```

### Diagnosing Current Setup

```bash
# Analyze current agent configuration
python diagnose_agent_setup.py
```

### Fixing Agent Configuration

1. **Copy the sample lambda implementation:**
   ```bash
   cp sample_receive_post_lambda.py /path/to/agent/WAKEUP.py
   ```

2. **Verify RECEIVE_POST.yaml has correct structure:**
   ```yaml
   session:
     name: Agent RECEIVE_POST Handler
     code_source: 'WAKEUP.py'
     loop:
       create_tasks:
         description: "Process incoming agent messages"
         type: bash
         input:
           - request:
               method: POST
         output:
           - filesystem:
               code_dir: /agentlife/post/inbox/new
           - text:
               name: output.txt
         action:
           executor: lambda
   ```

3. **Ensure agent filesystem directory exists:**
   ```bash
   mkdir -p /path/to/agent/filesystem/agentlife/post/inbox/new
   ```

## Expected Flow Validation

The tests validate this exact sequence:

1. **HTTP Request Processing**
   ```json
   {
     "method": "POST",
     "body": {
       "result": {
         "result": {
           "updated_files": [
             {
               "path": "dir_save_123456.json",
               "file_operation": "update",
               "file_content": "{\"message\": {...}}"
             }
           ]
         }
       }
     }
   }
   ```

2. **Lambda Processing**
   - Extracts `updated_files` from nested structure
   - Validates message format
   - Prepares data for filesystem adapter

3. **Filesystem Creation**
   - Creates file in `/agentlife/post/inbox/new/`
   - File contains the message JSON
   - agent_post can find and validate the file

## Troubleshooting Common Issues

### Issue: Empty WAKEUP.py Files
**Symptoms:** Tests pass but no files created
**Solution:** Implement proper lambda logic (see sample_receive_post_lambda.py)

### Issue: Wrong Filesystem Path
**Symptoms:** Files created but agent_post can't find them
**Solution:** Verify `code_dir: /agentlife/post/inbox/new` in RECEIVE_POST.yaml

### Issue: Request Data Not Available
**Symptoms:** Lambda fails to process request
**Solution:** Ensure HTTP adapter is capturing request data properly

### Issue: JSON Structure Mismatch
**Symptoms:** Lambda processes but wrong file content
**Solution:** Validate the nested result structure matches agent_post format

## Integration with Concurrent Execution Fixes

These tests work with the concurrent execution improvements to ensure:
- ✅ Multiple agents can process RECEIVE_POST actions simultaneously
- ✅ Session isolation prevents cross-contamination of message data
- ✅ Real-time logging tracks message processing correctly
- ✅ Filesystem operations are thread-safe and isolated per agent

## Running in Container

To run these tests in the loopai_web container:

```bash
docker compose exec loopai_web bash
cd /app/core/tests/integration
python run_agent_flow_tests.py
```

## Expected Output

When working correctly, you should see:
```
🎉 SUCCESS: All agent flow tests passed!

✅ Key validations completed:
   - HTTP adapter captures POST requests correctly
   - Lambda executor processes message data
   - Filesystem adapter creates files in agent inbox
   - End-to-end flow matches agent_post expectations
   - File creation and search works like agent_post tests
```

This confirms that the agent RECEIVE_POST flow is working correctly and agent_post tests should pass.