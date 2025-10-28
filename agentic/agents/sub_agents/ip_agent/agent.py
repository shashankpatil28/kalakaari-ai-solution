# ip_agent/agent.py
import os
from google.adk.agents import Agent
from .prompt import IP_PROMPT
from dotenv import load_dotenv
# Near the other imports
from ..shop_agent.agent import shop_agent
import base64 

import os
import json
import requests
import logging

logger = logging.getLogger(__name__)

# Add this new tool function
# Define your similarity threshold (adjust as needed)


# Add this new tool function
# Define your similarity threshold (adjust as needed)

# Add this new tool function
def call_metadata_similarity_search(onboarding_data: str) -> dict:
    """
    Tool for ip_agent:
    Searches for semantically similar items using textual metadata.
    Extracts artisan/art info, calls the /metadata/search endpoint,
    and returns the score of the top match.

    Args:
        onboarding_data (str): JSON string containing onboarding details.

    Returns:
        dict: {"status": "found", "score": float} if matches are found.
              {"status": "not_found", "score": 0.0} if no matches.
              {"status": "error", "message": "..."} if an error occurs.
    """
    try:
        data_payload = json.loads(onboarding_data)

        # Prepare the payload for the /metadata/search endpoint
        search_payload = {
            "artisan": data_payload.get("artisan", {}),
            "art": data_payload.get("art", {}),
            "top_k": 1 # Only need the top match for uniqueness check
        }
        # Remove photo_url if present, as the API ignores it but good practice
        search_payload["art"].pop("photo_url", None)

        # --- Use a NEW environment variable for the metadata search endpoint ---
        meta_search_url = os.getenv("METADATA_SEARCH_URL", "https://master-ip-service-978458840399.asia-southeast1.run.app/metadata/search") # Replace with your actual URL
        logger.info(f"[ip_agent] Sending data to metadata search endpoint: {meta_search_url}")

        # Make the POST request with JSON payload
        response = requests.post(meta_search_url, json=search_payload, timeout=30)
        response.raise_for_status()

        search_results = response.json()
        logger.info(f"[ip_agent] Metadata search result: {search_results}")

        # Check the results
        results_list = search_results.get("results", [])
        if not results_list:
            # No similar metadata found
            return {"status": "not_found", "score": 0.0}
        else:
            # Return the score of the top match
            top_match_score = results_list[0].get("score", 0.0)
            # Use 'final_score' if available and preferred, otherwise 'score'
            # top_match_score = results_list[0].get("final_score", results_list[0].get("score", 0.0))
            return {"status": "found", "score": float(top_match_score)}

    except json.JSONDecodeError as e:
        logger.error(f"[ip_agent] Invalid onboarding_data format for metadata search: {e}")
        return {"status": "error", "message": "Invalid data format provided."}
    except requests.exceptions.RequestException as e:
        logger.error(f"[ip_agent] Metadata search request failed: {e}")
        error_details = e.response.text if e.response else str(e)
        logger.error(f"[ip_agent] Error details: {error_details}")
        return {"status": "error", "message": f"Unable to connect to metadata search service: {error_details}"}
    except Exception as e:
        logger.exception(f"[ip_agent] Unexpected error during metadata search: {e}")
        return {"status": "error", "message": "An unexpected error occurred during metadata search."}

def call_image_similarity_search(image_url: str) -> dict:
    """
    Tool for ip_agent:
    Searches for visually similar images using the artwork's URL via a POST
    request with multipart/form-data encoding. Checks if the top match score
    exceeds a predefined threshold.

    Args:
        image_url (str): The direct photo URL of the artwork.

    Returns:
        dict: {"status": "unique", "score": float}
              {"status": "duplicate", "score": float, "message": "..."}
              {"status": "error", "message": "..."}
    """
    SIMILARITY_THRESHOLD = 0.85
    try:
        print(f"--- TOOL: call_image_similarity_search received image_url: '{image_url}' ---")

        if not image_url:
            logger.error("[ip_agent] Empty image_url received.")
            print("--- TOOL ERROR: image_url is missing or empty! ---")
            return {"status": "error", "message": "Artwork photo URL is missing or empty."}

        search_url = os.getenv("IMAGE_SEARCH_URL", "https://master-ip-service-978458840399.asia-southeast1.run.app/image-search/url")
        logger.info(f"[ip_agent] Sending URL ({image_url}) to image search endpoint: {search_url}")

        files_payload = {
            'image_url': (None, image_url),
            'top_k': (None, '1'),
            'include_meta': (None, 'false')
        }
        print(f"--- TOOL: Sending files_payload to API: {files_payload} ---")

        response = requests.post(search_url, files=files_payload, timeout=60)
        response.raise_for_status()

        search_results = response.json()
        logger.info(f"[ip_agent] Image search result: {search_results}")
        print(f"--- TOOL: Received API response: {search_results} ---")

        results_list = search_results.get("results", [])

        # --- START OF MODIFICATION ---
        if not results_list:
            print("--- TOOL: No similar results found, returning status: unique, score: 0.0 ---")
            # Explicitly return score 0.0 when no results
            return {"status": "unique", "score": 0.0}
        else:
            top_match_score = results_list[0].get("score", 0.0) # Ensure score is float
            print(f"--- TOOL: Top match score: {top_match_score} (Threshold: {SIMILARITY_THRESHOLD}) ---")
            if top_match_score >= SIMILARITY_THRESHOLD:
                duplicate_id = results_list[0].get("id", "Unknown")
                message = (
                    f"Our system detected a high visual similarity (score: {top_match_score:.2f}) "
                    f"with an existing artwork (ID: {duplicate_id})... " # Truncated
                )
                print(f"--- TOOL: High similarity detected, returning status: duplicate, score: {top_match_score} ---")
                # Explicitly return score even when duplicate
                return {"status": "duplicate", "score": float(top_match_score), "message": message}
            else:
                print(f"--- TOOL: Similarity below threshold, returning status: unique, score: {top_match_score} ---")
                # Explicitly return score even when unique but below threshold
                return {"status": "unique", "score": float(top_match_score)}
        # --- END OF MODIFICATION ---

    except requests.exceptions.RequestException as e:
        logger.error(f"[ip_agent] Image search request failed: {e}")
        error_details = e.response.text if e.response else str(e)
        logger.error(f"[ip_agent] Error details: {error_details}")
        print(f"--- TOOL ERROR: RequestException: {error_details} ---")
        return {"status": "error", "message": f"Unable to connect to image search service: {error_details}"}
    except Exception as e:
        logger.exception(f"[ip_agent] Unexpected error during image search: {e}")
        print(f"--- TOOL ERROR: Unexpected Exception: {e} ---")
        return {"status": "error", "message": "An unexpected error occurred during image search."}
    
