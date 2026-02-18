import hashlib
import hmac
import os
import json

from fastapi import APIRouter, Request, HTTPException

from auth import add_credits

router = APIRouter()

# Lemonsqueezy product variant → credits mapping
CREDIT_PACKAGES = {
    # Replace these variant IDs with your actual Lemonsqueezy variant IDs
    "variant_100": 100,
    "variant_500": 500,
    "variant_2000": 2000,
    "variant_10000": 10000,
}


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode("utf-8"), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/webhook/lemonsqueezy")
async def lemonsqueezy_webhook(request: Request):
    secret = os.getenv("LEMONSQUEEZY_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    body = await request.body()
    signature = request.headers.get("x-signature", "")

    if not verify_webhook_signature(body, signature, secret):
        raise HTTPException(status_code=403, detail="Invalid signature")

    data = json.loads(body)
    event_name = data.get("meta", {}).get("event_name", "")

    if event_name == "order_created":
        attributes = data.get("data", {}).get("attributes", {})
        custom_data = data.get("meta", {}).get("custom_data", {})
        api_key = custom_data.get("api_key", "")
        variant_id = str(attributes.get("first_order_item", {}).get("variant_id", ""))

        # Look up credits by variant ID
        variant_key = f"variant_{variant_id}"
        credits_to_add = CREDIT_PACKAGES.get(variant_key)

        if not credits_to_add:
            # Fallback: try to determine from product name or amount
            product_name = attributes.get("first_order_item", {}).get("product_name", "")
            for pkg_credits in [100, 500, 2000, 10000]:
                if str(pkg_credits) in product_name:
                    credits_to_add = pkg_credits
                    break

        if not api_key:
            raise HTTPException(status_code=400, detail="Missing api_key in custom_data")

        if not credits_to_add:
            raise HTTPException(status_code=400, detail="Unknown product variant")

        new_balance = await add_credits(api_key, credits_to_add)
        return {"success": True, "credits_added": credits_to_add, "new_balance": new_balance}

    return {"success": True, "message": f"Event '{event_name}' received"}
