# master-ip/server/chain/signer.py
import os
import json
import base64
from typing import Dict, Tuple
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

# DEV: For prototype, use PEM files. In production use KMS.
SIGNER_KEY_PATH = os.getenv("SIGNER_KEY_PATH", "../chain/keys/sign_priv.pem")
PLATFORM_PUBKEY_PATH = os.getenv("PLATFORM_PUBKEY_PATH", "../chain/keys/sign_pub.pem")

def _load_private_key():
    pem = open(SIGNER_KEY_PATH, "rb").read()
    return serialization.load_pem_private_key(pem, password=None)

def _load_public_key():
    pem = open(PLATFORM_PUBKEY_PATH, "rb").read()
    return serialization.load_pem_public_key(pem)

def sign_attestation(payload: Dict) -> Dict:
    """
    Returns {payload: ..., signature: base64}
    payload is canonical-serialized (sorted keys).
    """
    priv = _load_private_key()
    msg = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sig = priv.sign(msg, ec.ECDSA(hashes.SHA256()))
    return {"payload": payload, "signature": base64.b64encode(sig).decode("ascii")}

def verify_attestation(attestation: Dict) -> Tuple[bool, str]:
    """
    attestation: {payload, signature}
    returns (ok, error_message)
    """
    pub = _load_public_key()
    msg = json.dumps(attestation["payload"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sig = base64.b64decode(attestation["signature"])
    try:
        pub.verify(sig, msg, ec.ECDSA(hashes.SHA256()))
        return True, ""
    except InvalidSignature as e:
        return False, "invalid signature"
    except Exception as e:
        return False, str(e)
