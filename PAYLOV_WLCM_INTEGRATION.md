---
name: paylov-wlcm-integration
description: Complete, battle-tested guide for integrating the Paylov (WLCM) payment aggregator into any app — from legal contract through sandbox testing to live production. Covers HMAC auth, checkout, webhooks, the onboarding-token → API-key bootstrap, fiscalization, and a webhook+polling architecture. Written so a human dev or an AI agent can execute it end-to-end.
version: 1.0
last_verified: 2026-06-19
---

# Paylov (WLCM) Payment Integration — End-to-End Guide

> **What this is.** A reproducible playbook for wiring the **Paylov / WLCM** payment
> aggregator into a backend (Telegram bot, web app, API — anything that can sign HTTP
> requests and host an HTTPS endpoint). Every step here was verified against the live
> system. Follow it top to bottom.

> **Audience.** Solo devs / "vibe coders" and AI agents. Steps are explicit and ordered.
> When a step needs a human (signing a contract, paying with a real card), it is marked
> **[HUMAN]**. Everything else an agent can automate.

---

## 0. Mental model (read this first)

- **WLCM (brand: Paylov) is an *aggregator*.** You integrate **once**. Every payment
  provider enabled on your partner account (Payme, Click, Paylov, Uzcard/Humo card,
  Uzum…) then works through the **same** API and the **same** credentials. There is no
  per-provider integration — you just change one field (`payment_provider`).
- **One hard thing, then everything is easy.** ~90% of integration effort is getting
  **authentication** right (HMAC signing) and, for production, the **onboarding-token →
  API-key bootstrap**. Once that works, adding providers, webhooks, refunds, etc. is
  trivial.
- **Never trust a payment notification blindly.** Treat the webhook as a *"go check"*
  signal and confirm payment via the order-status API. This is both a security control
  and a reliability fallback.

### Environments

| Env        | API base URL              | Frontend / playground      | Docs                  |
|------------|---------------------------|----------------------------|-----------------------|
| Sandbox    | `https://apidev.wlcm.uz`  | `https://sandbox.wlcm.uz`  | `https://docs.wlcm.uz`|
| Production | `https://api.wlcm.uz`     | business panel (separate)  | `https://docs.wlcm.uz`|

Sandbox and production are **separate accounts with separate credentials**. The request
formats are identical; only `base_url` and the credentials change.

---

## 1. Authentication (the core — works for sandbox AND production)

Every authenticated request is signed with HMAC-SHA256. You need an **API key** and an
**API secret**.

**Required headers**

| Header          | Value                                            |
|-----------------|--------------------------------------------------|
| `X-API-Key`     | your API key (`wlcm_...`)                         |
| `X-Timestamp`   | Unix time in **milliseconds** (must be within 300s) |
| `X-Signature`   | HMAC-SHA256 hex (see below)                       |
| `Content-Type`  | `application/json`                                |

**Signature algorithm**

```
canonical_path = path
# if there is a query string: sort params, urlencode, append as "path?enc"
body_sha256    = sha256(raw_request_body_bytes).hexdigest()   # empty body for GET
message        = f"{METHOD}\n{canonical_path}\n{timestamp}\n{body_sha256}"
signature      = hmac_sha256(key=api_secret, msg=message).hexdigest()
```

**Reference implementation (Python, stdlib only)**

```python
import hashlib, hmac, json, time
from urllib.parse import parse_qsl, urlencode

def _canonical(path: str, query: str = "") -> str:
    params = sorted(parse_qsl(query, keep_blank_values=True))
    enc = urlencode(params)
    return f"{path}?{enc}" if enc else path

def make_signature(api_secret, method, path, query, ts, body: bytes) -> str:
    msg = f"{method.upper()}\n{_canonical(path, query)}\n{ts}\n{hashlib.sha256(body).hexdigest()}"
    return hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

def signed_headers(api_key, api_secret, method, path, body: bytes = b"", query=""):
    ts = str(int(time.time() * 1000))
    return {
        "X-API-Key": api_key,
        "X-Timestamp": ts,
        "X-Signature": make_signature(api_secret, method, path, query, ts, body),
        "Content-Type": "application/json",
        # Some edge/CDN configs reject default Python/curl UAs — set a normal one:
        "User-Agent": "curl/7.88.1",
    }
```

