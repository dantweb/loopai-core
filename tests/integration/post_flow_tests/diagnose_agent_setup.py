#!/usr/bin/env python3
"""
Diagnostic script for Agent RECEIVE_POST setup.

This script checks the current configuration of agents to identify
why the agent_post tests are failing.

It examines:
1. Agent database entries
2. RECEIVE_POST.yaml configurations
3. WAKEUP.py lambda implementations
4. Filesystem directory structure
5. Integration points between components
"""

import sys
import os
import json
import glob
from pathlib import Path

def check_agent_database():
    """Check agent database configuration"""
    print("🔍 Checking Agent Database Configuration...")

    try:
        # This would need to be run in the proper Flask context
        # For now, we'll check the filesystem structure
        print("   (Database check requires Flask context - checking filesystem instead)")

        # Look for agent loop directories
        user_loops = "/app/var/users/*/loops/*/config"  # In container
        local_loops = glob.glob("loopai_src/var/users/*/loops/*/config")

        if local_loops:
            print(f"   ✅ Found {len(local_loops)} agent loop directories")
            return local_loops[:5]  # Return first 5 for examination
        else:
            print("   ❌ No agent loop directories found")
            return []

    except Exception as e:
        print(f"   ❌ Error checking database: {e}")
        return []

def check_receive_post_yaml(config_dirs):
    """Check RECEIVE_POST.yaml configurations"""
    print("\n🔍 Checking RECEIVE_POST.yaml Configurations...")

    configurations = []

    for config_dir in config_dirs:
        receive_post_yaml = os.path.join(config_dir, "RECEIVE_POST.yaml")

        if os.path.exists(receive_post_yaml):
            print(f"   ✅ Found: {receive_post_yaml}")

            try:
                with open(receive_post_yaml, 'r') as f:
                    content = f.read()

                configurations.append({
                    'path': receive_post_yaml,
                    'content': content
                })

                # Quick analysis
                if 'filesystem' in content:
                    print("      ✅ Has filesystem output")
                else:
                    print("      ⚠️  No filesystem output found")

                if 'lambda' in content:
                    print("      ✅ Uses lambda executor")
                else:
                    print("      ⚠️  Not using lambda executor")

                if '/agentlife/post/inbox' in content:
                    print("      ✅ Targets agent inbox directory")
                else:
                    print("      ⚠️  Not targeting agent inbox directory")

            except Exception as e:
                print(f"      ❌ Error reading file: {e}")

        else:
            print(f"   ❌ Missing: {receive_post_yaml}")

    return configurations

def check_wakeup_py(config_dirs):
    """Check WAKEUP.py lambda implementations"""
    print("\n🔍 Checking WAKEUP.py Lambda Implementations...")

    implementations = []

    for config_dir in config_dirs:
        wakeup_py = os.path.join(config_dir, "WAKEUP.py")

        if os.path.exists(wakeup_py):
            print(f"   ✅ Found: {wakeup_py}")

            try:
                with open(wakeup_py, 'r') as f:
                    content = f.read()

                implementations.append({
                    'path': wakeup_py,
                    'content': content
                })

                # Analyze content
                content_size = len(content.strip())
                if content_size < 100:
                    print(f"      ⚠️  Very short content ({content_size} chars) - likely empty template")
                    print(f"      📝 Content preview: {repr(content[:50])}")
                else:
                    print(f"      ✅ Has substantial content ({content_size} chars)")

                # Check for key functions
                if 'def ' in content:
                    print("      ✅ Contains function definitions")
                else:
                    print("      ⚠️  No function definitions found")

                if 'request_data' in content:
                    print("      ✅ References request_data")
                else:
                    print("      ⚠️  No request_data handling found")

                if 'session_manager' in content:
                    print("      ✅ Uses session_manager")
                else:
                    print("      ⚠️  No session_manager usage found")

            except Exception as e:
                print(f"      ❌ Error reading file: {e}")

        else:
            print(f"   ❌ Missing: {wakeup_py}")

    return implementations

