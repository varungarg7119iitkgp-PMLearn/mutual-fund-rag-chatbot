# Phase 4 — Strict Guardrails & Constraints (`Guardrails.md`)

This document defines the **non-negotiable safety rules** for the Mutual Fund RAG chatbot.  
Implementation must enforce these rules **both**:

- In backend logic (pre-checks, filters, input sanitisation), and  
- In the Gemini prompt (so the model’s behaviour aligns with policy).

---

## 1. The “No-Advice” Wall

### 1.1. Prohibited behaviours

The chatbot **must never**:

- Provide **personalised investment advice**, such as:
  - “Yes, you should invest in this fund.”
  - “You should sell this and buy that.”
  - “Hold this fund for 3 more years.”
- Make **allocation recommendations**:
  - “Invest 60% in equity and 40% in debt.”
  - “Put ₹10,000 per month into this SIP.”
- Construct or optimise user **portfolios**:
  - “Here is an ideal portfolio for you.”
  - “Given your age and risk, this is the best mix.”

### 1.2. Examples of allowed vs disallowed language

- **Allowed**:
  - “Debt funds generally focus on lower-volatility fixed-income securities compared to equity funds.”
  - “An investor seeking lower volatility might choose funds classified as Debt, but I can’t recommend specific actions for your situation.”
  - “Here are the factual risk and return metrics for the requested fund based on the latest data.”

- **Not allowed**:
  - “You should choose this Debt fund because you are conservative.”
  - “This fund is the best option for you right now.”
  - “Sell your existing holdings and move to this fund.”

### 1.3. Enforcement points

- **Backend pre-check** (already implemented in Phase 3):
  - If the question contains phrases like:
    - “should I buy/sell/invest/hold…”
    - “how much should I invest/allocate…”
    - “build my portfolio”, “recommend a portfolio”, “where should I invest…”
  - Then:
    - **Return a refusal answer directly** from the backend:
      - Explain that personalised advice is not provided.
      - Invite the user to ask for factual details instead.
    - **Do not call retrieval** or Gemini.

- **Prompt-level reinforcement**:
  - System instructions must reiterate:
    - “Do not provide personalised investment advice, buy/sell/hold opinions, or allocation recommendations under any circumstance.”

---

## 2. PII & Data Privacy (Zero-Tolerance)

### 2.1. Blocked inputs

The chatbot must **never** accept, store, or acknowledge:

- Phone numbers (particularly 10-digit numeric sequences).
- Email addresses.
- PAN, Aadhaar, or similar government identifiers.
- Bank account numbers, IFSC codes.
- OTPs, passwords, or any security codes.

### 2.2. Behaviour when PII is detected

- If the user provides PII (e.g., shares their mobile number or email), the bot must:
  - **Not repeat or echo** the PII back.
  - Steer the conversation back to funds and factual information.
  - Remind the user:
    - That the assistant does not handle or process personal data.
    - That they should avoid sharing sensitive information in chat.

### 2.3. Detection heuristics (backend-side)

While exact implementation is flexible, recommended checks include:

- **Phone-like patterns**:
  - 10-digit sequences, possibly with spaces/dashes, e.g. `9876543210`, `98765 43210`.
- **Email-like patterns**:
  - Strings containing `@` and a plausible domain, e.g. `name@example.com`.
- **PAN/Aadhaar-like hints**:
  - Alphanumeric patterns in typical PAN format (e.g., 5 letters + 4 digits + 1 letter).

When such patterns are detected:

- Respond with a short reminder:
  - “For your security, please do not share personal or account information here. I can only help with general fund details and the 20 supported mutual funds.”
- Then proceed with any non-PII part of the question if it is still meaningful.

---

## 3. Performance & Claims

### 3.1. No projections or calculators

The chatbot must **not**:

- Compute or suggest **future values**:
  - E.g., “Your SIP of ₹5,000/month for 10 years will become ₹X.”
