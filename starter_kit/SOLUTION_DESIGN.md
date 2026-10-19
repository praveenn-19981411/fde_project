# Churn-Risk Screening: Solution Design

## Executive summary

Vantage Retail Systems wants to identify accounts whose product engagement may
be weakening before renewal. The supplied data contains weekly login counts,
but does not contain churn outcomes. This implementation therefore provides a
simple, explainable usage-based screening rule—not a trained model or a
probability of churn.

For an account with enough history, the tool compares the average logins in the
latest four weeks with the average in the four weeks immediately before them.
A decline of at least 30% is labeled `at_risk`. The output is a review queue
for a Customer Success person; it does not determine whether an account will
churn.

## User problem and intended outcome

Customer Success currently learns about some non-renewals too late to
intervene. The first useful step is to turn the login history they already
track into a repeatable signal, explain why an account appears to be declining,
and distinguish a lack of history from reassuring usage.

The v1 outcome is a terminal and text-file report that answers:

- Which accounts crossed the initial decline threshold?
- How much did their weekly logins change?
- Which accounts are declining but below the threshold?
- Which accounts cannot yet be scored?

## Data and assumptions

- Input is JSON with an `accounts` list. Every account has an ID, name, plan
  tier, and `weekly_logins` list.
- Login values are non-negative integers, ordered oldest to newest, with one
  value per consecutive week. The provided data has no dates, so this
  continuity assumption cannot be checked.
- Two complete periods are needed. With a four-week window, accounts need at
  least eight weekly values.
- A percentage decline of 30% or more is an initial signal for human review.
- When the earlier-period average is zero, percentage change is undefined and
  the account is `not_scored`.
- The sample is synthetic and contains only eight accounts. It includes no
  renewal, cancellation, or intervention outcomes.

These assumptions should be confirmed with Customer Success. In particular,
the useful intervention horizon and appropriate alert volume should guide the
period length and decline threshold.

## Processing flow

1. Read and validate the JSON file and required fields.
2. For each account, select two adjacent periods of `window` weeks each.
3. If fewer than `2 × window` values are available, report
   `insufficient_data`.
4. Calculate each period's average and percentage change:

   ```text
   (recent average - previous average) / previous average * 100
   ```

5. Assign a status and a plain-language explanation:
   - `at_risk`: change is less than or equal to the configured threshold.
   - `monitor`: change is negative but above the threshold.
   - `healthy`: change is zero or positive.
   - `not_scored`: the prior average is zero.
6. Print the report and save it as UTF-8 text. Invalid input or file errors are
   reported explicitly and produce a non-zero exit code.

The standard-library implementation has no external dependencies. Analysis is
linear in the input size and performs a single pass per account's selected
periods; this is sufficient for a small batch file, but not a full production
data platform.

## Sample result

With the defaults, the provided dataset produces:

- **At risk:** Northwind Traders (`-60.7%`) and Cascade Meridian (`-73.2%`).
- **Monitor:** Harborview Inc (`-17.4%`) and Choppy Retail Co (`-5.1%`).
- **Healthy:** Bluepeak Corp (`+4.8%`) and Solace Digital (`+41.2%`).
- **Insufficient data:** Fresh Startup Co (5 weeks) and New Signup LLC (2
  weeks).

The generated report is `starter_kit/churn_risk_report.txt`. Values represent
changes in average weekly logins between the periods, not probability of
churning.

## Design choices and trade-offs

Comparing adjacent averages is easy to explain and less sensitive to a single
unusual week than comparing individual observations. It may, however, smooth
over abrupt changes and does not account for seasonal patterns. Percentage
change is interpretable but can exaggerate movement from a very small baseline.

A fixed 30% cutoff gives the team a concrete starting point, but cannot be
called optimal without labeled history and a clear cost for missed risks versus
unnecessary outreach. The tool reports statuses, evidence, and insufficient
history rather than hiding uncertainty behind a single binary field.

## Production recommendations

With more data and time:

1. Confirm alert thresholds and intervention timing with Customer Success;
   consider segment-specific expectations only when supported by evidence.
2. Add week dates, define how to handle missing telemetry, and distinguish a
   measured zero from a missing observation.
3. Join account usage to renewal dates, cancellations, contract information,
   customer segments, and outreach outcomes.
4. Establish a historical baseline first, then compare more complex models
   using time-based holdout periods to avoid future-data leakage.
5. Evaluate precision, recall, calibration, and alert volume against the
   team's capacity and the cost of missed churn.
6. If operationalized, schedule scoring, retain dated results, assign account
   owners, track follow-up, and monitor data quality and performance drift.

## How to run

From the repository root:

```powershell
python starter_kit\churn_utils.py
```

This uses the included data and writes
`starter_kit/churn_risk_report.txt`. The README documents the data format,
options, tests, report statuses, and troubleshooting.