def check_filesystem_structure():
    """Check filesystem directory structure for agent inboxes"""
    print("\n🔍 Checking Agent Filesystem Structure...")

    # Look for agent filesystem directories
    patterns = [
        "loopai_src/var/users/*/loops/*/filesystem/*",
        "loopai_src/var/users/*/loops/*/agentlife/*",
        "/app/var/users/*/loops/*/filesystem/*",
        "/app/var/users/*/loops/*/agentlife/*"
    ]

    found_dirs = []
    for pattern in patterns:
        dirs = glob.glob(pattern)
        found_dirs.extend(dirs)

    if found_dirs:
        print(f"   ✅ Found {len(found_dirs)} filesystem directories")
        for d in found_dirs[:10]:  # Show first 10
            print(f"      📁 {d}")
    else:
        print("   ⚠️  No agent filesystem directories found")

    # Check for specific inbox structures
    inbox_patterns = [
        "**/agentlife/post/inbox/new",
        "**/filesystem/agentlife/post/inbox/new"
    ]

    inbox_dirs = []
    for pattern in inbox_patterns:
        dirs = glob.glob(pattern, recursive=True)
        inbox_dirs.extend(dirs)

    if inbox_dirs:
        print(f"   ✅ Found {len(inbox_dirs)} agent inbox directories")
        for d in inbox_dirs[:5]:
            print(f"      📥 {d}")
    else:
        print("   ❌ No agent inbox directories found")

    return found_dirs, inbox_dirs

def analyze_integration_points():
    """Analyze integration points between components"""
    print("\n🔍 Analyzing Integration Points...")

    print("   📋 Expected Flow:")
    print("      1. agent_post sends POST to /api/public/agent/X/action/RECEIVE_POST/")
    print("      2. HTTP adapter captures request data")
    print("      3. Lambda executor (WAKEUP.py) processes the data")
    print("      4. Filesystem adapter creates files in agent inbox")
    print("      5. agent_post finds the created file")

    print("\n   🔧 Common Issues:")
    print("      ❌ Empty WAKEUP.py (no processing logic)")
    print("      ❌ Wrong filesystem output path in RECEIVE_POST.yaml")
    print("      ❌ Lambda executor not extracting request data properly")
    print("      ❌ Filesystem adapter not creating files in expected location")
    print("      ❌ agent_post looking in wrong directory for created files")

def generate_fix_recommendations(yaml_configs, py_implementations):
    """Generate specific fix recommendations"""
    print("\n💡 Fix Recommendations:")

    # Check YAML configurations
    has_proper_yaml = False
    for config in yaml_configs:
        content = config['content']
        if ('filesystem' in content and
            'lambda' in content and
            '/agentlife/post/inbox' in content):
            has_proper_yaml = True
            break

    if not has_proper_yaml:
        print("   🔧 Fix RECEIVE_POST.yaml:")
        print("      - Ensure 'filesystem' output with code_dir: '/agentlife/post/inbox/new'")
        print("      - Use 'lambda' executor")
        print("      - Include proper input/output configuration")

    # Check Python implementations
    has_proper_python = False
    for impl in py_implementations:
        content = impl['content']
        if (len(content.strip()) > 100 and
            'def ' in content and
            'request_data' in content):
            has_proper_python = True
            break

    if not has_proper_python:
        print("   🔧 Fix WAKEUP.py:")
        print("      - Implement proper message processing logic")
        print("      - Extract data from request_data structure")
        print("      - Use session_manager for broadcast")
        print("      - See sample_receive_post_lambda.py for reference")

    print("\n   📋 Quick Fix Steps:")
    print("      1. Copy sample_receive_post_lambda.py to affected WAKEUP.py files")
    print("      2. Verify RECEIVE_POST.yaml has correct filesystem output path")
    print("      3. Test with a simple agent_post simulation")
    print("      4. Run the integration test to validate the flow")

def main():
    """Main diagnostic execution"""
    print("🔬 Agent RECEIVE_POST Diagnostic Tool")
    print("=" * 60)

    # Check database/filesystem
    config_dirs = check_agent_database()

    if not config_dirs:
        print("\n❌ No agent configurations found.")
        print("   Make sure you're running from the correct directory.")
        print("   Expected structure: loopai_src/var/users/*/loops/*/config/")
        return 1

    # Check configurations
    yaml_configs = check_receive_post_yaml(config_dirs)
    py_implementations = check_wakeup_py(config_dirs)

    # Check filesystem
    fs_dirs, inbox_dirs = check_filesystem_structure()

    # Analyze integration
    analyze_integration_points()

    # Generate recommendations
    generate_fix_recommendations(yaml_configs, py_implementations)

    print("\n🎯 Summary:")
    print(f"   - Checked {len(config_dirs)} agent configurations")
    print(f"   - Found {len(yaml_configs)} RECEIVE_POST.yaml files")
    print(f"   - Found {len(py_implementations)} WAKEUP.py files")
    print(f"   - Found {len(inbox_dirs)} agent inbox directories")

    # Determine if fixes are needed
    needs_fixes = (len(yaml_configs) == 0 or
                   len(py_implementations) == 0 or
                   len(inbox_dirs) == 0)

    if needs_fixes:
        print("\n⚠️  Issues detected - fixes needed for agent_post tests to pass")
        return 1
    else:
        print("\n✅ Configuration looks reasonable - run integration tests for validation")
        return 0

if __name__ == "__main__":
    exit(main())