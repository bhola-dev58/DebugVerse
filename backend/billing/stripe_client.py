"""
Stripe Billing Client for DebugVerse.

Handles:
  - Checkout session creation (free → pro upgrade flow)
  - Stripe webhook processing (subscription events)
  - Billing portal session (manage subscription)
  - Subscription status lookup

Pricing Tiers:
  - Free     : $0/month  — 10 debugs/day
  - Pro      : $19/month — Unlimited, all models
  - Enterprise: $49/seat — Team features + SSO
"""

import os
import logging
from typing import Optional, Dict, Any

from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger(__name__)

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRO_PRICE_ID = os.getenv("STRIPE_PRO_PRICE_ID", "")
STRIPE_ENTERPRISE_PRICE_ID = os.getenv("STRIPE_ENTERPRISE_PRICE_ID", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Lazy import stripe to avoid startup failure when key not set
_stripe = None

def _get_stripe():
    global _stripe
    if _stripe is not None:
        return _stripe
    if not STRIPE_SECRET_KEY:
        logger.warning("STRIPE_SECRET_KEY not set — billing features disabled.")
        return None
    try:
        import stripe as _stripe_module
        _stripe_module.api_key = STRIPE_SECRET_KEY
        _stripe = _stripe_module
        logger.info("Stripe client initialized.")
        return _stripe
    except ImportError:
        logger.error("stripe package not installed. Run: pip install stripe")
        return None


# ── Pricing plan map ───────────────────────────────────────────────────────────
PLAN_PRICE_MAP = {
    "pro": STRIPE_PRO_PRICE_ID,
    "enterprise": STRIPE_ENTERPRISE_PRICE_ID,
}

PRICE_TIER_MAP: Dict[str, str] = {}  # populated on first webhook: price_id → tier


def create_checkout_session(
    user_id: str,
    user_email: str,
    plan: str = "pro",
) -> Optional[str]:
    """
    Create a Stripe Checkout Session for upgrading to Pro or Enterprise.
    Returns the Stripe-hosted checkout URL or None if Stripe is not configured.
    """
    stripe = _get_stripe()
    if not stripe:
        return None

    price_id = PLAN_PRICE_MAP.get(plan)

    # If an explicit Stripe Price ID is configured, use it.
    # Otherwise, fallback to dynamic Stripe Checkout price_data so it works out-of-the-box.
    if price_id:
        line_items = [{"price": price_id, "quantity": 1}]
    elif plan == "pro":
        line_items = [{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "DebugVerse Pro",
                    "description": "Unlimited AI debugs, Claude 3.5 + Gemini 2.5 Flash, multi-agent pipeline",
                },
                "unit_amount": 1900,  # $19.00 / month
                "recurring": {"interval": "month"},
            },
            "quantity": 1,
        }]
    elif plan == "enterprise":
        line_items = [{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "DebugVerse Enterprise",
                    "description": "Team workspace, private RAG indexing, SLA, priority support",
                },
                "unit_amount": 4900,  # $49.00 / seat / month
                "recurring": {"interval": "month"},
            },
            "quantity": 1,
        }]
    else:
        raise ValueError(f"Unknown plan '{plan}'. Valid plans: ['pro', 'enterprise']")

    try:
        session = stripe.checkout.Session.create(
            customer_email=user_email,
            mode="subscription",
            line_items=line_items,
            success_url=f"{FRONTEND_URL}/dashboard?upgraded=true",
            cancel_url=f"{FRONTEND_URL}/pricing?cancelled=true",
            metadata={
                "user_id": user_id,
                "plan": plan,
            },
            allow_promotion_codes=True,
            subscription_data={
                "metadata": {"user_id": user_id, "plan": plan},
            },
        )
        logger.info(f"Checkout session created for user {user_id}, plan={plan}")
        return session.url
    except Exception as e:
        logger.error(f"Failed to create Stripe checkout session: {e}")
        raise


