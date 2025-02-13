import requests
import json

def test_vision():
    """Test the vision processing endpoint."""
    
    # The vision to process
    vision = """
    Build an AI-powered code review system that:
    - Automatically checks code quality and style
    - Identifies security vulnerabilities
    - Suggests performance improvements
    - Ensures compliance with best practices
    - Provides clear, actionable feedback
    """
    
    # Send request to the API
    response = requests.post(
        "http://localhost:5004/vision",
        json={"vision": vision}
    )
    
    # Print the response
    print("\nResponse Status:", response.status_code)
    print("\nTeam's Analysis:")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_vision() 