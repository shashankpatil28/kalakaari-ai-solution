# agentic/agents/sub_agents/ip_agent/tools.py

import requests
import json
from google.adk.tools import FunctionTool

def call_master_ip_service(onboarding_data: str) -> dict:
    """
    Makes an API call to the master IP backend service to submit the artisan's data.

    Args:
        onboarding_data: The complete JSON data packet as a string.

    Returns:
        A dictionary with a 'status' key ('success' or 'error') and a 'message'
        key containing either a success confirmation or an error description.
    """
    try:
        # The onboarding_data is a string, so we need to parse it to a Python dictionary
        data_payload = json.loads(onboarding_data)

        # Define the API endpoint
        url = "http://localhost:8001/create"

        # Make the POST request to the backend service
        response = requests.post(url, json=data_payload, timeout=30)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # Check for a successful response (e.g., 200 OK, 201 Created)
        if response.status_code in [200, 201]:
            # Assuming the master service returns a success message
            return {
                "status": "success",
                "message": "Your IP data has been successfully submitted for verification. We will notify you once the process is complete.",
                "response": response,
            }
        else:
            return {
                "status": "error",
                "message": f"An unexpected error occurred with the service. Status code: {response.status_code}"
            }

    except requests.exceptions.RequestException as e:
        # Handle network-related errors (e.g., connection refused, timeout)
        return {
            "status": "error",
            "message": f"We are currently unable to connect to the IP service. Please try again later. Error: {e}"
        }
    except json.JSONDecodeError:
        # Handle cases where the input data is not valid JSON
        return {
            "status": "error",
            "message": "The data format received was invalid. Please restart the process."
        }
    except Exception as e:
        # Handle any other unexpected errors
        return {
            "status": "error",
            "message": f"An unexpected error occurred during the submission process. Error: {e}"
        }

# Create the FunctionTool instance
ip_service_tool = FunctionTool(func=call_master_ip_service)