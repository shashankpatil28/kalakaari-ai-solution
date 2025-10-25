import os
import json
import requests
import logging
from google.adk.agents import Agent
from .prompt import SHOP_PROMPT # We will create SHOP_PROMPT next
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# --- TOOL 1: Moved from ip_agent ---
def call_add_product(onboarding_data: str) -> dict:
    """
    Tool for shop_agent: Submits onboarding data to the shop backend.
    """
    try:
        payload = json.loads(onboarding_data)
    except json.JSONDecodeError as e:
        logger.error("[shop_agent] Invalid onboarding_data JSON: %s", e)
        return {"status": "error", "message": "Invalid data format received."}

    # Use a specific env var for the shop endpoint if different
    url = os.getenv("SHOP_ENDPOINT", "https://kalakaari-shop-backend-978458840399.asia-southeast1.run.app/add-product") # Ensure URL is correct
    logger.info(f"[shop_agent] Posting product data to {url}")

    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
        logger.info("[shop_agent] Product listed successfully.")
        return {"status": "success", "message": "Product listed successfully.", "response": body}
    except requests.exceptions.RequestException as e:
        logger.error("[shop_agent] Request to /add-product failed: %s", e)
        return {"status": "error", "message": "Unable to list product now. Please try later.", "details": str(e)}
    except Exception as e:
        logger.exception(f"[shop_agent] Unexpected error during product listing: {e}")
        return {"status": "error", "message": "An unexpected error occurred while listing the product."}


# --- TOOL 2: Moved from ip_agent ---
def trigger_shop_navigation(should_redirect: bool) -> str:
    """
    Generates a structured command for the user interface. Includes a thank you message.
    If should_redirect is True, it commands a browser redirect.
    If False, it provides a message with a link.

    Args:
        should_redirect (bool): Determines whether to issue a redirect command.

    Returns:
        str: A JSON string containing the command for the UI.
    """
    shop_url = "https://kalakaari-service-main-978458840399.asia-southeast1.run.app/"
    
    # --- ADDED GRATITUDE MESSAGE ---
    gratitude = "Thank you for using the CraftID platform and for your time!"
    # --- END ADDITION ---

    if should_redirect:
        # Combine gratitude with the redirect message
        user_msg = f"{gratitude} Your product is listed. Redirecting you to the shop now..."
        response = {
            "action": "REDIRECT",
            "url": shop_url,
            "user_message": user_msg
        }
    else:
        # Combine gratitude with the link message
        user_msg = f"{gratitude} No problem at all! You can visit the shop anytime at the following link: {shop_url}\n\nHave a wonderful day!"
        response = {
            "action": "MESSAGE",
            "user_message": user_msg
        }
        
    return json.dumps(response)


load_dotenv()

# --- Define the Shop Agent ---
shop_agent = Agent(
    name="shop_agent",
    model=os.getenv("MODEL_NAME"),
    description="Asks the user if they want to list their verified artwork in the shop and handles the listing process.",
    instruction=SHOP_PROMPT,
    tools=[
        call_add_product,
        trigger_shop_navigation
    ]
)