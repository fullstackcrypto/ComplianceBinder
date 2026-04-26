# Stripe Test Mode Setup

This app supports three launch products:

- Starter subscription: `$19/month`
- Pro subscription: `$49/month`
- Done-With-You Setup: `$299 one-time`

## 1. Create Stripe test products

In Stripe test mode:

1. Create product: `InspectionBinder Starter`
   - Recurring monthly price: `$19`
   - Copy the test price ID into `STRIPE_PRICE_STARTER`
2. Create product: `InspectionBinder Pro`
   - Recurring monthly price: `$49`
   - Copy the test price ID into `STRIPE_PRICE_PRO`
3. Create product: `Done-With-You Setup`
   - One-time price: `$299`
   - Copy the test price ID into `STRIPE_PRICE_SETUP`

## 2. Configure app environment

Set these values in staging:

```env
STRIPE_SECRET_KEY=<test mode secret key>
STRIPE_PRICE_STARTER=<test recurring price id>
STRIPE_PRICE_PRO=<test recurring price id>
STRIPE_PRICE_SETUP=<test one-time price id>
PUBLIC_APP_URL=https://<staging-domain>
```

## 3. Configure webhook

Create a webhook endpoint in Stripe test mode:

```text
https://<staging-domain>/billing/webhook
```

Subscribe to these events:

- `checkout.session.completed`
- `customer.subscription.updated`
- `customer.subscription.deleted`

Copy the webhook signing secret into:

```env
STRIPE_WEBHOOK_SECRET=<webhook signing secret>
```

## 4. Full payment-to-PDF test

1. Start from a fresh staging user.
2. Register and log in.
3. Create a binder.
4. Choose `Starter` or `Pro` checkout.
5. Use Stripe test card `4242 4242 4242 4242` with any valid future expiration and CVC.
6. Return to the app after checkout.
7. Refresh the page.
8. Confirm `/billing/status` returns `active` or `trialing`.
9. Open a binder report.
10. Click `Download PDF`.
11. Confirm the PDF downloads.

## 5. Failure checks

Also test:

- Unpaid user cannot download PDF report.
- Invalid plan returns a 400 error.
- Missing Stripe config returns 503 on checkout.
- Canceled subscription removes PDF export access after Stripe sends subscription deletion/update event.

## Notes

The app does not store card numbers. Stripe handles payment collection. The app stores plan/status metadata and customer/subscription identifiers needed to authorize paid features.
