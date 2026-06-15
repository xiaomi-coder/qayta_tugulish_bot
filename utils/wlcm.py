import hashlib
import hmac
import json
import logging
import time
from urllib.parse import parse_qsl, urlencode

import aiohttp

logger = logging.getLogger(__name__)


def _build_canonical_path(path: str, query_string: str = "") -> str:
    params = sorted(parse_qsl(query_string, keep_blank_values=True))
    encoded = urlencode(params)
    return f"{path}?{encoded}" if encoded else path


def make_signature(api_secret: str, method: str, path: str,
                   query_string: str, timestamp: str, body: bytes) -> str:
    canonical = _build_canonical_path(path, query_string)
    body_hash = hashlib.sha256(body).hexdigest()
    message = f"{method.upper()}\n{canonical}\n{timestamp}\n{body_hash}"
    return hmac.new(
        key=api_secret.encode(),
        msg=message.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()


def verify_webhook_signature(api_secret: str, payload: dict) -> bool:
    """WLCM webhook imzosini tekshiradi.
    Format: order_id:payment_id:state:timestamp
    """
    received_sig = payload.get("signature", "")
    msg = (
        f"{payload.get('order_id', '')}:"
        f"{payload.get('payment_id', '')}:"
        f"{payload.get('state', '')}:"
        f"{payload.get('timestamp', '')}"
    )
    expected = hmac.new(
        key=api_secret.encode(),
        msg=msg.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(received_sig, expected)


async def create_checkout(
    api_key: str,
    api_secret: str,
    base_url: str,
    external_id: str,
    amount_som: int,
    payment_provider: str,
    return_url: str,
) -> dict:
    """WLCM checkout yaratadi, javobni qaytaradi."""
    path = "/api/v1/integrations/checkout"
    body_dict = {
        "external_id": external_id,
        "amount": amount_som * 100,  # tiyinga
        "payment_provider": payment_provider,
        "return_url": return_url,
    }
    body_bytes = json.dumps(body_dict, ensure_ascii=False, separators=(",", ":")).encode()
    timestamp = str(int(time.time() * 1000))
    sig = make_signature(api_secret, "POST", path, "", timestamp, body_bytes)

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
        "X-Timestamp": timestamp,
        "X-Signature": sig,
        "User-Agent": "curl/7.88.1",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}{path}", data=body_bytes, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                data = await resp.json()
                logger.info("WLCM checkout response %s: %s", resp.status, data)
                return {"status": resp.status, "data": data}
    except Exception as e:
        logger.error("WLCM checkout error: %s", e)
        return {"status": 0, "data": {"error": str(e)}}
