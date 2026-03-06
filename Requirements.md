## Mutual Fund RAG Chatbot — Product Requirements

### 1. Executive Summary

This document defines the product requirements for a world‑class, Retrieval‑Augmented Generation (RAG) chatbot and data dashboard focused on a curated set of 20 Mutual Funds. The application acts as a **facts‑only, highly constrained financial FAQ assistant**, helping users understand key characteristics, metrics, and recent developments of supported mutual funds while **strictly avoiding personalized financial advice or recommendations**.

The system ingests structured data from authoritative mutual fund information sources, organizes and embeds this data for retrieval, and uses a large language model to generate concise, clearly cited responses. It includes a consumer‑grade, visually rich UI featuring an interactive chat, fund‑level insights, and a trending funds module powered by anonymized interaction data. This document serves as the single source of truth for product scope, user flows, data needs, UI expectations, and safety/guardrail requirements.

---

### 2. User Personas

#### 2.1 Retail Mutual Fund Explorer
- **Description**: Individual investor with basic to intermediate knowledge of mutual funds, exploring options and seeking to understand specific funds better.
- **Goals**:
  - Quickly understand key facts about a specific mutual fund (returns, risk, fees, etc.).
  - Compare high‑level characteristics of funds within the supported universe (without personalized recommendations).
  - Stay informed about recent news or developments related to a selected fund.
- **Constraints & Behaviors**:
  - May not be comfortable reading long factsheets or regulatory documents.
  - Needs clear visual cues about risk and performance history.
  - Must not be guided toward “what to buy/sell”; only factual information is allowed.

#### 2.2 Curious Finance Learner
- **Description**: Student, early‑career professional, or self‑learner trying to understand mutual fund concepts through concrete examples.
- **Goals**:
  - Ask conceptual questions tied to the supported funds (e.g., “What does the riskometer say for this fund?”).
  - Learn terminology and see it grounded in actual fund data.
- **Constraints & Behaviors**:
  - May ask broad or opinion‑seeking questions that must be redirected to factual explanations.
  - Needs educational content and links without any advisory positioning.

#### 2.3 Product Owner / Admin (Internal)
- **Description**: Internal stakeholder responsible for maintaining the list of 20 funds and overseeing correctness of data.
- **Goals**:
  - Configure and update the curated list of 20 mutual funds and their source URLs.
  - Ensure that scraped data is up‑to‑date and correctly reflected in the chatbot responses.
  - Monitor usage patterns (e.g., which funds are queried most often) while preserving user anonymity.
- **Constraints & Behaviors**:
  - Requires high confidence that the system does not drift into advice or hallucination.
  - Needs basic observability into data freshness and scrape status.

---

### 3. Core Features

#### 3.1 Mutual Fund Data Corpus Management
- **Curated Fund Universe**:
  - Exactly **20 mutual funds** supported at any time, defined in a structured configuration file (e.g., `config/fund_universe.csv`) that can be updated by internal stakeholders.
  - Organized into **4 categories**:
    - 5 Debt funds.
    - 5 Commodities funds.
    - 5 Hybrid funds.
    - 5 Equity funds.
  - The initial fund universe comprises:
    - **Commodity funds**:
      - HDFC Silver ETF FoF Direct Growth.
      - Axis Silver FoF Direct Growth.
      - ICICI Prudential Silver ETF FoF Direct Growth.
      - Nippon India Silver ETF FoF Direct Growth.
      - Aditya Birla Sun Life Silver ETF FoF Direct Growth.
    - **Debt funds**:
      - DSP Credit Risk Fund Direct Plan Growth.
      - HDFC Income Plus Arbitrage Active FoF Direct Growth.
      - Aditya Birla Sun Life Credit Risk Fund Direct Growth.
      - HSBC Credit Risk Fund Direct Growth.
      - Aditya Birla Sun Life Medium Term Plan Direct Growth.
    - **Hybrid funds**:
      - SBI Magnum Children's Benefit Fund Investment Plan Direct Growth.
      - Quant Multi Asset Allocation Fund Direct Growth.
      - ICICI Prudential Retirement Fund Hybrid Aggressive Plan Direct Growth.
      - Nippon India Multi Asset Allocation Fund Direct Growth.
      - HDFC Hybrid Equity Fund Direct Growth.
    - **Equity funds**:
      - Motilal Oswal BSE Enhanced Value Index Fund Direct Growth.
      - SBI PSU Direct Plan Growth.
      - Invesco India PSU Equity Fund Direct Growth.
      - Aditya Birla Sun Life PSU Equity Fund Direct Growth.
      - ICICI Prudential PSU Equity Fund Direct Growth.
  - Each fund has:
    - A canonical name (as listed in the configuration file).
    - A category (Commodity, Debt, Hybrid, or Equity).
    - One or more platform or factsheet URLs (e.g., Groww, AMC factsheet, SEBI disclosure page, trusted aggregator).
    - A set of **keywords/aliases** capturing common ways users may refer to the fund (e.g., “HDFC Silver”, “Silver ETF”), to assist in mapping natural language queries to the correct fund.
  - Product Owner must be able to update the configuration file to add/remove funds or adjust keywords (subject to maintaining the 20‑fund limit for this version).