**Gotchas**
- HMAC key is the **raw `api_secret`**, not a hash of it.
- The signature is over the **exact raw body bytes** you send — sign the same bytes you transmit.
- `X-Timestamp` is **milliseconds**. Wrong unit or >300s skew → `401`.
- If an **IP whitelist** is set on your key, requests only work from allowed IPs. Run
  server-to-server from the whitelisted host.

---

## 2. Phase A — Legal & fiscal setup  **[HUMAN]**

You cannot go live without these. Do them in parallel with sandbox testing.

1. **Register a legal entity** — an `ИП/ЯТТ` (individual entrepreneur) or LLC with a STIR/PINFL.
2. **Sign the acquiring contract** ("Эквайринг шартномаси") with the aggregator
   (legal entity: `OCTAGRAM AJ` for WLCM). Typically signed electronically via **Didox**
   with an **E-IMZO** digital signature. Free-form document → recipient by STIR → sign → send.
3. **Add the aggregator as a *commissioner*** in your tax cabinet `my3.soliq.uz`
   (section "Комиссионерлар"). Needed so the aggregator can issue **fiscal receipts** on
   your behalf. You'll enter the aggregator's STIR, bank MFO + account, contract no./date,
   your own PINFL as sub-comitent, and pick the system type (e.g. "Маркетплейс").
4. **Know your VAT status.** New/small entities are usually **not** VAT (`QQS`) payers
   (turnover tax regime). Confirm via the VAT-payers registry on `soliq.uz`. The aggregator
   needs this to format fiscal receipts correctly.
5. **Request production credentials** via an official letter (the aggregator will tell you
   the format). The letter declares the **server IP(s)** to whitelist for the token.