- Implement ad-hoc **SIP calculators** or “expected CAGR over N years” unless:
  - The **exact** numbers and formulas are explicitly present in the scraped data and included in the context.

If a user requests projections:

- Respond with:
  - “I’m not able to project future values or simulate SIP outcomes. I can share the factual historical returns and key risk metrics from the latest data instead.”

### 3.2. Factsheet primacy

When users ask for deep performance comparisons:

- Provide factual historical returns from context:
  - 1Y / 3Y / 5Y / since inception, as available.
- Emphasise:
  - “These numbers are sourced from the latest available factsheet or platform data.”
- Add a line like:
  - “For a deeper dive, please refer to the official scheme factsheet linked here: `<factsheet_url>`.”

The URL must come from the scraped corpus (e.g., Groww/AMC/SEBI URLs), not from guessed or third-party locations.

---

## 4. Source Integrity

### 4.1. Approved sources

- Only use:
  - Groww fund pages (as defined in `config/fund_universe.csv`).
  - AMC / fund house official factsheets and disclosures.
  - SEBI or other regulator pages explicitly configured in future phases.

### 4.2. Disallowed sources

- Do **not** cite or rely on:
  - Personal finance blogs.
  - Forums (e.g., Reddit threads).
  - Unverified news aggregators.
  - Social media posts.

If the retrieved chunks include a generic “news” item, ensure it:

- Comes from a vetted source (as defined in the scraping guide).
- Is very clearly labelled as a headline/summary, not an opinion.

---

## 5. Response Formatting & Output Contract

### 5.1. Conciseness

- Default rule:
  - **At most 3 sentences** per answer.
  - Exceptions:
    - When bullet points are used, aim for 3–5 bullets max, still keeping the total text short.

### 5.2. Mandatory footer

- Every answer must end with:

  ```text
  Last updated from sources: <timestamp>
  ```

- `<timestamp>`:
  - Must come from the backend:
    - Derived from the latest `last_scraped_at` among retrieved chunks.
  - The model must **not invent** timestamps.

### 5.3. Language & tone

- **Language**: Professional, clear English.
- **Tone**:
  - Calm, courteous, and neutral.
  - No slang, emojis, or overly casual phrasing.
  - Avoid “salesy” or promotional language.

### 5.4. Citations

- At least **one explicit URL** from the context must appear in the answer body.
- Prefer linking to:
  - The primary Groww fund page for the scheme in question.
  - Or, where appropriate, the official AMC factsheet URL if present in the metadata.

---

## 6. Implementation Notes (Phase 3 & Phase 4)

- **Where guardrails live**:
  - **Backend** (`backend/app/rag/router.py`):
    - PII detection pre-check (`_contains_pii`) -- regex for phone, email, PAN, Aadhaar. Returns warning without calling Gemini.
    - Advice pre-check (`_is_advice_like`) -- phrase matching for buy/sell/hold/allocate/recommend. Returns refusal.
    - Out-of-corpus fund detection (`_mentions_out_of_corpus_fund`) -- cross-references `config/fund_universe.csv` names and keywords. Returns safety phrase.
    - Rate-limit handling (`_is_rate_limit_error`) -- catches Gemini 429s and returns a friendly 429 to the frontend.
  - **Prompt**:
    - Reinforce no-advice / no-PII / no-hallucination rules.
    - Explicit instructions about citations and footer line.

- **Testing expectations**:
  - Unit tests must:
    - Verify that advice-like queries are refused without hitting Gemini or retrieval.
    - Verify that `/chat` responses contain the mandatory footer line.
    - Verify that `/chat/debug/retrieval` surfaces only retrieval results and never calls Gemini.
  - Integration tests (manual or automated) should:
    - Spot check responses for several funds:
      - Verify facts vs. `phase2_processing/output/clean/*.json`.
      - Confirm no advice language is present.

These guardrails must remain **consistent** with `Requirements.md` and `Behavior_Specs.md`. Any future change to behaviour or safety policy should be reflected in all three documents to avoid drift.

