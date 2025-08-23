import hashlib
import time
from google.adk.agents import Agent

def generate_craft_id(product_name: str, artisan_name: str, product_description: str) -> dict:
    """Generates a mock digital certificate (CraftID) for a product.

    Args:
        product_name (str): The name of the product.
        artisan_name (str): The name of the artisan.
        product_description (str): A description of the product.

    Returns:
        dict: A dictionary containing the CraftID, a simulated blockchain hash, and a success status.
    """
    # Create a simple hash as a mock IP certificate/blockchain signature
    data_to_hash = f"{product_name}{artisan_name}{product_description}{time.time()}"
    hash_value = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()

    craft_id = f"CRAFT-{hash_value[:10].upper()}"
    
    # In a real-world scenario, this would be a more robust ID and the hash
    # would be stored on a blockchain, but for the MVP, this simulates it.
    
    return {
        "status": "success",
        "craft_id": craft_id,
        "blockchain_hash": hash_value,
        "message": "CraftID generated successfully. This is your digital certificate of authenticity."
    }

root_agent = Agent(
    name="artisan_platform_agent",
    model="gemini-2.0-flash",
    description=(
        "An agent for the Artisan Platform that helps generate digital certificates (CraftIDs) "
        "and provides marketing support for cultural crafts."
    ),
    instruction=(
        "You are a helpful assistant for artisans. Your primary function is to "
        "take product details and generate a unique digital certificate of authenticity (CraftID) "
        "and a corresponding hash. Provide the generated CraftID and hash back to the user."
    ),
    tools=[generate_craft_id],
)