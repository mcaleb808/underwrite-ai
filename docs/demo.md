# Five-minute demo script

The point of this script is to make every second land. Five minutes is roughly 600-700 spoken words; you can't waste any of them. The structure: a 20-second hook, a two-and-a-half-minute live walkthrough of one applicant going through the pipeline, ninety seconds on what makes it production-shaped (not a prototype), and a 30-second close.

If anything goes wrong with the live demo, the fallback is the recorded video and the screenshots in [`docs/screenshots/`](screenshots/). Switch to those without apologising — the audience won't know.

---

## Pre-demo setup (do this 5 minutes before)

- [ ] `make api` and `make web` are both running (verify `curl http://localhost:8000/api/v1/health` returns `ok`).
- [ ] Browser at `http://localhost:3000`, **light theme**, dev tools closed, browser zoom 100%.
- [ ] On the home page: click **Clear finished** so recent decisions are tidy. Leave one nice approved case visible if you want a "look how this normally lands" moment.
- [ ] Open `docs/screenshots/` in a second tab as the fallback.
- [ ] Open `docs/architecture.md` in a third tab — for the architecture diagram you'll show during the engineering segment.
- [ ] Speaker notes (this file) on a phone or second screen.
- [ ] Close every other tab. Mute notifications. Start a stopwatch when you begin.

---

## The script

### `[0:00 – 0:20]` Hook *(20s)*

**Show:** Slide 1 — title slide.

**Say:**

> A senior underwriter in Rwanda spends about 30 minutes on a typical health-insurance case: reading the medical PDFs, scoring risk against the underwriting manual, looking up the relevant rules, and writing the customer email. UnderwriteAI does that in 30 seconds — and shows you every step the AI took. Let me run a real case.

---

### `[0:20 – 0:50]` Home page tour *(30s)*

**Show:** `http://localhost:3000`.

**Do:** Stay on the home page.

**Point at, in order:**

1. The five seed applicants — *"covering the full risk spectrum, from a clean 29-year-old to a 66-year-old with cardiac history"*.
2. The status tabs (`Running` / `Awaiting review` / `Approved` / `Failed`) — *"every case is queryable by state"*.
3. The recent-decisions table.

**Say:**

> I'll run Jean — 44 years old, controlled hypertension. The most realistic case. Here's the start state — three previous decisions, no active runs.

**Do:** Click Jean's `Run →` button.

---

### `[0:50 – 2:20]` The pipeline runs *(90s — this is the main attraction)*

The pipeline takes ~25 seconds. You have ~65 seconds of narration to fill while it runs.

**Show:** The case detail page, mid-run. Pipeline strip animates left-to-right.

**Narrate, paced to land each step as it completes on screen:**

> Five agents in a fixed order. First: **doc_parser** — a fast model reads the medical PDF and pulls structured facts. It's told to copy verbatim and never invent.
>
> Then in parallel: **risk_assessor** — pure Python, no AI. The score is deterministic and reproducible. Run the same applicant twice, get the same number twice.
>
> And **guidelines_rag** — semantic search over the underwriting manual, plus four pinned foundational rules so the drafter never accidentally ignores them.
>
> The drafter writes the decision: a strong model with a schema-validated output. The verdict has to be one of four values. Citations have to be a list. Garbage out is structurally impossible.
>
> Last step: the **critic**. Adversarial review with five concrete failure modes — verdict mismatch, bias terms, uncited rules, loading caps, conditions without evidence. The LLM critic is paired with a regex backstop that scans for protected terms — Ubudehe, CBHI, district. The LLM may miss bias; the regex cannot.

**When the decision card appears, do:** point at, in order:

- the verdict chip (`Approved with conditions`);
- the loading (`+25.0%`) and the three conditions;
- the reasoning paragraph;
- the citation chips at the bottom (`UW-030 · UW-020 · UW-080 · UW-120 · UW-130`).

**Say:**

> Every percentage points back to a specific rule. The reasoning cites UW-130 for the score-to-verdict mapping, UW-030 for hypertension loading, UW-020 for BMI. No invented numbers, no hallucinated rules.

---

### `[2:20 – 3:00]` Human in the loop *(40s)*

**Do:** Click `Modify`.

