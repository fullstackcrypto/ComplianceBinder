# Payment-to-PDF Acceptance Test

This is the launch-critical test. If this fails, the SaaS is not ready to sell.

## Preconditions

- App is deployed to staging over HTTPS.
- Staging database is migrated with `alembic upgrade head`.
- Stripe test products/prices are configured.
- Stripe webhook is configured for the staging URL.
- `PUBLIC_APP_URL` matches the staging URL.
- The app can send users back from Stripe Checkout.

## Test steps

### 1. Fresh unpaid user

1. Open the staging app in a private browser window.
2. Register a new account.
3. Log in.
4. Create a binder named `Payment PDF Test`.
5. Choose industry `Assisted Living`.
6. Confirm the binder has starter tasks.
7. Open the report tab.
8. Click `Download PDF`.

Expected result:

- PDF download is blocked with payment-required behavior.

### 2. Start checkout

1. Click `Starter — $19/mo` or `Pro — $49/mo`.
2. Confirm Stripe Checkout opens.
3. Pay with Stripe test card:

```text
4242 4242 4242 4242
```

Use any future expiration date and any CVC.

Expected result:

- Stripe payment succeeds.
- User returns to `PUBLIC_APP_URL` with `?payment=success`.

### 3. Confirm billing state

1. Refresh the app.
2. Confirm the UI shows plan/status.
3. Call `/billing/status` while authenticated.

Expected result:

```json
{
  "plan": "starter",
  "status": "active"
}
```

`trialing` is also acceptable if Stripe is configured with trials.

### 4. Confirm PDF access

1. Re-open the binder.
2. Open the report tab.
3. Click `Download PDF`.

Expected result:

- A file named similar to `inspection-report-<id>.pdf` downloads.
- The PDF includes binder name, tasks, and uploaded document metadata.

### 5. Webhook verification

In Stripe test-mode event logs, confirm:

- `checkout.session.completed` was sent.
- Response status from the app was `200`.

If the app did not activate billing, inspect:

- `STRIPE_WEBHOOK_SECRET`
- `PUBLIC_APP_URL`
- webhook endpoint URL
- event subscriptions
- app logs around `/billing/webhook`

### 6. Cancellation test

1. Cancel the test subscription in Stripe.
2. Trigger or wait for `customer.subscription.deleted`.
3. Refresh app billing status.
4. Try PDF export again.

Expected result:

- Billing status becomes `canceled` or inactive.
- PDF export is blocked again.

## Pass criteria

This test passes only when:

- unpaid PDF export is blocked
- test payment succeeds
- webhook activates billing
- paid PDF export works
- cancellation removes access
