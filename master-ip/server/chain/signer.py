import os
import json
from typing import Dict, Tuple
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

# Load paths directly from environment variables.
SIGNER_KEY_PATH = os.getenv("SIGNER_KEY_PATH")
PLATFORM_PUBKEY_PATH = os.getenv("PLATFORM_PUBKEY_PATH")

# Add checks to fail fast if the environment variables are missing
if not SIGNER_KEY_PATH:
    raise EnvironmentError("SIGNER_KEY_PATH environment variable not set.")
if not PLATFORM_PUBKEY_PATH:
    raise EnvironmentError("PLATFORM_PUBKEY_PATH environment variable not set.")

# Cache for the loaded keys
_priv_key_cache = None
_pub_key_cache = None

def _load_private_key():
    """
    Loads the private key from the path specified by SIGNER_KEY_PATH.
    """
    global _priv_key_cache
    if _priv_key_cache:
        return _priv_key_cache
    
    try:
        # This will now correctly open /run/secrets/sign_priv.pem in Cloud Run
        with open(SIGNER_KEY_PATH, "rb") as pem_file:
            pem = pem_file.read()
            
    # --- SAFER ERROR HANDLING ---
    # Catch the FileNotFoundError specifically
    except FileNotFoundError:
        # DO NOT print the path, as it might contain the secret.
        raise FileNotFoundError("Signer private key not found at the specified path.")
    # Catch if the path is actually the key content
    except (OSError, NotADirectoryError, TypeError) as e:
        # This catches errors like "File name too long" or "Invalid argument"
        # which happen when the path is actually the key content.
        raise EnvironmentError(
            f"Failed to open private key. "
            f"Ensure SIGNER_KEY_PATH is a valid FILE PATH, not the key content itself. Error: {e}"
        )
    # --- END SAFER ERROR HANDLING ---
        
    try:
        _priv_key_cache = serialization.load_pem_private_key(pem, password=None)
    except Exception as e:
        # Error parsing the key file
        raise ValueError(f"Failed to parse private key from {SIGNER_KEY_PATH}: {e}")
        
    return _priv_key_cache

def _load_public_key():
    """
    Loads the public key from the path specified by PLATFORM_PUBKEY_PATH.
    """
    global _pub_key_cache
    if _pub_key_cache:
        return _pub_key_cache
    
    try:
        with open(PLATFORM_PUBKEY_PATH, "rb") as pem_file:
            pem = pem_file.read()
    except FileNotFoundError:
        raise FileNotFoundError("Platform public key not found at the specified path.")
    except (OSError, NotADirectoryError, TypeError) as e:
         raise EnvironmentError(
            f"Failed to open public key. "
            f"Ensure PLATFORM_PUBKEY_PATH is a valid FILE PATH, not the key content itself. Error: {e}"
        )

    try:
        _pub_key_cache = serialization.load_pem_public_key(pem)
    except Exception as e:
         raise ValueError(f"Failed to parse public key from {PLATFORM_PUBKEY_PATH}: {e}")
         
    return _pub_key_cache

def sign_attestation(payload: Dict) -> str:
    """
    Signs a payload dictionary and returns a hex signature.
    Matches the att_payload from the controller.
    """
    priv = _load_private_key()
    
    # Create a deterministic, canonical JSON string for signing
    message = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    
    signature = priv.sign(
        message,
        # --- THIS IS THE FIX ---
        ec.ECDSA(hashes.SHA256()) # Changed SHA2S56 to SHA256
        # --- END FIX ---
    )
    return signature.hex()

def verify_attestation(payload: Dict, signature_hex: str) -> Tuple[bool, str]:
    """
    Verifies a signature against a payload using the platform public key.
    """
    pub = _load_public_key()
    
    try:
        signature = bytes.fromhex(signature_hex)
    except ValueError:
        return False, "invalid signature hex"
        
    message = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    
    try:
        pub.verify(
            signature,
            message,
            # --- THIS IS THE FIX ---
            ec.ECDSA(hashes.SHA256()) # Changed SHA2S56 to SHA256
            # --- END FIX ---
        )
        return True, ""
    except InvalidSignature:
        return False, "invalid signature"
    except Exception as e:
        return False, str(e)