- **Data Ingestion & Scraping**:
  - System periodically retrieves data from the configured URLs for each fund.
  - Scraping focuses on specific, predefined metrics (see Data Requirements).
  - Scraper must handle:
    - Static HTML pages.
    - Dynamic content that appears after user interaction or loading delays.
    - Minor structural changes (e.g., extra sections) without breaking core extraction.
  - Scraping failures for any fund must be logged and surfaced through an internal status view or report.

- **Scheduled Refresh**:
  - There is a scheduled process that re‑fetches and updates fund data at a defined frequency (e.g., once per day at a configurable time).
  - Manual re‑ingestion trigger must be possible for internal stakeholders (e.g., via an internal endpoint or admin action).
  - The chatbot must display the **effective last update timestamp** in user‑visible responses.

#### 3.2 Interactive Chat Experience
- **Free‑form Question Input**:
  - Users can type natural language questions about the 20 supported mutual funds.
  - Input box supports:
    - Multi‑line questions.
    - Editing before submission.
  - Optional quick‑action example prompts exposed on the welcome screen.

- **RAG‑Backed Responses**:
  - Each user query triggers:
    - Retrieval of relevant data chunks linked to one or more of the 20 funds.
    - Generation of a concise, well‑formatted answer grounded exclusively in retrieved chunks.
  - Responses must:
    - Be limited to scope of supported funds.
    - Include at least one clickable citation per answer.
    - End with a “Last updated from sources: [Date/Time]” line.

- **Conversation History (Session‑Level)**:
  - Within a user session, previous questions and answers remain visible in the chat window.
  - The system may use recent conversation context to disambiguate follow‑up questions but **must still rely exclusively on retrieved, grounded data** for factual content.
  - No persistent, user‑identified history is stored; only anonymized logs are kept for analytics.

#### 3.3 Trending / Popular Funds Module
- **Trending Calculation**:
  - The system maintains counts of how many times each of the 20 funds is mentioned or requested within a configurable rolling time window.
  - Counts must be based solely on **anonymized query logs**, with no tie to user identities.

- **UI Presentation**:
  - A dedicated UI widget displays:
    - Top N (e.g., 3–5) most frequently queried funds.
    - Basic metrics or tags for each trending fund (e.g., category, high‑level risk label).
  - Optional interaction:
    - Clicking a trending fund can pre‑fill a recommended query or open a brief fund fact summary in the chat.

#### 3.4 Marquee Ticker
- **Fund Ticker Strip**:
  - A horizontally scrolling ticker displays the 20 supported funds.
  - For each fund, ticker shows:
    - Fund short name.
    - Latest NAV or recent change indicator.
    - Directional movement (e.g., up/down arrow).
  - Ticker reflects the **most recently scraped data**.
  - Hover or click interactions may reveal a compact tooltip with key metrics (e.g., category, riskometer level).

