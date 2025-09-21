# ip_agent/agent.py
import os
from google.adk.agents import Agent
from .prompt import IP_PROMPT
from dotenv import load_dotenv

import os
import json
import requests
import logging

logger = logging.getLogger(__name__)


def call_add_product(onboarding_data: str) -> dict:
    """
    Tool for shop_agent:
    Submits onboarding data to the shop backend (/add-product).

    Args:
        onboarding_data (str): JSON string containing onboarding details.

    Returns:
        dict: Structured response.
    """
    try:
        payload = json.loads(onboarding_data)
    except json.JSONDecodeError as e:
        logger.error("Invalid onboarding_data JSON: %s", e)
        return {"status": "error", "message": "Invalid onboarding data format."}

    url = os.getenv("SHOP_ENDPOINT", "https://basic-backend-fastapi.vercel.app/add-product")
    logger.info(f"[shop_agent] Posting to {url}")

    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("[shop_agent] Request to /add-product failed: %s", e)
        return {"status": "error", "message": "Unable to connect to shop service now. Please try later.", "details": str(e)}

    # success
    try:
        body = resp.json()
    except Exception:
        body = resp.text

    return {"status": "success", "message": "Product listed.", "response": body}

def call_master_ip_service(onboarding_data: str) -> dict:
    """
    Tool for ip_agent:
    Submits onboarding data to the Master IP backend service for verification.

    Args:
        onboarding_data (str): JSON string containing onboarding details.

    Returns:
        dict: Structured response with status, message, and backend response if available.
    """
    try:
        # Validate and parse the incoming string
        data_payload = json.loads(onboarding_data)
        
        # Dynamic endpoint (prefer env, fallback to localhost)
        url = os.getenv("MASTER_IP_ENDPOINT", "https://basic-backend-fastapi.vercel.app/create")
        logger.info(f"[ip_agent] Sending onboarding data to {url}")

        # POST request
        response = requests.post(url, json=data_payload, timeout=30)
        response.raise_for_status()

        # Success response
        if response.status_code in (200, 201):
            logger.info("[ip_agent] Successfully submitted onboarding data.")
            return {
                "status": "success",
                "message": (
                    "Your IP data has been submitted for verification. "
                    "The system will notify you once the process is complete."
                ),
                "response": (
                    response.json()
                    if response.headers.get("content-type", "").startswith("application/json")
                    else response.text
                ),
            }

        # Unexpected status codes
        logger.warning(f"[ip_agent] Unexpected status: {response.status_code}")
        return {
            "status": "error",
            "message": f"Service responded with unexpected status code {response.status_code}.",
            "response": response.text,
        }

    except json.JSONDecodeError as e:
        logger.error(f"[ip_agent] Invalid onboarding_data format: {e}")
        return {
            "status": "error",
            "message": "Invalid data format provided. Please recheck the onboarding input.",
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"[ip_agent] Request failed: {e}")
        return {
            "status": "error",
            "message": (
                "Unable to connect to the Master IP service right now. "
                "Please try again later."
            ),
            "details": str(e),
        }

    except Exception as e:
        logger.exception(f"[ip_agent] Unexpected error: {e}")
        return {
            "status": "error",
            "message": "An unexpected error occurred during the IP submission process.",
            "details": str(e),
        }

load_dotenv()

ip_agent = Agent(
    name="ip_agent",
    model=os.getenv("MODEL_NAME"),
    description="Verifies artwork uniqueness (cosine similarity) before submitting to the Master IP service.",
    instruction=IP_PROMPT,
    tools=[call_master_ip_service, call_add_product]
)