**Show:** Inline edit form (verdict dropdown, loading number, conditions textarea, reasoning textarea).

**Say:**

> If the underwriter wants to override anything — the verdict, the loading, the conditions, the reasoning — they edit inline. The AI is a draft, not a decision. This is the human-in-the-loop seam.

**Do:** Click `Cancel`. Then click `Approve & notify applicant`.

**Show:** Email receipt appears.

**Say:**

> The customer email is composed by a separate fast model with a tight prompt: never leak rule IDs, never use the raw verdict enum, never name a percentage. If the LLM call fails, a deterministic template fires — a failed approve never ships an empty email.

**Do:** Point at the `Delivered · message-id` line.

---

### `[3:00 – 4:30]` What makes this production-shaped *(90s — three pillars, ~30s each)*

**Show:** Slide 2 — architecture diagram (or share the Mermaid system view from `docs/architecture.md`).

#### Pillar 1: deterministic guard rails *(30s)*

> The LLM is the assistant, not the judge. Risk scoring is pure Python — auditable, reproducible, immune to model variance. The critic's LLM is paired with a regex backstop that scans for protected terms regardless of what the LLM concludes. The revision loop is hard-capped at one revision so a stubborn argument can't run forever. Every adverse path has a deterministic check the LLM cannot override.

#### Pillar 2: honest evaluation *(30s)*

> We have five golden cases that exercise the full verdict spectrum. Each one asserts verdict bounds, loading bounds, required citations, and bias flags. Latest run: three of five passing. The two failures are documented in `docs/eval-report.md` with the precise check that didn't pass. We don't gloss them — the eval doesn't earn its keep if it lies to us.

#### Pillar 3: production observability *(30s)*

> Every underwriting run produces a single nested trace tree in Langfuse — five agents, their LLM calls, tokens, cost, latency. There's a `/health` endpoint for liveness probes and a `/metrics` endpoint for at-a-glance counters. Every log line carries a request ID that follows the request through every agent. When something goes wrong, you can find it.

---

### `[4:30 – 5:00]` Close *(30s)*

**Show:** Slide 3 — closing slide (`github.com/mcaleb808/underwrite-ai`).

**Say:**

> Backend on Cloud Run, frontend on Vercel, infrastructure in Terraform — fully reproducible from a fresh GCP project, fully destroyable when you're done. Five agents, five eval cases, structured logs, traced AI calls. Code is at github.com/mcaleb808/underwrite-ai. Happy to take questions.

---

## Slide outline (3 slides total)

Keep it minimal. The product is the demo; slides are punctuation.

### Slide 1 — Title (5 seconds on screen)

- **UnderwriteAI**
- *Health insurance underwriting in seconds*
- Your name, the date

### Slide 2 — One architecture diagram (visible during pillars segment, ~90s)

Use the **System view** mermaid from [`docs/architecture.md`](architecture.md), or a simplified version: browser → API → 5-agent graph → SQLite + Chroma + email.

Captions to mention while it's on screen: *deterministic risk scorer · regex bias backstop · pinned foundational rules · single nested trace per run.*

### Slide 3 — Close (5 seconds on screen)

- `github.com/mcaleb808/underwrite-ai`
- Tech stack (icons or short list): Next.js · FastAPI · LangGraph · Chroma · Cloud Run · Vercel · Terraform · Langfuse
- *Questions?*

---

## If something breaks

- **Pipeline hangs at one step.** Don't wait. Switch to `docs/screenshots/03-decision-card.png` — *"this is what the same case looks like when it completes; let me show you the modify flow next"* — and skip to the modify segment.
- **Decision card looks wrong.** Don't troubleshoot live. *"The latest run had a regression I'm tracking — here's a clean run from earlier"* — switch to a screenshot.
- **Both servers down.** Open the recorded fallback video (link in `docs/demo-video.md` once it exists) — *"let me play the recorded version while I tell you what's happening"*.
- **Audience asks a deep question mid-demo.** *"Great question — let me park that and come back to it after the close"*. Don't break the flow.

---

## After the demo

The Q&A pre-prep — 15 anticipated questions with talking-point answers — is in [`docs/qa.md`](qa.md). Read it the morning of.