#### 3.5 Welcome & Onboarding Experience
- **Welcome Screen Content**:
  - Prominent, unambiguous disclaimer text:
    - “**Facts‑only. No investment advice.**”
  - Brief explanation of what the chatbot can and cannot do, including:
    - “Can explain metrics and historical data for the 20 supported mutual funds.”
    - “Cannot tell you what to buy or sell.”

- **Example Queries**:
  - At least 3 clickable example prompts such as:
    - “Show key stats for [Example Equity Fund].”
    - “What is the expense ratio and exit load for [Example Debt Fund]?”
    - “What does the riskometer say for [Example Hybrid Fund]?”
  - Clicking an example query auto‑fills and sends the question into the chat interface.

#### 3.6 Scope Restriction & Fund Selection
- **Fund Scope Enforcement**:
  - If a user asks about a fund that is not within the curated 20:
    - The chatbot must clearly state that it only supports the configured funds.
    - Optionally, the UI can suggest picking from the list or provide a searchable dropdown of supported funds.
  - For general or vague questions:
    - The bot should request clarification referencing specific funds or categories within the supported set.

---

### 4. Data Requirements

#### 4.1 Data Sources
- **Primary Sources**:
  - Mutual fund aggregator or platform pages (e.g., fund profile pages).
  - Official AMC factsheets and regulatory disclosures.
  - SEBI or other regulatory data pages when available.

- **News Sources**:
  - Financial news or market information sites where headlines and URLs can be scraped or ingested.
  - Only reputable sources are to be used (to be defined during configuration).

- **Configuration**:
  - Each fund configuration records:
    - Fund name and short code.
    - Category (Debt, Commodities, Hybrid, Equity).
    - Primary details URL (canonical data source).
    - Optional secondary/backup data URLs.
    - News source URLs or search patterns.
  - The specific fields to be scraped from these sources are defined in the **Mutual Fund Scraping Reference Guide** (`config/scraping_reference_guide.md`), which must be treated as the authoritative checklist for scraping and data mapping.

#### 4.2 Data Fields per Fund
For each of the 20 funds, the system must capture and maintain at minimum:

- **Identity & Classification**:
  - Fund name.
  - Category (Debt / Commodities / Hybrid / Equity).
  - AMC name.
  - Benchmark index name (if available).
  - A list of fund **keywords/aliases** as configured (e.g., “HDFC Silver, Silver ETF, Silver FoF, Commodity fund, silver price investment”) to aid in entity recognition in user queries.

- **NAV & Price Metrics**:
  - Latest NAV.
  - NAV date.
  - 52‑week high NAV and date.
  - 52‑week low NAV and date.

- **Performance / Returns**:
  - Point‑to‑point or annualized returns for:
    - 1‑year.
    - 3‑year.
    - 5‑year.
  - Corresponding benchmark returns for the same periods (if available).
  - Time periods and calculation basis must be recorded to avoid misinterpretation.

- **Costs & Loads**:
  - Expense ratio (regular plan; direct plan if available, clearly labeled).
  - Exit load structure (e.g., % and applicable holding periods).
  - Any other recurring or one‑time fees clearly described in the source.

- **Investment Minimums**:
  - Minimum SIP amount.
  - Minimum lump‑sum amount (if available).

- **Risk & Compliance Indicators**:
  - Riskometer level (e.g., Low, Moderately High, High, etc.).
  - Category‑specific risk labels or warnings as stated in the source documents.

- **News & Headlines**:
  - A recent list of news items (configurable count per fund, e.g., last 3–5 items), each with:
    - Headline text.
    - Publisher/source name.
    - Publication date.
    - Short summary snippet or lead paragraph where available.
    - Clickable URL.
  - News and updates should align with the “In the News / Updates” expectations defined in `config/scraping_reference_guide.md`, so that the bot can answer “why” questions (e.g., reasons for recent moves) using contextual snippets, not just restated NAV changes.

