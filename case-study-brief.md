# FDE Take-Home Case Study: Churn Risk Flagging

## Before you start

This exercise mirrors a real Forward Deployed Engineer (FDE) engagement: a customer brings you a genuine but partially-specified problem, and you're expected to (1) clarify/assume what's needed, (2) propose a solution, (3) build a working version of it, and (4) present and defend your approach to the customer (in this case, our panel).

**What we're evaluating:** how you handle ambiguity, the soundness of your design judgment, your ability to build a working solution under real constraints, how clearly you communicate your reasoning, and how you respond when your approach is challenged. We are **not** grading for a "perfect" or exhaustive solution — a well-reasoned, appropriately-scoped solution with clearly stated trade-offs is exactly what we want to see.

## The customer

**Vantage Retail Systems** sells inventory-management software to mid-size retailers. Their Head of Customer Success, Dana Reyes, reached out with the following ask:

> "We only find out an account is about to churn when they tell us they're not renewing — by then it's way too late to do anything about it. We track weekly login counts per account. I'd love something that looks at that usage data and flags accounts that seem to be trending down, early enough that our CS team can actually reach out and try to save the relationship.
>
> I don't have a precise definition of 'at risk' — that's part of what I'm hoping you can help figure out. What would you build for us?"

**Note:** Dana's ask is intentionally incomplete. You will need to decide things like: how much of a decline (and over what time period) counts as "at risk," how much usage history is actually needed before a trend is meaningful, and what you'd do with an account that's too new to have much history yet. **Document whatever assumptions you make.**

## What we're providing you

- A seed dataset of realistic (synthetic) weekly login history across 8 accounts of varying tenure.
- A minimal starter repository scaffold with a basic trend-calculation utility, so you're not starting from a completely blank page.
- *(See `starter_kit/` alongside this brief.)*

## What you have full freedom on

- **Language/stack** — use whatever you're most productive in.
- **Scope** — you decide what's in v1 versus "future work." A smaller, well-reasoned scope beats an ambitious, half-finished one.
- **Exact thresholds** — pick reasonable defaults and state your reasoning; there's no single "correct" number we're looking for.

## Time expectation

We expect this to take **roughly 3-4 focused hours**, with a full week of calendar time to fit it in. If you're well past 4-5 hours, **stop** — use your README to describe what you'd tackle next.

## Required deliverables

1. **`SOLUTION_DESIGN.md`** (1-2 pages): the problem restated in your own words, your assumptions, your proposed approach, the trade-offs you considered, and what you'd do with more time/data/budget.
2. **Working implementation** — should run end-to-end against the provided dataset and produce a clear list of "here's who I'd flag, and why."
3. **`README.md`** — how to run it, known limitations.

## Optional bonus track (not required, never penalized if skipped)

You're welcome to explore an AI-powered enhancement — for example, using an LLM to generate a one-line, human-readable explanation of why a given account was flagged (e.g., "Logins dropped roughly 70% over the last month after several months of steady, heavy usage"). This is a **plus signal**, not a gate.

## What happens after you submit

We'll review your submission ahead of a **30-45 minute live session**: a walkthrough of your design doc and a short demo, followed by Q&A, including "what if..." questions and the occasional new constraint introduced mid-conversation.

## Submission

Send us a link to your repository (or a zip archive) containing your code, `SOLUTION_DESIGN.md`, and `README.md`.
