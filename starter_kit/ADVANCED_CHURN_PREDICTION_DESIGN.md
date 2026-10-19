# Advanced Churn Prediction: Proposed Design

## 1. Executive summary

Vantage Retail Systems wants to identify customer accounts that may churn early
enough for Customer Success to intervene. The current script is a useful,
transparent baseline: it flags a large decline in weekly logins. An advanced
version would learn patterns from historical accounts whose eventual renewal
or churn outcome is known, then estimate each active account's risk over a
defined future period.

This document proposes a phased, supervised machine-learning system. It is a
design proposal, not a description of functionality already implemented.
The supplied sample has only eight synthetic accounts and no churn labels, so
it is not sufficient to train or validate a predictive model.

## 2. Business objective and prediction definition

The system should give Customer Success a prioritized, explainable list of
accounts to review—not automatically decide that an account will churn.

Before training, the business must define:

- **What counts as churn:** for example, a customer cancellation or
  non-renewal, with a consistent event date.
- **Who is eligible for scoring:** for example, active paying accounts that
  are not already in a cancellation process.
- **Prediction horizon:** for example, estimate the chance that an account
  churns within the next 90 days.
- **Intervention capacity:** how many accounts the Customer Success team can
  review each week.
- **Success measure:** whether the prioritized list finds useful risks early
  enough to act, and whether interventions improve retention.

The 90-day horizon is an example for discussion, not a confirmed requirement.
The horizon should match contract timing and the time needed for an effective
customer intervention.

## 3. Data required

The model needs a historical, dated record of both customer signals and
outcomes. Candidate sources include:

| Data area | Example fields | Why it may help |
| --- | --- | --- |
| Account and subscription | Account ID, plan, segment, start date, renewal date, contract value | Provides account context and identifies lifecycle stage. |
| Product usage | Dated logins, active users, feature adoption, usage frequency | Measures engagement level and changes over time. |
| Support | Ticket dates, severity, resolution time, open issues | Surfaces unresolved friction or support burden. |
| Customer Success activity | Outreach dates, meeting outcomes, owner, success plan | Shows engagement and helps measure interventions. |
| Commercial/customer outcomes | Renewal, cancellation, contraction, expansion, outcome date, reason | Supplies the target label for supervised learning. |

Every training observation must represent information that was actually
available on its scoring date. Define a consistent account identity across
systems and document missing, delayed, or corrected records. An observed zero
must be distinguishable from missing telemetry.

## 4. Label and feature design

Create dated account snapshots (for example, one per account per week). For a
chosen horizon `H`, label a snapshot as churned if the account's defined churn
event occurs within the following `H` days; otherwise label it as not churned
only when the full horizon is observable. Exclude or separately handle
accounts whose outcome cannot yet be known. Define treatment of pauses,
reactivations, mergers, and contractions with the business before building the
label.

Candidate features, calculated using data available on or before the snapshot
date:

- Usage in recent periods, including login counts, active-user counts, and
  feature breadth.
- Changes and trends in usage over multiple lookback windows.
- Account tenure and time remaining until renewal.
- Support volume, severity, age of unresolved cases, and resolution times.
- Customer Success engagement and recorded meeting outcomes.
- Plan or segment information, where appropriate and permitted.

Feature logic should be centralized, versioned, and tested to prevent training
and production calculations from drifting apart. Exclude post-snapshot
information, cancellation notices, and other data that would reveal the label
or would not be available when the model is used.

## 5. Modeling approach

Start with simple, comparable baselines:

1. **Current rule-based baseline:** the four-week login comparison and decline
   threshold. Keep this as an understandable benchmark.
2. **Logistic regression:** estimates a probability and provides a relatively
   interpretable first supervised model.
3. **Gradient-boosted trees:** evaluate only if sufficient labeled data exists
   and they provide measurable value over the simpler baseline.