- **Metadata**:
  - Source URLs for each data field (or field group).
  - Last successful scrape timestamp.
  - Versioning or snapshot ID to track changes over time (internal use).

#### 4.3 Data Structuring for RAG
- **Chunking Strategy**:
  - Data must be segmented into semantically meaningful chunks that can be embedded and retrieved effectively, such as:
    - Fund overview summary.
    - Performance section.
    - Fees and loads section.
    - Risk and riskometer section.
    - News snapshot section.
  - Each chunk must contain:
    - Human‑readable text summary.
    - Structured backing fields (for display and validation).
    - One or more source URLs for citation.

- **Retrieval Metadata**:
  - Each chunk is tagged with:
    - Fund identifier.
    - Fund category.
    - Data type (e.g., “performance_1Y_3Y_5Y”, “riskometer”, “exit_loads”, “news”).
    - Timestamp of last data refresh.

- **Updatability**:
  - When new data is scraped:
    - Old chunks must be replaced or invalidated.
    - Newly generated chunks are embedded/vectorized and indexed.
  - There must be a clear mechanism to avoid mixing old and new snapshots in a single response.

---

### 5. UI / UX Requirements

The high‑level UI and UX expectations for the product are defined in this section. A more detailed visual and interaction specification is maintained in `ui-references/UI_UX_Specs.md`; any design or implementation decisions for the frontend should be consistent with both this master requirements document and that companion spec.

#### 5.1 Overall Look & Feel
- **Visual Theme**:
  - Modern, dark‑mode first design (“Midnight” theme) suitable for financial analytics.
  - High contrast for text and important metrics.
  - Use of accent colors to highlight risk levels, performance, and call‑to‑action elements, with a primary “growth green” accent for positive movement.
  - Overall visual tone is premium, calm, and high‑trust, inspired by institutional‑grade finance tools and modern neo‑bank interfaces.
  - Where an AI avatar or brand mark for the assistant is shown, it may incorporate subtle Gemini‑inspired accent colors while remaining consistent with the WealthAI brand and dark theme.

- **Layout Principles**:
  - Centered chat experience with supporting panels for:
    - Trending funds.
    - Quick fund selection/search.
    - Key metrics or highlights.
  - Persistent top or bottom area for disclaimers and the ticker.

#### 5.2 Welcome Screen
- **Content Elements**:
  - Prominent title and short description of the assistant’s purpose.
  - “Facts‑only. No investment advice.” displayed clearly and persistently.
  - Three or more sample queries as clickable chips/buttons.
  - Brief one‑sentence description of the supported fund universe (20 curated funds across 4 categories).

#### 5.3 Chat Interface
- **Input Area**:
  - Text area with placeholder text guiding the user toward fund‑specific questions.
  - Send button plus keyboard shortcut for submission.
  - Optional small note reminding users not to input personal information.

- **Message Display**:
  - Clear differentiation between user messages and bot responses.
  - Bot responses must visibly:
    - Present the main answer text.
    - Show citations as clickable links (e.g., under the answer or inline).
    - Include the timestamp line “Last updated from sources: [Date/Time]”.
    - Display a small “Verified” shield or checkmark icon next to the assistant name to signal that answers are grounded in the curated corpus and linked to verified sources.
  - Long answers should be visually broken into paragraphs or bullet lists where appropriate, maintaining the ≤3‑sentence guideline wherever possible.

- **Error & Refusal States**:
  - For unsupported questions (advice‑seeking, off‑universe funds, speculative projections), responses must:
    - Politely decline.
    - Reiterate scope limitations.
    - Optionally link to an educational resource or regulatory guideline.

#### 5.4 Marquee Ticker & Fund Discovery
- **Ticker Behavior**:
  - Runs continuously on desktop widths at a deliberate, newsroom‑style speed so that each fund item can be comfortably read in one pass.
  - Behaves gracefully on smaller screens (e.g., collapsible or swipeable).
  - Each fund entry clickable to:
    - Trigger a quick summary in the chat, or
    - Open a side panel with snapshot metrics.