def create_billing_portal_session(stripe_customer_id: str) -> Optional[str]:
    """
    Create a Stripe Billing Portal session so the user can manage their subscription.
    Returns the portal URL.
    """
    stripe = _get_stripe()
    if not stripe:
        return None
    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=f"{FRONTEND_URL}/dashboard",
        )
        return session.url
    except Exception as e:
        logger.error(f"Failed to create billing portal session: {e}")
        raise


def handle_stripe_webhook(payload: bytes, sig_header: str) -> Dict[str, Any]:
    """
    Process incoming Stripe webhook events.
    Updates the Supabase subscriptions table on subscription changes.
    Returns a dict describing what was processed.
    """
    stripe = _get_stripe()
    if not stripe:
        return {"status": "skipped", "reason": "Stripe not configured"}

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Stripe webhook signature verification failed: {e}")
        raise ValueError("Invalid Stripe webhook signature")

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info(f"Processing Stripe webhook: {event_type}")

    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        _upsert_subscription(
            stripe_customer_id=data["customer"],
            stripe_subscription_id=data["id"],
            status=data["status"],
            price_id=data["items"]["data"][0]["price"]["id"] if data.get("items") else None,
            metadata=data.get("metadata", {}),
        )

    elif event_type == "customer.subscription.deleted":
        _cancel_subscription(
            stripe_customer_id=data["customer"],
            stripe_subscription_id=data["id"],
        )

    elif event_type == "checkout.session.completed":
        # Ensure metadata links user to subscription
        metadata = data.get("metadata", {})
        user_id = metadata.get("user_id")
        if user_id and data.get("subscription"):
            logger.info(f"Checkout completed for user {user_id}, subscription {data['subscription']}")

    return {"status": "processed", "event_type": event_type}


def _upsert_subscription(
    stripe_customer_id: str,
    stripe_subscription_id: str,
    status: str,
    price_id: Optional[str],
    metadata: Dict,
) -> None:
    """Upsert subscription record in Supabase."""
    try:
        from auth.supabase_client import _get_supabase
        client = _get_supabase()
        if not client:
            logger.warning("Supabase not available — skipping subscription upsert.")
            return

        # Determine tier from price_id
        tier = "free"
        if price_id:
            if price_id == STRIPE_PRO_PRICE_ID:
                tier = "pro"
            elif price_id == STRIPE_ENTERPRISE_PRICE_ID:
                tier = "enterprise"

        user_id = metadata.get("user_id")
        if not user_id:
            logger.warning(f"No user_id in subscription metadata for customer {stripe_customer_id}")
            return

        client.table("subscriptions").upsert({
            "user_id": user_id,
            "stripe_customer_id": stripe_customer_id,
            "stripe_subscription_id": stripe_subscription_id,
            "tier": tier,
            "status": "active" if status == "active" else "inactive",
        }, on_conflict="stripe_subscription_id").execute()

        logger.info(f"Subscription upserted: user={user_id}, tier={tier}, status={status}")
    except Exception as e:
        logger.error(f"Failed to upsert subscription: {e}")


def _cancel_subscription(stripe_customer_id: str, stripe_subscription_id: str) -> None:
    """Mark subscription as cancelled in Supabase."""
    try:
        from auth.supabase_client import _get_supabase
        client = _get_supabase()
        if not client:
            return
        client.table("subscriptions").update(
            {"status": "cancelled", "tier": "free"}
        ).eq("stripe_subscription_id", stripe_subscription_id).execute()
        logger.info(f"Subscription cancelled: {stripe_subscription_id}")
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")


def get_subscription_status(user_id: str) -> Dict[str, Any]:
    """Return the current subscription status and tier for a user."""
    try:
        from auth.supabase_client import _get_supabase
        client = _get_supabase()
        if not client:
            return {"tier": "pro", "status": "active", "dev_mode": True}

        result = (
            client.table("subscriptions")
            .select("tier,status,stripe_customer_id,created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]
        return {"tier": "free", "status": "active"}
    except Exception as e:
        logger.error(f"Failed to get subscription status: {e}")
        return {"tier": "free", "status": "unknown"}
