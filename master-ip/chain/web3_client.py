# master-ip/server/chain/web3_client.py
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

RPC = os.getenv("WEB3_RPC_URL", "https://rpc-amoy.polygon.technology")
CONTRACT_ADDR = os.getenv("ANCHOR_CONTRACT_ADDRESS", "")
ANCHORER_PRIVATE_KEY = os.getenv("ANCHORER_PRIVATE_KEY", None)  # dev only
CHAIN_ID = int(os.getenv("CHAIN_ID", "80002"))  # Amoy default (Mumbai was 80001)

# Minimal ABI for CraftAnchor (anchor + isAnchored view)
CRAFT_ANCHOR_ABI = [
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

def _get_contract():
    if not CONTRACT_ADDR:
        raise RuntimeError("ANCHOR_CONTRACT_ADDRESS not set")
    return WEB3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDR), abi=CRAFT_ANCHOR_ABI)

def _to_bytes32(hex_str: str) -> bytes:
    h = hex_str[2:] if hex_str.startswith("0x") else hex_str
    if len(h) != 64:
        # pad left if needed (shouldn't normally happen)
        h = h.rjust(64, "0")
    return bytes.fromhex(h)

def anchor_hash_on_chain(hash_hex: str, public_id: str, wait_for_receipt: bool = True, timeout: int = 120) -> str:
    """
    Sends anchor(hash, public_id) tx and returns tx_hash hex string.
    WAIT: uses local private key (dev only). For production use KMS signing.
    """
    if not ANCHORER_PRIVATE_KEY:
        raise RuntimeError("ANCHORER_PRIVATE_KEY not set in env")
    contract = _get_contract()
    acct = WEB3.eth.account.from_key(ANCHORER_PRIVATE_KEY)
    tx = contract.functions.anchor(_to_bytes32(hash_hex), public_id).build_transaction({
        "from": acct.address,
        "nonce": WEB3.eth.get_transaction_count(acct.address),
        "chainId": CHAIN_ID,
        "gas": 200000
    })
    signed = WEB3.eth.account.sign_transaction(tx, ANCHORER_PRIVATE_KEY)
    # web3.py v6+: use raw_transaction (lowercase with underscore)
    # web3.py v5: use rawTransaction (camelCase)
    raw_tx = getattr(signed, 'raw_transaction', None) or getattr(signed, 'rawTransaction')
    tx_hash = WEB3.eth.send_raw_transaction(raw_tx)
    tx_hash_hex = tx_hash.hex()
    if wait_for_receipt:
        start = time.time()
        while True:
            try:
                receipt = WEB3.eth.get_transaction_receipt(tx_hash)
                return tx_hash_hex
            except TransactionNotFound:
                if time.time() - start > timeout:
                    raise TimeoutError("tx receipt timeout")
                time.sleep(2)
    return tx_hash_hex

def is_anchored(hash_hex: str) -> Tuple[bool, int]:
    """
    Returns (anchored_bool, anchored_at_unix_ts_or_0)
    """
    contract = _get_contract()
    anchored, ts = contract.functions.isAnchored(_to_bytes32(hash_hex)).call()
    return anchored, int(ts)