The model output should be a risk score for the agreed horizon. A score is not
a causal explanation and does not prove that an account will churn. If
probabilities are shown to users, assess and improve calibration on held-out
data. Use per-account explanation methods as supporting evidence, not as
guarantees about cause.

Survival analysis may be evaluated later if estimating time-to-churn is
important and censoring is handled correctly. Uplift modeling is a still later
option: it requires reliable records of interventions and outcomes to estimate
which action changes the outcome, not just who appears at risk.

## 6. Training and evaluation

Use chronological evaluation rather than randomly splitting account snapshots:

1. Train on earlier dates.
2. Tune decisions on a later validation period.
3. Report final results on a still later, untouched test period.
4. Keep snapshots from the same account from leaking future information into
   its past.

Churn is often uncommon, so accuracy alone is not a useful success measure.
Report at least:

- Precision and recall at the number of accounts Customer Success can review.
- Precision-recall AUC and the baseline churn rate.
- Calibration (whether predicted probabilities align with observed rates).
- Results by relevant segments and time periods, where sample size supports
  meaningful comparison.
- Alert volume, lead time before churn, and stability over time.

Set acceptance criteria with Customer Success before launch. The model should
only replace or supplement the rule-based baseline if it adds demonstrable
value at an operationally manageable alert volume. Review false positives and
false negatives with the team.

## 7. Proposed production workflow

```text
Source systems
    -> validated dated account data
    -> point-in-time weekly feature dataset
    -> versioned model training and evaluation
    -> approved model artifact
    -> scheduled weekly scoring
    -> account-level risk queue with evidence
    -> Customer Success review and outcome feedback
```

The scoring output should include account ID, scoring date, model version,
prediction horizon, risk score, review priority, and key supporting signals.
Store score snapshots so teams can see how risk changes and so results can be
audited. Do not expose unnecessary personal data in the report.

For an initial release, use a batch job and a controlled review queue rather
than real-time infrastructure. Route high-priority accounts to their owners,
record actions and outcomes, and preserve a path to fall back to the
rule-based baseline.

## 8. Monitoring, ownership, and safeguards

- Monitor input freshness, missingness, invalid values, and feature
  distributions.
- Track score distribution, alert volume, calibration, and outcome performance
  as labels become available.
- Review performance and alert usefulness regularly with Customer Success;
  retrain only through a versioned, evaluated process.
- Set access controls and retention rules for customer data. Use only fields
  with an approved business purpose.
- Keep a human decision-maker in the loop. A risk score should prompt
  investigation, not automatic adverse treatment.
- Document model versions, training dates, label definition, feature versions,
  evaluation results, and known limitations.

## 9. Phased delivery

1. **Define:** agree on churn, eligibility, horizon, intervention capacity,
   data ownership, and success criteria.
2. **Prepare data:** join dated usage and account records to renewal outcomes;
   validate data quality and label completeness.
3. **Establish baseline:** calculate the existing rule on historical snapshots
   and evaluate it with chronological holdouts.
4. **Prototype:** train and compare a logistic-regression baseline; test
   boosted trees only if data volume and results justify them.
5. **Pilot:** deliver a weekly review queue to a limited Customer Success
   group, collect feedback, and monitor alert usefulness.
6. **Operationalize:** automate scoring, versioning, monitoring, ownership,
   access controls, and incident/fallback procedures after the pilot meets
   agreed criteria.

## 10. Current scope and open decisions

The current `churn_utils.py` script implements only the rule-based baseline.
It reads the supplied JSON file, handles insufficient history explicitly, and
writes a human-readable report. It does not train a model, estimate churn
probabilities, connect to customer systems, or send alerts.

The sample dataset cannot answer whether the proposed model would work. Before
implementation, the client should confirm:

1. The business definition of churn and the required prediction horizon.
2. Which historical systems and outcome data are available, and for how many
   accounts and years.
3. How many accounts the team can review and what makes an alert actionable.
4. Which customer fields are approved for modeling and who owns the data.
5. Whether the initial deliverable should remain a batch report or integrate
   with an existing Customer Success workflow.
