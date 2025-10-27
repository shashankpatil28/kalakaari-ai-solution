# agentic/agents/sub_agents/shop_agent/agent.py
import os
import json
import requests
import logging
from google.adk.agents import Agent
from .prompt import SHOP_PROMPT
from dotenv import load_dotenv
import base64 # Make sure this is imported

logger = logging.getLogger(__name__)

# --- TOOL 1: call_add_product ---
def call_add_product(onboarding_data: str) -> dict:
    """
    Tool for shop_agent: Downloads image from photo_url, converts to Base64,
    applies failsafe field name corrections, and submits complete data
    (with Base64 'photo' field) to the shop backend /add-product endpoint.
    """
    try:
        # 1. Parse incoming data
        data_payload = json.loads(onboarding_data)

        # 2. Extract photo URL
        image_url = data_payload.get("art", {}).get("photo_url")
        if not image_url:
            logger.error("[shop_agent] Photo URL missing for add_product call.")
            return {"status": "error", "message": "Artwork photo URL is missing."}

        # 3. Download image
        logger.info(f"[shop_agent] Downloading image from: {image_url} for Base64.")
        try:
            image_response = requests.get(image_url, timeout=30)
            image_response.raise_for_status()
            image_bytes = image_response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"[shop_agent] Failed to download image: {e}")
            return {"status": "error", "message": "Failed to retrieve artwork image from URL."}

        # 4. Convert to Base64 with prefix
        base64_encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        mime_type = "image/jpeg" if image_url.lower().endswith((".jpg", ".jpeg")) else "image/png"
        base64_string_with_prefix = f"data:{mime_type};base64,{base64_encoded_image}"

        # 5. Prepare final payload with failsafe field name corrections
        shop_payload = json.loads(onboarding_data) # Fresh copy
        if 'artisan' in shop_payload and isinstance(shop_payload['artisan'], dict):
            print("--- SHOP TOOL: Checking for field name fixes... ---")
            if 'email_address' in shop_payload['artisan']:
                print("--- SHOP TOOL FIX: Renaming 'email_address' -> 'email' ---")
                shop_payload['artisan']['email'] = shop_payload['artisan'].pop('email_address')
            if 'contact' in shop_payload['artisan']:
                 print("--- SHOP TOOL FIX: Renaming 'contact' -> 'contact_number' ---")
                 shop_payload['artisan']['contact_number'] = shop_payload['artisan'].pop('contact')
            if 'aadhaar' in shop_payload['artisan']:
                 print("--- SHOP TOOL FIX: Renaming 'aadhaar' -> 'aadhaar_number' ---")
                 shop_payload['artisan']['aadhaar_number'] = shop_payload['artisan'].pop('aadhaar')
            if 'full_name' in shop_payload['artisan']:
                 print("--- SHOP TOOL FIX: Renaming 'full_name' -> 'name' ---")
                 shop_payload['artisan']['name'] = shop_payload['artisan'].pop('full_name')
            print("--- SHOP TOOL: Field name checks complete. ---")
        else:
            logger.error("[shop_agent] Invalid structure: 'artisan' key missing.")
            return {"status": "error", "message": "Internal data error (artisan)."}

        if 'art' in shop_payload and isinstance(shop_payload['art'], dict):
            shop_payload['art'].pop('photo_url', None) # Remove URL
            shop_payload['art']['photo'] = base64_string_with_prefix # Add Base64
        else:
            logger.error("[shop_agent] Invalid structure: 'art' key missing.")
            return {"status": "error", "message": "Internal data error (art)."}

        # 6. Send to shop endpoint
        url = os.getenv("SHOP_ENDPOINT", "https://kalakaari-shop-backend-978458840399.asia-southeast1.run.app/add-product")
        logger.info(f"[shop_agent] Posting final payload to {url}")
        print(f"--- SHOP TOOL: Payload for /add-product: {json.dumps(shop_payload, indent=2)} ---") # Debug print

        resp = requests.post(url, json=shop_payload, timeout=60) # Increased timeout

        # Explicitly check for non-OK status codes before raise_for_status
        # to provide slightly better context in the error message if possible
        if not resp.ok:
             logger.error(f"[shop_agent] Request to /add-product failed with status {resp.status_code}: {resp.text}")
             # This will be caught by the RequestException handler below

        resp.raise_for_status() # Raise HTTPError for 4xx/5xx

        # 7. Process success response
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
        logger.info("[shop_agent] Product listed successfully.")
        return {"status": "success", "message": "Product listed successfully.", "response": body}

    except json.JSONDecodeError as e:
        logger.error("[shop_agent] Invalid onboarding_data JSON: %s", e)
        return {"status": "error", "message": "Invalid data format received."}
    except requests.exceptions.RequestException as e: # Catches connection errors, timeouts, and HTTPError from raise_for_status
        logger.error(f"[shop_agent] Request to /add-product failed: {e}")
        error_status = "Network/Timeout"
        error_details = str(e)
        # Try to get more specific info if it's an HTTPError
        if hasattr(e, 'response') and e.response is not None:
             error_status = e.response.status_code
             try:
                 error_detail_json = e.response.json()
                 # Use the 'detail' field if available (common in FastAPI errors)
                 error_details = error_detail_json.get('detail', e.response.text)
             except json.JSONDecodeError:
                 error_details = e.response.text # Fallback to raw text
        logger.error(f"[shop_agent] Error details (Status {error_status}): {error_details}")
        # Refined error message
        return {"status": "error", "message": f"Unable to list product now (Server responded with error: {error_status}). Please try later.", "details": error_details}
    except Exception as e:
        logger.exception(f"[shop_agent] Unexpected error during product listing: {e}")
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}


# --- TOOL 2: trigger_shop_navigation ---
def trigger_shop_navigation(should_redirect: bool) -> str:
    # This tool appears correct based on previous iterations.
    shop_url = "https://kalakaari-service-main-978458840399.asia-southeast1.run.app/"
    gratitude = "Thank you for using the CraftID platform and for your time!"

    if should_redirect:
        user_msg = f"{gratitude} Your product is listed. Redirecting you to the shop now..."
        response = {"action": "REDIRECT", "url": shop_url, "user_message": user_msg}
    else:
        user_msg = f"{gratitude} No problem at all! You can visit the shop anytime at the following link: {shop_url}\n\nHave a wonderful day!"
        response = {"action": "MESSAGE", "user_message": user_msg}
    return json.dumps(response)

# --- Environment Loading & Agent Definition ---
load_dotenv()

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