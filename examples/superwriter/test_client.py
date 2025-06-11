import requests
import json
import sys

# The URL of the running FastAPI server
API_URL = "http://127.0.0.1:8000/run-task"

# The task to be sent to the workflow
# This prompt is designed to trigger the PlannerAgent to use the echo_tool
task_payload = {
    "task": "Please use the echo_tool to confirm you have received this message. The message is: 'Hello, configuration-driven world!'"
}

def run_test():
    """
    Sends a request to the SuperWriter API and prints the response.
    """
    print(f"--- SuperWriter Test Client ---")
    print(f"Sending POST request to: {API_URL}")
    print("Payload:")
    print(json.dumps(task_payload, indent=2))

    try:
        # Set a generous timeout to allow for LLM processing
        response = requests.post(API_URL, json=task_payload, timeout=300)
        
        # Check for HTTP errors (e.g., 4xx or 5xx responses)
        response.raise_for_status()
        
        print("\n--- Server Response (Success) ---")
        response_data = response.json()
        print(json.dumps(response_data, indent=2))
        print("\n--- Test Finished Successfully ---")

    except requests.exceptions.RequestException as e:
        print(f"\n--- An error occurred ---", file=sys.stderr)
        print(f"Failed to connect or get a valid response from the server: {e}", file=sys.stderr)
        print("\nPlease ensure the server is running.", file=sys.stderr)
        print("You can start it by running 'sh run_server.sh' in the 'superwriter' directory.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_test()
