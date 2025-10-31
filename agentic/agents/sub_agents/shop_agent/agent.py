import os
import json
import requests
import logging
from google.adk.agents import Agent
from .prompt import SHOP_PROMPT
from dotenv import load_dotenv
import base64

logger = logging.getLogger(__name__)

# --- TOOL 1: call_add_product (This tool is correct and remains unchanged) ---
def call_add_product(onboarding_data: str) -> dict:
    """
    Tool for shop_agent: Downloads image, converts to Base64,
    fixes fields, and submits to the shop backend.
    """
    try:
        data_payload = json.loads(onboarding_data)
        image_url = data_payload.get("art", {}).get("photo_url")
        if not image_url:
            logger.error("[shop_agent] Photo URL missing for add_product call.")
            return {"status": "error", "message": "Artwork photo URL is missing."}

        try:
            image_response = requests.get(image_url, timeout=60)
            image_response.raise_for_status()
            image_bytes = image_response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"[shop_agent] Failed to download image: {e}")
            return {"status": "error", "message": "Failed to retrieve artwork image from URL."}

        base64_encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        mime_type = "image/jpeg" if image_url.lower().endswith((".jpg", ".jpeg")) else "image/png"
        base64_string_with_prefix = f"data:{mime_type};base64,{base64_encoded_image}"

        shop_payload = json.loads(onboarding_data)
        if 'artisan' in shop_payload and isinstance(shop_payload['artisan'], dict):
            print("--- SHOP TOOL: Checking for field name fixes... ---")
            if 'full_name' in shop_payload['artisan']:
                 shop_payload['artisan']['name'] = shop_payload['artisan'].pop('full_name')
            if 'email_address' in shop_payload['artisan']:
                shop_payload['artisan']['email'] = shop_payload['artisan'].pop('email_address')
            if 'contact' in shop_payload['artisan']:
                 shop_payload['artisan']['contact_number'] = shop_payload['artisan'].pop('contact')
            if 'aadhaar' in shop_payload['artisan']:
                 shop_payload['artisan']['aadhaar_number'] = shop_payload['artisan'].pop('aadhaar')
            print("--- SHOP TOOL: Field name checks complete. ---")
        else:
            logger.error("[shop_agent] Invalid structure: 'artisan' key missing.")
            return {"status": "error", "message": "Internal data error (artisan)."}

        if 'art' in shop_payload and isinstance(shop_payload['art'], dict):
            shop_payload['art'].pop('photo_url', None)
            shop_payload['art']['photo'] = base64_string_with_prefix
        else:
            logger.error("[shop_agent] Invalid structure: 'art' key missing.")
            return {"status": "error", "message": "Internal data error (art)."}

        url = os.getenv("SHOP_ENDPOINT", "https://kalakaari-shop-backend-978458840399.asia-southeast1.run.app/add-product")
        logger.info(f"[shop_agent] Posting final payload to {url}")
        print(f"--- SHOP TOOL: Payload for /add-product: {json.dumps(shop_payload, indent=2)} ---")

        resp = requests.post(url, json=shop_payload, timeout=60)
        resp.raise_for_status()

        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
        logger.info("[shop_agent] Product listed successfully.")
        return {"status": "success", "message": "Product listed successfully.", "response": body}

    except requests.exceptions.RequestException as e:
        logger.error(f"[shop_agent] Request to /add-product failed: {e}")
        error_status = "Network/Timeout"
        error_details = str(e)
        if hasattr(e, 'response') and e.response is not None:
             error_status = e.response.status_code
             try: error_details = e.response.json().get('detail', e.response.text)
             except: error_details = e.response.text
        logger.error(f"[shop_agent] Error details (Status {error_status}): {error_details}")
        return {"status": "error", "message": f"Unable to list product now (Server responded with error: {error_status}). Please try later.", "details": error_details}
    except Exception as e:
        logger.exception(f"[shop_agent] Unexpected error during product listing: {e}")
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}


# --- TOOL 2: trigger_shop_navigation (REMOVED) ---


# --- Environment Loading & Agent Definition ---
load_dotenv()

shop_agent = Agent(
    name="shop_agent",
    model=os.getenv("MODEL_NAME"),
    description="Asks the user if they want to list their verified artwork in the shop and handles the listing process.",
    instruction=SHOP_PROMPT,
    tools=[
        call_add_product
        # trigger_shop_navigation  <-- REMOVED FROM LIST
    ]
)