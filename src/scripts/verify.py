import asyncio
import os
import sys

# Add root folder to sys.path so we can import api/memory/agents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.app import runtime_config, manager

async def main():
    print("=== Starting Aythron Genesis Integration Verification ===")
    
    # 1. Ensure we are in Mock sandbox mode for test run
    runtime_config.provider_type = "mock"
    manager.provider = runtime_config.get_provider()
    
    goal = "Create the fibonacci.py script containing the fibonacci function and its test cases"
    print(f"Goal: '{goal}'")
    print("Executing manager loop...")
    
    # 2. Run the loop
    success = await manager.execute_goal(goal)
    
    print("\n=== Execution Logs ===")
    for log_line in manager.logs:
        print(log_line)
        
    print("\n=== Verification Verification ===")
    if not success:
        print("FAIL: Execution loop returned failure status.")
        sys.exit(1)
        
    # Check that generated files exist
    fib_path = "fibonacci.py"
    test_fib_path = "test_fibonacci.py"
    
    if os.path.exists(fib_path) and os.path.exists(test_fib_path):
        print(f"SUCCESS: {fib_path} and {test_fib_path} were successfully written to the workspace!")
        
        # Print contents of fibonacci.py
        with open(fib_path, "r") as f:
            print(f"\n--- {fib_path} Contents ---")
            print(f.read().strip())
            
        # Clean up files so the workspace stays clean
        os.remove(fib_path)
        os.remove(test_fib_path)
        print("Cleaned up test files.")
        print("\nALL SYSTEM VERIFICATIONS PASSED SUCCESSFULLY!")
    else:
        print(f"FAIL: Generated files were not found in workspace.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