**Typical commission (verify in your contract's tariff annex):** Payme 2%, Uzum 2%,
Click 2.5%, Uzcard/Humo card 1.5%. The fee is withheld from settlement; the bank remits
the net to your account (commonly within ~3 business days).

---

## 3. Phase B — Sandbox integration & testing

Goal: prove your code creates checkouts, receives webhooks, and confirms payments —
**before** touching real money.

### 3.1 Get sandbox credentials
The aggregator gives you a sandbox `api_key` (`wlcm_...`) + `api_secret`. Set:
```
WLCM_BASE_URL=https://apidev.wlcm.uz
WLCM_API_KEY=wlcm_xxx
WLCM_API_SECRET=xxx
```

### 3.2 Smoke-test auth
```python
import urllib.request
path = "/api/v1/partners/me"
h = signed_headers(API_KEY, API_SECRET, "GET", path)
req = urllib.request.Request(BASE + path, headers=h)  # GET
print(urllib.request.urlopen(req).read())   # 200 + partner info == auth works
```

### 3.3 Create a checkout
`POST /api/v1/integrations/checkout`

```jsonc
// request body
{
  "external_id": "42",            // YOUR payment id — you get it back in the webhook
  "amount": 14900000,             // in TIYIN  (som * 100). 149 000 som -> 14900000
  "payment_provider": "payme",    // "payme" | "click" | "paylov" | "card" | "uzum"
  "return_url": "https://t.me/YourBot"
}
```
```jsonc
// response
{
  "order_id": 48,                 // WLCM's order id — STORE THIS (needed to poll status)
  "external_id": "42",
  "state": 1,
  "checkout_url": "https://checkout.paycom.uz/...",  // redirect the user here
  ...
}
```
For a **direct card** charge you may pass `card_number` + `expire_date` and then confirm
with an OTP via `POST /api/v1/integrations/card/confirm` (`{transaction_id, cid, otp}`).

> **Persist `order_id` (as `wlcm_order_id`) against your payment row.** You need it to poll
> status and to reconcile webhooks.

### 3.4 Order status (the source of truth — **no auth required**)
`GET /api/v1/orders/{order_id}/status`
```jsonc
{ "order_id": 48, "amount": 149000.0, "is_paid": true, "state": 2,
  "status": "paid", "status_explanation": {"state": "2", ...} }
```
`is_paid: true` / `state: 2` ⇒ paid. This endpoint is your reliability anchor.

**State codes:** `0` created · `1` initiating/pending · `2` **success/paid** · `-1`
cancelled during init · `-2` cancelled.

### 3.5 Webhooks
Register an HTTPS endpoint the aggregator will POST to on payment events.

`POST /api/v1/partners/me/webhooks`  body `{"url": "https://you.example/wlcm/webhook", "secret_key": "<any-secret>"}`
- Manage: `GET` (list), `PATCH /{id}`, `DELETE /{id}`.
- Delivery log: `GET /api/v1/partners/me/webhooks/{id}/events` → shows `last_triggered_at`,
  `last_status_code`, and per-event `status`/`response_code`. Use this to debug delivery.

**Webhook payload you will receive (WLCM → you):**
```
POST https://you.example/wlcm/webhook
X-Webhook-Event: payment.success
X-Webhook-Signature: <hmac_sha256_hex>
{
  "external_id": "42", "order_id": 48, "payment_id": 73,
  "amount": "149000.00", "state": 2, "provider": "payme",
  "timestamp": 1781605686404, "signature": "..."
}
```

> **CRITICAL GOTCHA — event name.** The real emitted event is **`payment.success`**, even
> though the dashboard/docs sometimes display `payment.update`, and the API's webhook-create
> endpoint may ignore/normalize the `events` field. **Do not branch on the event name.**
> Instead, on *any* webhook: read `external_id`, look up your payment, and **confirm via
> `GET /orders/{order_id}/status`** before granting value. This sidesteps event-name and
> signature-format ambiguity entirely.

### 3.6 Simulate a real payment in sandbox (no money, no UI clicking)
Sandbox uses a mock Payme gateway you can drive over JSON-RPC:

`POST /api/v1/webhooks/mock-payme` (no auth)
```jsonc
// 1) create transaction
{"jsonrpc":"2.0","id":1,"method":"CreateTransaction",
 "params":{"id":"mock_tx_123","time":<unix_ms>,"amount":14900000,
           "account":{"order_id":"<order_id_from_checkout>"}}}
// 2) perform (this marks the order paid -> fires payment.success webhook)
{"jsonrpc":"2.0","id":1,"method":"PerformTransaction","params":{"id":"mock_tx_123"}}
```
Sandbox test card (for the card flow): `8600069195406311`, exp `0328`, **OTP `888888`**.

After `PerformTransaction`, verify: order status `is_paid:true`, and your webhook endpoint
received a POST (check `…/webhooks/{id}/events` → `count` increments, `status:"delivered"`).

> **If the sandbox webhook never fires** even though the order is paid: it's almost always a
> relay/config issue **on the aggregator side**, not yours. Prove your side with a direct
> `curl -X POST https://you.example/wlcm/webhook -d '{...}'` (should hit your server). Then
> ask support to check the relay for your webhook id. Your **polling fallback** (next
> section) keeps you working regardless.

---

## 4. Phase C — Production go-live

### 4.1 The production credential bootstrap (the "OAuth method")
Production does **not** reuse sandbox keys. The aggregator emails you an **onboarding
token** + `partner_id`. This token is **NOT** a Bearer token and **NOT** an `X-API-Key`.
It is used **once**, as a **query parameter**, to mint your real API key + secret.
(Docs: `https://docs.wlcm.uz/onboard` → "Onboarding API".)

> Copy the token by **paste, never retype** — `l/I/1` and `0/O` are indistinguishable in
> most fonts and a single wrong char yields `401 Could not validate credentials`.
> The token is also typically **IP-whitelisted** and has limited **uses** — call from your
> whitelisted server and don't waste the POST.

**Step 1 — validate (does not consume a use):**
```
GET https://api.wlcm.uz/api/v1/partners/onboarding/?token=<ONBOARDING_TOKEN>
-> 200 {"status":"ok"}
```
**Step 2 — mint credentials (consumes one use):**
```
POST https://api.wlcm.uz/api/v1/partners/onboarding/?token=<ONBOARDING_TOKEN>
Content-Type: application/json
{"name": "production-key"}
->
{"id": 57, "name": "production-key",
 "api_key": "wlcm_....", "api_secret": "...."}
```
Store `api_key` + `api_secret` in your secret store. From here on, production auth is the
**same HMAC scheme** as sandbox.

### 4.2 Switch config
```
WLCM_BASE_URL=https://api.wlcm.uz
WLCM_API_KEY=wlcm_<prod>
WLCM_API_SECRET=<prod>
```

### 4.3 Re-create the webhook on the production account
```
POST https://api.wlcm.uz/api/v1/partners/me/webhooks
{"url": "https://you.example/wlcm/webhook", "secret_key": "<secret>"}
```

### 4.4 Production verification checklist
- [ ] `GET /api/v1/partners/me` → 200, partner `is_active: true`
- [ ] `GET /api/v1/payments/providers` → providers you need show `is_active: true`
- [ ] `POST /api/v1/integrations/checkout` → returns a **real** `checkout_url`
      (Payme → `checkout.paycom.uz`, Click → `my.click.uz`)
- [ ] `GET /api/v1/orders/{id}/status` → works (drives webhook verify + polling)
- [ ] webhook listed via `GET /api/v1/partners/me/webhooks`
- [ ] **[HUMAN] one real low-value payment** → access granted automatically within seconds
      (webhook) or within your poll interval (fallback)

---

## 5. Recommended architecture (resilient by design)

Run **both** paths; they reconcile through the same status API and are idempotent:

```
                       ┌─────────────────────────────────────────┐
  user pays ──►  WLCM ─┤ (a) webhook  POST /your/webhook  (instant)│
                       │ (b) you poll GET /orders/{id}/status      │──► confirm_payment()
                       └─────────────────────────────────────────┘     (idempotent;
                                                                         grants access once)
```

1. **Webhook receiver** (e.g. aiohttp) behind an **HTTPS reverse proxy** (nginx) with a
   valid cert. On receipt: parse `external_id` → load payment → **verify via order-status
   API** → grant access. Return `200 OK` quickly.
2. **Polling fallback** (cron/scheduler, e.g. every 2 min): for each `pending` payment with
   a stored `wlcm_order_id`, call order-status; if `is_paid`, confirm. Optionally expire
   stale unpaid checkouts (e.g. >30 min) and notify the user to retry.
3. **Idempotency:** `confirm_payment()` must early-return if already confirmed, so webhook
   and poll (or webhook retries) can't double-grant.

**Minimal webhook handler (verify-via-API pattern):**
```python
async def wlcm_webhook(request):
    data = await request.json()
    external_id = data.get("external_id")              # == your payment id
    payment = await get_payment(external_id)
    if not payment:
        return web.Response(text="OK")                 # unknown — ack and ignore
    order_id = payment["wlcm_order_id"] or data.get("order_id")
    if await order_is_paid(order_id):                  # GET /orders/{id}/status -> is_paid
        await confirm_payment(payment["id"])           # idempotent
    return web.Response(text="OK")
```

**Minimal polling fallback:**
```python
async def poll_pending():
    for p in await pending_payments_with_wlcm_order_id():
        if await order_is_paid(p["wlcm_order_id"]):
            await confirm_payment(p["id"])             # idempotent
```

---

## 6. API quick reference

| Action | Method & path | Auth |
|---|---|---|
| Partner info | `GET /api/v1/partners/me` | HMAC |
| Create checkout | `POST /api/v1/integrations/checkout` | HMAC |
| Order status | `GET /api/v1/orders/{order_id}/status` | **none** |
| List/create webhooks | `GET` / `POST /api/v1/partners/me/webhooks` | HMAC |
| Update/delete webhook | `PATCH` / `DELETE /api/v1/partners/me/webhooks/{id}` | HMAC |
| Webhook delivery log | `GET /api/v1/partners/me/webhooks/{id}/events` | HMAC |
| Providers | `GET /api/v1/payments/providers` | HMAC |
| Card OTP confirm | `POST /api/v1/integrations/card/confirm` | HMAC |
| Onboarding validate | `GET /api/v1/partners/onboarding/?token=…` | token (query) |
| Onboarding mint key | `POST /api/v1/partners/onboarding/?token=…` | token (query) |
| Mock pay (sandbox) | `POST /api/v1/webhooks/mock-payme` | none (JSON-RPC) |

Amounts are always in **tiyin** (`som * 100`). `payment_provider`:
`payme | click | paylov | card | uzum` (whichever your account has enabled).

---

## 7. Lessons learned (the things that cost hours)

1. **Production "OAuth token" ≠ a usable API token.** It's an *onboarding* token used at
   `/partners/onboarding/?token=` (query param) to mint the real `api_key`/`api_secret`.
   It fails as Bearer, as `X-API-Key`, and as a refresh token — by design.
2. **Real webhook event is `payment.success`**, regardless of what the UI/docs show and what
   the webhook-create endpoint stores. Don't branch on it — verify via order-status.
3. **Verify, don't trust.** Confirm `is_paid` through the status API before granting value.
   Removes dependence on signature format and protects against spoofed callbacks.
4. **Always ship a polling fallback.** Sandbox (and occasionally prod) relays can silently
   not deliver. Polling the status API guarantees eventual confirmation.
5. **Token transcription:** paste, never retype. `l/I/1`, `0/O` ambiguity → `401`.
6. **IP whitelist** applies to the onboarding token and may apply to the API key — operate
   from the declared server IP.
7. **Set a normal `User-Agent`.** Some edge/bot filters reject default `python-urllib`/`curl`
   UAs from certain hosts.
8. **Sandbox provider reality:** only the mock provider may be configured in sandbox; real
   providers ("Provider is not configured") light up in production per your contract.

---

## 8. For an AI agent executing this

Order of operations, with the human handoffs called out:

1. **[HUMAN]** contract + soliq commissioner + production-credential request letter.
2. **[AGENT]** implement `make_signature` / `signed_headers`; smoke-test `GET /partners/me`
   in **sandbox**.
3. **[AGENT]** implement checkout, store `wlcm_order_id`, implement order-status confirm.
4. **[AGENT]** stand up the webhook endpoint (HTTPS); register it; drive `mock-payme`
   `CreateTransaction`+`PerformTransaction`; assert order paid + webhook delivered + access
   granted. Add the polling fallback and assert it also confirms.
5. **[HUMAN/AGENT]** when the onboarding token arrives: from the **whitelisted server**,
   `GET …/partners/onboarding/?token=` to validate, then `POST` once to mint prod creds.
6. **[AGENT]** switch `WLCM_BASE_URL`/key/secret to production; re-create the prod webhook;
   run the §4.4 checklist.
7. **[HUMAN]** one real low-value payment to confirm live end-to-end.

If any auth call returns `401`: check (a) timestamp unit/skew, (b) exact-bytes body signing,
(c) IP whitelist, (d) correct base URL for the environment, (e) token transcription.
