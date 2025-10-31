import os
import time
from web3 import Web3
try:
    # Try newer web3.py import path (v6+)
    from web3.middleware import ExtraDataToPOAMiddleware
    geth_poa_middleware = ExtraDataToPOAMiddleware
except ImportError:
    # Fallback to older import path (v5)
    from web3.middleware import geth_poa_middleware
from web3.exceptions import TransactionNotFound
from typing import Tuple

RPC = os.getenv("WEB3_RPC_URL")
CONTRACT_ADDR = os.getenv("ANCHOR_CONTRACT_ADDRESS")
ANCHORER_PRIVATE_KEY_PATH = os.getenv("ANCHORER_PRIVATE_KEY") # Renamed for clarity
CHAIN_ID = int(os.getenv("CHAIN_ID", "80002"))  # Amoy default

# --- Fail-fast Checks ---
if not RPC:
    raise EnvironmentError("WEB3_RPC_URL environment variable not set.")
if not CONTRACT_ADDR:
    raise EnvironmentError("ANCHOR_CONTRACT_ADDRESS environment variable not set.")
if not ANCHORER_PRIVATE_KEY_PATH:
    # Changed variable name in error message
    raise EnvironmentError("ANCHORER_PRIVATE_KEY environment variable (containing the path) not set.")
# --- End Checks ---

# Minimal ABI for CraftAnchor (anchor + isAnchored view)
CRAFT_ANCHOR_ABI = [
    # ... (ABI remains the same) ...
    {
      "inputs":[{"internalType":"bytes32","name":"h","type":"bytes32"},{"internalType":"string","name":"publicId","type":"string"}],
      "name":"anchor",
      "outputs":[],
      "stateMutability":"nonpayable",
      "type":"function"
    },
    {
      "inputs":[{"internalType":"bytes32","name":"h","type":"bytes32"}],
      "name":"isAnchored",
      "outputs":[{"internalType":"bool","name":"","type":"bool"},{"internalType":"uint256","name":"","type":"uint256"}],
      "stateMutability":"view",
      "type":"function"
    }
]

# Initialize Web3 with POA middleware (required for Polygon)
WEB3 = Web3(Web3.HTTPProvider(RPC))
WEB3.middleware_onion.inject(geth_poa_middleware, layer=0)

# --- NEW: Function to load the private key from file ---
_anchor_key_cache = None

def _load_anchor_private_key():
    """Loads the anchorer private key from the file path."""
    global _anchor_key_cache
    if _anchor_key_cache:
        return _anchor_key_cache

    try:
        with open(ANCHORER_PRIVATE_KEY_PATH, "r") as key_file:
            # Read the key, remove leading/trailing whitespace/newlines
            key_content = key_file.read().strip()
            _anchor_key_cache = key_content
            return _anchor_key_cache
    except FileNotFoundError:
        raise FileNotFoundError(f"Anchorer private key file not found at path: {ANCHORER_PRIVATE_KEY_PATH}")
    except (OSError, TypeError) as e:
        raise EnvironmentError(
            f"Failed to open anchorer private key file. "
            f"Ensure ANCHORER_PRIVATE_KEY env var points to a valid FILE PATH. Error: {e}"
        )
    except Exception as e:
         raise ValueError(f"Failed to read anchorer private key from {ANCHORER_PRIVATE_KEY_PATH}: {e}")
# --- END NEW FUNCTION ---

def _get_contract():
    return WEB3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDR), abi=CRAFT_ANCHOR_ABI)

def _to_bytes32(hex_str: str) -> bytes:
    h = hex_str[2:] if hex_str.startswith("0x") else hex_str
    if len(h) != 64:
        h = h.rjust(64, "0")
    try:
        return bytes.fromhex(h)
    except ValueError as e:
        # Catch the specific error if hash_hex is bad
        raise ValueError(f"Invalid public_hash provided to _to_bytes32: '{hex_str[:10]}...' - {e}") from e


def anchor_hash_on_chain(hash_hex: str, public_id: str, wait_for_receipt: bool = True, timeout: int = 120) -> str:
    """
    Sends anchor(hash, public_id) tx and returns tx_hash hex string.
    """
    contract = _get_contract()
    # --- FIX: Load key content from file ---
    anchor_key = _load_anchor_private_key()
    try:
        acct = WEB3.eth.account.from_key(anchor_key)
    except ValueError as e:
         # Handle case where the key content itself is invalid hex
         raise ValueError(f"Invalid anchorer private key format loaded from file: {e}") from e
    # --- END FIX ---

    try:
        bytes32_hash = _to_bytes32(hash_hex)
    except ValueError as e:
        # Propagate error if hash_hex is invalid before sending tx
        raise e

    tx = contract.functions.anchor(bytes32_hash, public_id).build_transaction({
        "from": acct.address,
        "nonce": WEB3.eth.get_transaction_count(acct.address),
        "chainId": CHAIN_ID,
        "gas": 200000 # Consider making gas configurable or estimating it
        # You might need to add gasPrice or maxFeePerGas/maxPriorityFeePerGas for non-legacy networks
    })

    # --- FIX: Use loaded key content for signing ---
    signed = WEB3.eth.account.sign_transaction(tx, anchor_key)
    # --- END FIX ---

    raw_tx = getattr(signed, 'raw_transaction', None) or getattr(signed, 'rawTransaction')
    tx_hash = WEB3.eth.send_raw_transaction(raw_tx)
    tx_hash_hex = tx_hash.hex()

    if wait_for_receipt:
        start = time.time()
        while True:
            try:
                receipt = WEB3.eth.get_transaction_receipt(tx_hash)
                # Check receipt status for success (optional but recommended)
                if receipt is None:
                     # Still pending
                     pass
                elif receipt.status == 0:
                     raise Exception(f"Transaction {tx_hash_hex} failed (receipt status 0)")
                elif receipt.status == 1:
                     return tx_hash_hex # Success!
                else: # Should not happen
                     raise Exception(f"Transaction {tx_hash_hex} has unexpected status {receipt.status}")

            except TransactionNotFound:
                pass # Keep waiting

            if time.time() - start > timeout:
                raise TimeoutError(f"tx receipt timeout after {timeout}s for {tx_hash_hex}")
            time.sleep(2) # Wait before polling again

    return tx_hash_hex # Return hash if not waiting for receipt


def is_anchored(hash_hex: str) -> Tuple[bool, int]:
    """
    Returns (anchored_bool, anchored_at_unix_ts_or_0)
    """
    contract = _get_contract()
    try:
        bytes32_hash = _to_bytes32(hash_hex)
    except ValueError as e:
        # If hash is invalid, it can't be anchored
        print(f"Warning: Invalid hash passed to is_anchored: {e}") # Or use logger
        return False, 0
    anchored, ts = contract.functions.isAnchored(bytes32_hash).call()
    return anchored, int(ts)