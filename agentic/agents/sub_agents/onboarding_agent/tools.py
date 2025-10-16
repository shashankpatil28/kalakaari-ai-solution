# agents/sub_agents/onboarding_agent/tools.py
import json

def package_onboarding_data(onboarding_data: str) -> str:
    """
    This tool is called when the onboarding agent has successfully collected all artisan and art data.
    It packages the data into a final JSON object with a status, indicating that the next step is to
    invoke the ip_agent. This entire JSON object is then returned as a string to the orchestrator.

    Args:
        onboarding_data (str): A JSON string containing the structured data for the artisan and their art.

    Returns:
        str: A JSON string containing a status wrapper and the original data,
             signaling the orchestration_agent to proceed to the next step.
    """
    print("--- Tool Activated: Packaging onboarding_data ---")
    try:
        # Parse the incoming JSON string to validate it
        data = json.loads(onboarding_data)
        
        # Create the final payload for the orchestrator
        final_payload = {
            "status": "ONBOARDING_COMPLETE",
            "message": "Artisan details collected. Ready for IP creation process.",
            "data": data  # This is the original artisan/art JSON
        }
        
        # Return the entire payload as a JSON string
        return json.dumps(final_payload, indent=2)

    except json.JSONDecodeError as e:
        # Handle cases where the LLM provides invalid JSON
        error_payload = {
            "status": "ERROR",
            "message": "Failed to package data due to invalid JSON format.",
            "details": str(e)
        }
        return json.dumps(error_payload, indent=2)