def call_master_ip_service(onboarding_data: str) -> dict:
    """
    Tool for ip_agent:
    Downloads the image from photo_url, converts it to Base64, and submits
    the complete data (with Base64 'photo' field) to the Master IP backend
    /create endpoint, matching the backend's expectation.

    Args:
        onboarding_data (str): JSON string containing onboarding details
                               (including art.photo_url).

    Returns:
        dict: Structured response with status, message, and backend response.
    """
    try:
        data_payload = json.loads(onboarding_data)
        image_url = data_payload.get("art", {}).get("photo_url")
        if not image_url:
            logger.error("[ip_agent] Photo URL missing for /create.")
            return {"status": "error", "message": "Artwork photo URL is missing."}

        try:
            image_response = requests.get(image_url, timeout=30)
            image_response.raise_for_status()
            image_bytes = image_response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"[ip_agent] Failed image download: {e}")
            return {"status": "error", "message": "Failed to retrieve image from URL."}

        base64_encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        mime_type = "image/jpeg" if image_url.lower().endswith((".jpg", ".jpeg")) else "image/png"
        base64_string_with_prefix = f"data:{mime_type};base64,{base64_encoded_image}"

        # Prepare payload AND APPLY FAILSAFE FIXES
        create_payload = json.loads(onboarding_data)
        if 'artisan' in create_payload and isinstance(create_payload['artisan'], dict):
            print("--- TOOL: Checking for field name fixes... ---") # Added debug print
            if 'email_address' in create_payload['artisan']:
                print("--- TOOL FIX: Renaming 'email_address' -> 'email' ---")
                create_payload['artisan']['email'] = create_payload['artisan'].pop('email_address')
            if 'contact' in create_payload['artisan']:
                print("--- TOOL FIX: Renaming 'contact' -> 'contact_number' ---")
                create_payload['artisan']['contact_number'] = create_payload['artisan'].pop('contact')
            if 'aadhaar' in create_payload['artisan']:
                print("--- TOOL FIX: Renaming 'aadhaar' -> 'aadhaar_number' ---")
                create_payload['artisan']['aadhaar_number'] = create_payload['artisan'].pop('aadhaar')
            print("--- TOOL: Field name checks complete. ---") # Added debug print
        else:
            logger.error("[ip_agent] Invalid structure: 'artisan' key missing.")
            return {"status": "error", "message": "Internal data error (artisan)."}

        if 'art' in create_payload and isinstance(create_payload['art'], dict):
            create_payload['art'].pop('photo_url', None)
            create_payload['art']['photo'] = base64_string_with_prefix
        else:
            logger.error("[ip_agent] Invalid structure: 'art' key missing.")
            return {"status": "error", "message": "Internal data error (art)."}

        create_url = os.getenv("MASTER_IP_ENDPOINT", "https://master-ip-service-978458840399.asia-southeast1.run.app/create")
        logger.info(f"[ip_agent] Sending payload (fields corrected) to CREATE: {create_url}")
        print(f"--- TOOL: Final Payload for /create: {json.dumps(create_payload, indent=2)} ---")

        response = requests.post(create_url, json=create_payload, timeout=60)

        if response.status_code == 409:
            logger.warning(f"[ip_agent] 409 Conflict: {response.text}")
            error_detail = response.json().get("detail", "Similar name exists.")
            return {"status": "conflict", "message": error_detail, "response": response.text}

        response.raise_for_status()

        logger.info("[ip_agent] Successfully submitted to /create.")
        success_response_payload = {
            "status": "success",
            "message": response.json().get("message", "CraftID created."),
            "response": response.json(),
        }
        return success_response_payload

    except requests.exceptions.RequestException as e:
        logger.error(f"[ip_agent] /create request failed: {e}")
        error_details = e.response.text if hasattr(e, 'response') and e.response else str(e)
        logger.error(f"[ip_agent] Error details: {error_details}")
        print(f"--- TOOL ERROR (RequestException): {error_details} ---") # Added print
        return {"status": "error", "message": f"Unable to connect to CraftID creation service: {error_details}"}
    except Exception as e:
        logger.exception(f"[ip_agent] Unexpected error in /create call: {e}")
        print(f"--- TOOL ERROR (Exception): {e} ---") # Added print
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
load_dotenv()

ip_agent = Agent(
    name="ip_agent",
    model=os.getenv("MODEL_NAME"),
    description="Confirms details, searches for similar images, and submits unique artwork to the Master IP service.", # Updated description
    instruction=IP_PROMPT,
    tools=[
        call_image_similarity_search,
        call_metadata_similarity_search, # <-- REPLACED verify with image search
        call_master_ip_service,
    ],
    sub_agents=[shop_agent] # Keep shop_agent as the child
)