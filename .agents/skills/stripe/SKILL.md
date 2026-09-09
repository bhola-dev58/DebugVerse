---
name: stripe
description: "Expert guidance for Stripe Billing, Checkout Sessions, Webhooks, Customer Portal, and Subscriptions."
---

# Stripe Integration Best Practices & Architecture

## Core Concepts
1. **Stripe Checkout**:
   - Use `mode: 'subscription'` for recurring SaaS tiers.
   - Always pass `metadata: { user_id, plan }` on both the session and `subscription_data.metadata`.
   - Prefer passing dynamic `price_data` if static price IDs are not configured yet, for instant zero-config billing.
   - Specify `success_url` and `cancel_url` pointing to frontend application.

2. **Webhooks & Idempotency**:
   - Verify signatures using `stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)`.
   - Always return `200 OK` quickly. Heavy work or external DB calls should handle retries gracefully.
   - Handle key events:
     - `checkout.session.completed`: Upgrade user tier in database.
     - `customer.subscription.updated`: Update status (`active`, `past_due`, `cancelled`).
     - `customer.subscription.deleted`: Downgrade user to `free` tier.
     - `invoice.payment_failed`: Mark subscription `past_due`.

3. **Customer Portal**:
   - Generate session via `stripe.billing_portal.Session.create(customer=stripe_customer_id, return_url=...)`.
   - Enables users to update payment methods, cancel subscriptions, and view invoices without custom UI.

4. **Security**:
   - NEVER expose `STRIPE_SECRET_KEY` or `STRIPE_WEBHOOK_SECRET` to the frontend or browser.
   - Only `pk_test_...` or `pk_live_...` (Publishable Key) can exist on client side.
