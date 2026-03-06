## Mutual Fund Scraping Reference Guide

This guide defines the **canonical set of fields** that must be extracted for each mutual fund from its configured source URLs. It exists to:

- Provide a **clear checklist** for what to scrape from each page.
- Keep the scraping logic **modular and extensible** as new fields or funds are added.
- Ensure the RAG system has consistent, rich, and comparable data across all funds.

The fields below are organized into logical categories. For each field, the table describes:

- **Field Name**: What the field is called in our internal model.
- **Description / Likely Location**: How/where it usually appears on fact sheets or platforms like Groww/AMCs.
- **Why It Matters for the RAG Bot**: How the chatbot is expected to use this data.

---

### 1. Identity & Core Metadata

| Category | Field Name                | Description / Likely Location on Page                                                       | Why It's Critical for the RAG Bot                                                                                   |
|----------|---------------------------|---------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| Identity | Scheme Name & Plan        | Full scheme name including plan and option (e.g., “Direct Growth”, “Regular IDCW”)         | Prevents confusion between similar plans (e.g., Direct vs Regular, Growth vs IDCW) when answering user questions.  |
| Identity | ISIN Code                 | Found in “Fund Overview”, “Key Details”, or “Scheme Details” sections                       | Acts as a unique identifier to link with external market data or news APIs and to disambiguate similarly named funds. |

---

### 2. Performance & Benchmarking

| Category     | Field Name                | Description / Likely Location on Page                                                       | Why It's Critical for the RAG Bot                                                                                         |
|--------------|---------------------------|---------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| Performance  | NAV (Latest)             | Latest Net Asset Value and its effective date; typically near the top of the page          | Directly answers “What is the price today?” and powers ticker and snapshot displays.                                     |
| Performance  | Returns (1Y, 3Y, 5Y, SI) | Annualized and/or absolute returns over 1, 3, 5 years and since inception                  | Enables answers about historical performance and allows relative comparisons across funds over different horizons.       |
| Performance  | Benchmark Returns        | Corresponding benchmark index returns for the same periods                                  | Supports questions like “Is this fund beating the market?” by comparing fund vs benchmark performance.                   |
| Performance  | Category Average         | Average returns of similar funds in the same category                                       | Provides context such as “This fund outperformed its category average by X%,” without making recommendations.            |

---

### 3. Risk Metrics

| Category | Field Name      | Description / Likely Location on Page                                                        | Why It's Critical for the RAG Bot                                                                                          |
|----------|-----------------|----------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| Risk     | Risk-o-meter    | Visual or textual scale (e.g., Low, Moderate, Moderately High, High, Very High)            | Allows precise answers to “How risky is this fund?” using standardized, regulator-defined language.                       |
| Risk     | Standard Deviation | Volatility measure often shown in “Risk Measures” or “Statistics” tables                | Helps explain how much the fund’s returns fluctuate over time.                                                            |
| Risk     | Sharpe Ratio    | Risk-adjusted return metric in “Risk Measures” section                                      | Enables more advanced users to understand whether the returns justify the level of risk taken.                            |
| Risk     | Alpha & Beta    | Alpha (excess return) and Beta (sensitivity to market/benchmark) values                     | Supports expert-level comparisons like “Is this fund more volatile than its benchmark?” without giving advice.           |

---

### 4. Portfolio Composition

| Category  | Field Name          | Description / Likely Location on Page                                                     | Why It's Critical for the RAG Bot                                                                                      |
|-----------|---------------------|-------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------|
| Portfolio | Asset Allocation %  | Percentage breakdown across Equity, Debt, Cash, and other asset classes                  | Answers “Where is my money being invested?” and provides high-level allocation insight.                               |
| Portfolio | Top 10 Holdings     | Table listing top holdings with their weights (%)                                        | Allows the bot to answer “Does this fund have exposure to Reliance or HDFC?” and similar exposure-related questions.  |
| Portfolio | Sector Allocation   | Allocation by sector (e.g., Financials, IT, Energy)                                      | Enables responses like “How concentrated is this fund in IT?” while remaining factual and non-advisory.              |
| Portfolio | Turnover Ratio      | Turnover ratio or portfolio churn percentage, often in “Fund Facts” or “Key Metrics”     | Helps explain whether the strategy is relatively active or passive in factual terms.                                  |

---

### 5. Operational & Investor-Facing Terms

| Category    | Field Name      | Description / Likely Location on Page                                                  | Why It's Critical for the RAG Bot                                                                                               |
|-------------|-----------------|----------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| Operational | Expense Ratio   | Total expense ratio for the specific plan (Direct/Regular)                             | Powers high-value questions like “Which of these funds has the lowest cost?” without recommending any specific fund.        |
| Operational | Exit Load       | Exit load structure (percentage and applicable holding periods)                       | Essential for answers such as “When can I withdraw without paying a penalty?”                                                 |
| Operational | Min Investment  | Minimum SIP amount and minimum lump-sum amount                                         | Answers “Can I start with ₹X?” in factual terms based on the fund documentation.                                              |
| Operational | Taxation Info   | Notes on STCG/LTCG rules specific to the fund category                                 | Enables factual explanations of tax treatment for equity, debt, and hybrid funds, without computing personalized tax advice. |

---

### 6. People & Management