- **Fund Search / Selection**:
  - A control (e.g., dropdown or search box) to quickly filter and select one of the 20 funds by name.
  - Selecting a fund can auto‑generate a default informational query in the chat.

#### 5.5 Trending / Popular Funds Module
- **User‑Facing Behavior**:
  - Displays a small list of most queried funds.
  - Shows an indicator of change (e.g., rising, stable) based on recent activity.
  - Clicking a fund behaves similarly to ticker interactions (e.g., quick summary or query prefill).

#### 5.6 Responsiveness & Accessibility
- **Device Support**:
  - UI must be usable on desktop, tablet, and mobile browser form factors.

- **Accessibility Basics**:
  - Sufficient color contrast for text and key interactive elements.
  - Clear focus states and keyboard navigability for critical actions (chat input, send button, fund selection).
  - Clear, non‑ambiguous language in disclaimers and guidance messages.

---

### 6. LLM, Response Behavior, and RAG Requirements

#### 6.1 LLM Usage Principles
- **Primary Role**:
  - Transform retrieved, factual data chunks into concise, coherent, and user‑friendly answers.
  - Provide explanations of metrics and terms using only information derived from the corpus or safely general financial definitions that do not imply advice.

- **Current Implementation Choice (Phases 3–4)**:
  - The initial implementation of the LLM layer uses:
    - The **Google GenAI SDK** (`google-genai`) to communicate with Gemini.
    - The **`gemini-3-flash-preview`** model for answer generation.
    - A **local TF/IDF-style index** over Phase 2 chunks (stored under `backend/rag_index/`) as the retrieval mechanism, instead of an external vector database for this version.
  - Higher-level RAG and LLM principles in this document remain valid even if the underlying model or vector store is swapped in a future phase.

- **Strict Grounding**:
  - All factual statements about funds (returns, risk, fees, minimums, etc.) must derive from the ingested and indexed data.
  - The model must not fabricate:
    - Fund metrics not present in the corpus.
    - Projections or forecasts of future performance.
    - Rankings beyond what’s explicitly encoded in the data.

#### 6.2 Answer Formatting
- **Conciseness**:
  - Default answer length: ideally ≤3 sentences, unless explicitly asked for more detail.
  - Use bullet points sparingly for clarity (e.g., listing returns for multiple periods).

- **Citations**:
  - Every response must include:
    - At least one clickable citation pointing to a relevant authoritative page (e.g., factsheet, regulator page, or fund profile).
    - Additional citations when referencing multiple data points from distinct sources.
  - Citation placements:
    - Either inline (e.g., “as per [AMC factsheet]”) or as a separate “Sources” section beneath the answer.

- **Timestamp Requirement**:
  - Each answer must conclude with:
    - “Last updated from sources: [Date/Time]”.
  - The timestamp corresponds to the **most recent successful data refresh** for any data used in the answer.

#### 6.3 Behavior on Out‑of‑Scope Queries
- **Personal Advice**:
  - For queries like:
    - “Should I invest in this fund?”
    - “Which is better for me between Fund A and Fund B?”
    - “How much should I allocate?”
  - The bot must:
    - Clearly state that it cannot provide investment advice or personalized recommendations.
    - Optionally:
      - Offer to show factual metrics for the funds mentioned.
      - Provide links to neutral educational resources on how to evaluate funds.

- **Unsupported Instruments or Funds**:
  - For instruments outside the 20‑fund universe or unrelated products:
    - The bot must clarify its restricted coverage.
    - Suggest focusing on the supported funds or topics within stated scope.

- **Speculative Forecasts or Projections**:
  - For questions about future performance (e.g., “What will the NAV be next year?”):
    - Bot must decline to predict.
    - May restate historical returns and risk factors for context, labeled clearly as historical data only.

---

### 7. Non‑Functional Requirements (Security, Guardrails, Performance)

