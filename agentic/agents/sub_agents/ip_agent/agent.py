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

        response = requests.post(meta_search_url, json=search_payload, timeout=90)
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
    SIMILARITY_THRESHOLD = 0.60
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
    Downloads the image from photo_url, converts it to Base64 (with prefix),
    applies failsafe field name corrections, and submits the complete data
    to the Master IP backend /create endpoint.

    Args:
        onboarding_data (str): JSON string containing onboarding details
                               (potentially with incorrect field names but
                               containing 'art.photo_url').

    Returns:
        dict: Structured response with status ('success', 'conflict', 'error'),
              message, and backend response.
    """
    try:
        # 1. Parse incoming data
        data_payload = json.loads(onboarding_data)

        # 2. Extract image URL
        image_url = data_payload.get("art", {}).get("photo_url")
        if not image_url:
            logger.error("[ip_agent] Photo URL missing for /create.")
            return {"status": "error", "message": "Artwork photo URL is missing."}

        # 3. Download image bytes
        logger.info(f"[ip_agent] Downloading image from: {image_url} for Base64 conversion.")
        try:
            image_response = requests.get(image_url, timeout=60) # Increased timeout for download
            image_response.raise_for_status()
            image_bytes = image_response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"[ip_agent] Failed image download for /create: {e}")
            return {"status": "error", "message": "Failed to retrieve image from URL."}

        # 4. Convert image bytes to Base64 string with prefix
        base64_encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        mime_type = "image/jpeg" if image_url.lower().endswith((".jpg", ".jpeg")) else "image/png"
        base64_string_with_prefix = f"data:{mime_type};base64,{base64_encoded_image}"
        print(f"--- TOOL: Base64 prefix generated: data:{mime_type};base64,... ---") # Debug print

        # 5. Prepare final payload AND APPLY FAILSAFE FIXES
        create_payload = json.loads(onboarding_data) # Fresh copy
        if 'artisan' in create_payload and isinstance(create_payload['artisan'], dict):
            print("--- TOOL /create: Checking for field name fixes... ---")
            if 'full_name' in create_payload['artisan']:
                 print("--- TOOL FIX /create: Renaming 'full_name' -> 'name' ---")
                 create_payload['artisan']['name'] = create_payload['artisan'].pop('full_name')
            if 'email_address' in create_payload['artisan']:
                print("--- TOOL FIX /create: Renaming 'email_address' -> 'email' ---")
                create_payload['artisan']['email'] = create_payload['artisan'].pop('email_address')
            if 'contact' in create_payload['artisan']:
                print("--- TOOL FIX /create: Renaming 'contact' -> 'contact_number' ---")
                create_payload['artisan']['contact_number'] = create_payload['artisan'].pop('contact')
            if 'aadhaar' in create_payload['artisan']:
                print("--- TOOL FIX /create: Renaming 'aadhaar' -> 'aadhaar_number' ---")
                create_payload['artisan']['aadhaar_number'] = create_payload['artisan'].pop('aadhaar')
            print("--- TOOL /create: Field name checks complete. ---")
        else:
            logger.error("[ip_agent] Invalid structure: 'artisan' key missing.")
            return {"status": "error", "message": "Internal data error (artisan)."}

        # Modify 'art' dictionary for Base64 photo
        if 'art' in create_payload and isinstance(create_payload['art'], dict):
            create_payload['art'].pop('photo_url', None) # Remove URL field
            create_payload['art']['photo'] = base64_string_with_prefix # Add Base64 field
        else:
            logger.error("[ip_agent] Invalid structure: 'art' key missing.")
            return {"status": "error", "message": "Internal data error (art)."}

        # 6. Send the FIXED payload to the /create endpoint
        create_url = os.getenv("MASTER_IP_ENDPOINT", "https://master-ip-service-978458840399.asia-southeast1.run.app/create")
        logger.info(f"[ip_agent] Sending payload (fields corrected, Base64 image) to CREATE endpoint: {create_url}")
        print(f"--- TOOL: Final Payload for /create: {json.dumps(create_payload, indent=2)} ---") # Debug print

        response = requests.post(create_url, json=create_payload, timeout=90) # Increased timeout further

        # 7. Handle Specific HTTP Errors
        if response.status_code == 409:
             logger.warning(f"[ip_agent] Received 409 Conflict from /create: {response.text}")
             error_detail = response.json().get("detail", "A similar product name already exists.")
             return {"status": "conflict", "message": error_detail, "response": response.text}
        elif response.status_code == 422:
             logger.error(f"[ip_agent] Received 422 Unprocessable Entity from /create: {response.text}")
             try:
                 error_detail = response.json().get("detail", "Validation error.")
                 if isinstance(error_detail, list) and error_detail:
                     first_error = error_detail[0]
                     error_msg = f"{first_error.get('msg', 'Validation error')} in field '{'.'.join(map(str, first_error.get('loc', ['unknown'])))}'"
                     error_detail = error_msg
             except json.JSONDecodeError:
                 error_detail = "Validation error (non-JSON response)."
             return {"status": "error", "message": f"Data validation failed on the server: {error_detail}", "response": response.text}

        response.raise_for_status() # Raise errors for other bad statuses

        # 8. Process successful response (200 or 201)
        logger.info("[ip_agent] Successfully submitted onboarding data to /create.")
        try:
            response_json = response.json()
            success_response_payload = {
                "status": "success",
                "message": response_json.get("message", "CraftID created successfully."),
                 "response": response_json, # Return the full backend JSON response
            }
        except json.JSONDecodeError:
             success_response_payload = { "status": "success", "message": "CraftID submitted successfully (non-JSON response).", "response": response.text }
        return success_response_payload

    # --- Robust Error Handling ---
    except json.JSONDecodeError as e:
        logger.error(f"[ip_agent] Invalid onboarding_data JSON format in /create tool: {e}")
        return {"status": "error", "message": "Invalid data format received."}
    except requests.exceptions.Timeout as e:
        logger.error(f"[ip_agent] /create request timed out: {e}")
        print(f"--- TOOL ERROR (Timeout): {e} ---")
        return {"status": "error", "message": "The request to the CraftID creation service timed out. Please try again later."}
    except requests.exceptions.RequestException as e:
        logger.error(f"[ip_agent] /create request failed: {e}")
        error_status = "Network/Connection"
        error_details = str(e)
        if hasattr(e, 'response') and e.response is not None:
             error_status = e.response.status_code
             try: error_details = e.response.json().get('detail', e.response.text)
             except: error_details = e.response.text
        logger.error(f"[ip_agent] Error details (Status {error_status}): {error_details}")
        print(f"--- TOOL ERROR (RequestException - Status {error_status}): {error_details} ---")
        return {"status": "error", "message": f"Unable to connect/process request with CraftID creation service ({error_status}). Please try later.", "details": error_details}
    except Exception as e:
        logger.exception(f"[ip_agent] Unexpected error in /create call: {e}")
        print(f"--- TOOL ERROR (Exception): {e} ---")
        return {"status": "error", "message": f"An unexpected error occurred during submission: {str(e)}"}
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