| Category | Field Name            | Description / Likely Location on Page                                             | Why It's Critical for the RAG Bot                                                                                       |
|----------|-----------------------|-----------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| People   | Fund Manager Bio      | Name, experience, tenure, and brief profile, typically under “Fund Manager”      | Builds trust by answering “Who is managing this fund?” with concise, factual information.                              |
| People   | Other Funds Managed   | List or links to other schemes managed by the same fund manager                   | Enables discovery-style queries such as “What other funds does this manager run?” without ranking or recommending.     |

---

### 7. Market Intelligence & News

| Category            | Field Name         | Description / Likely Location on Page                                               | Why It's Critical for the RAG Bot                                                                                               |
|---------------------|--------------------|-------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| Market Intelligence | In the News / Updates | Recent news items, AMC announcements, or market updates referencing the scheme. Each item should capture **headline, publication date, summary snippet (if available), and URL** | Provides context-aware responses when there are notable changes (e.g., manager change, strategy update, sudden performance), allowing the bot to answer “why” questions, not just “what changed.” |

In practice, the **News / Updates** scraping should:

- Avoid scraping only bare headlines; wherever possible, capture:
  - Headline.
  - Publication date.
  - Short summary snippet or lead paragraph.
  - Publisher/source name.
  - URL.
- Focus on news that materially affects:
  - Market sentiment.
  - Regulatory changes.
  - Fund‑specific events (manager change, strategy shift, merger, etc.).

This richer context allows the retriever to support questions like:

- “Why did this fund drop last week?”
- “What recent events affected this category of funds?”

by pulling in **news snippets that describe the underlying cause**, instead of only reporting that “NAV is down X%”.

---

### 8. Recommended Structured Representation (Conceptual)

To keep the system scalable and RAG‑friendly, each fund’s scraped data should be representable as a **nested, self‑contained object** (e.g., a JSON document) that groups identity, metrics, risk, portfolio, operations, people, and news together.

For sources like Groww, a large portion of this structure can be populated directly from their embedded structured data (for example, the `__NEXT_DATA__` JSON block which contains `mfServerSideData`). Conceptually, the mapping for a Groww page should look like:

- **Identity**
  - `fund_id` → `mfServerSideData.isin`
  - `name` → `mfServerSideData.scheme_name`
  - `category` → `mfServerSideData.category` (plus `sub_category` where relevant)
  - `amc_name` → `mfServerSideData.fund_house` or `mfServerSideData.amc_info.name`
  - `benchmark_name` → `mfServerSideData.benchmark_name` or `mfServerSideData.benchmark`

- **Metrics**
  - NAV value → `mfServerSideData.nav`
  - NAV date → `mfServerSideData.nav_date`
  - Fund returns (1Y, 3Y, 5Y, since inception) → element in `mfServerSideData.stats` with `type == "FUND_RETURN"` (`stat_1y`, `stat_3y`, `stat_5y`, `stat_all`).
  - Category average returns → element in `mfServerSideData.stats` with `type == "CATEGORY_AVG_RETURN"` (`stat_1y`, `stat_3y`, `stat_5y`).

- **Risk**
  - Riskometer / overall risk label → `mfServerSideData.return_stats[0].risk` (e.g., “Moderately High”).
  - Standard deviation, Sharpe, Alpha, Beta → `mfServerSideData.return_stats[0].standard_deviation`, `.sharpe_ratio`, `.alpha`, `.beta`.

- **Portfolio**
  - Top holdings → `mfServerSideData.holdings` (e.g., `company_name`, `corpus_per`, `sector_name`, `instrument_name`).
  - Asset allocation and sector allocation can be derived from the holdings or any dedicated allocation fields if present.
  - Turnover ratio → `mfServerSideData.portfolio_turnover`.

- **Operations**
  - Expense ratio → `mfServerSideData.expense_ratio` (e.g., `"0.79"`).
  - Exit load → `mfServerSideData.exit_load` (human‑readable description).
  - Minimum SIP amount → `mfServerSideData.min_sip_investment`.
  - Minimum lumpsum amount → `mfServerSideData.min_investment_amount`.
  - Taxation info → `mfServerSideData.category_info.tax_impact` or equivalent field describing tax treatment.

- **People**
  - Fund manager(s) → `mfServerSideData.fund_manager_details`:
    - Name → `person_name`.
    - Tenure start → `date_from` (used to derive tenure in years if needed).
    - Experience summary → `experience`.
    - Other funds managed → names from `funds_managed[*].scheme_name`.

- **News / Context**
  - If available from the source (e.g., `mfServerSideData.fund_news`), each item should map to:
    - `headline`
    - `date`
    - `summary` or snippet
    - `publisher` / `source`
    - `url`
  - Where the platform does not expose news in structured form, the generic HTML news scraping guidance (above) still applies.

Regardless of source, the resulting per‑fund object consumed by downstream systems should follow a common conceptual schema (field names like `identity`, `nav`, `returns`, `risk`, `portfolio`, `operations`, `fund_manager`, `news_context`, `last_scraped_at`), even if some fields originate from JSON APIs and others from HTML tables.

---

### 9. Extensibility & Governance

- This guide should be **kept in sync** with the system’s data model and RAG schema.
- When adding a new data field:
  - Update this document with the new field name, description, and rationale.
  - Ensure the scraping layer, storage, and retrieval logic are extended accordingly (in later implementation phases).
- When adding new funds:
  - Confirm that the same field set is practically obtainable from their sources.
  - Note any fields that are consistently missing so the bot can transparently communicate limitations to users.