#### 7.1 Security & Privacy
- **No PII Collection**:
  - The system must not:
    - Prompt users for personal identifiers (PAN, Aadhaar, account numbers, email, phone, OTPs, etc.).
    - Accept or store PII when it is incidentally provided; instead:
      - Display a warning message and instruct the user not to share such information.
  - Input validation and filtering should minimize storage of any accidentally shared PII in logs.

- **Anonymized Tracking**:
  - Interaction logs must:
    - Record query text, timestamps, and derived fund references.
    - Not contain any stable, real‑world user identifier (no login IDs, IPs in the analytics store, etc., unless required for infrastructure security and stored separately).
  - Data used for the Trending module must be fully anonymized and aggregated.

- **Behavior & Guardrail Specifications (Phase 4)**:
  - Detailed behavior and guardrail definitions for the chatbot are maintained in:
    - `phase4/Behavior_Specs.md` — role, persona, RAG-first behavior, and prompt orchestration.
    - `phase4/Guardrails.md` — strict no-advice wall, PII handling, performance/claims limits, source integrity, and output contract.
  - Any changes to chatbot behavior or safety policy must be reflected in both this master document and the Phase 4 specs to avoid drift.

#### 7.2 Guardrails & Compliance
- **Advice Prohibition**:
  - The system must consistently:
    - Reject any attempt to elicit personalized financial advice.
    - Avoid language that could be interpreted as a recommendation (“You should…”, “This is best for you…”).
  - Pre‑defined refusal templates should:
    - Reiterate that the tool is informational only.
    - Encourage consulting a registered financial advisor for personal advice.

- **Fact‑Only Policy**:
  - No fabrication of performance metrics or risk indicators.
  - No generation of forward‑looking return estimates, price targets, or guarantees.
  - If data is missing or stale:
    - The system must acknowledge this explicitly.
    - Optionally suggest checking the official AMC website directly.

- **Content Safety**:
  - The assistant must avoid:
    - Promoting illegal activity or fraudulent schemes.
    - Making derogatory or discriminatory statements.
  - If prompted for non‑financial, harmful, or irrelevant content, the assistant must decline and guide the user back to the mutual fund information scope.

#### 7.3 Reliability & Performance
- **Availability**:
  - The chatbot UI must degrade gracefully if:
    - Scraping fails for some or all funds.
    - The retrieval or generation process is temporarily unavailable.
  - In such cases:
    - The system should show clear, user‑friendly error states.
    - Provide partial data where safe (e.g., last known snapshot) while flagging its potential staleness.

- **Latency Targets**:
  - Typical end‑to‑end response time (from user send to answer display) should be within a user‑acceptable range for an interactive chatbot, with loading indicators to set expectations.

- **Scalability Goal (Initial)**:
  - The system must comfortably handle **at least 1,000 unique users per month**, with peak‑hour concurrency appropriate for this scale.
  - Design and logging decisions should not preclude future scaling to higher traffic.

#### 7.4 Observability & Monitoring
- **Operational Metrics**:
  - Scrape job success/failure counts per fund.
  - Last successful scrape timestamp per fund.
  - Volume of queries per time window.
  - Error rates and timeouts for user requests.

- **Quality Monitoring**:
  - Internal review tools or reports that:
    - Sample recent answers with their retrieved chunks and citations.
    - Allow manual verification of factual accuracy.

---

### 8. Out‑of‑Scope (for Initial Release)

- Personalized portfolios, risk profiling, or suitability assessments.
- Support for funds beyond the curated set of 20.
- Direct transaction or order‑placement capabilities.
- User accounts, authentication, or persistent identity‑based profiles.
- Multi‑language support beyond the primary launch language.

---

### 9. Future Enhancements (Non‑binding)

These items are not part of the initial requirements but may be considered later:

- Support for additional funds or categories beyond the initial 20.
- Side‑by‑side comparison views for multiple supported funds.
- More sophisticated analytics panels (e.g., rolling return charts, drawdown visualizations) still presented as historical facts.
- Multi‑language interface and localized explanations of investment concepts.

