# Weekly Login Churn-Risk Screening

## What this tool does

This small command-line tool reviews weekly account login counts and creates a
readable list of accounts whose recent usage has declined substantially. It is
intended to help a Customer Success team decide who may need a check-in.

The result is a **usage-based warning signal**, not a prediction that an account
will churn. It does not make decisions or contact customers automatically.

## Project files

| File | Purpose |
| --- | --- |
| `data/account_usage.json` | Sample input: eight synthetic accounts and their weekly login counts. |
| `churn_utils.py` | Loads and validates input, calculates trends, assigns statuses, and writes the report. |
| `churn_risk_report.txt` | Default generated report; created when the script runs. |
| `SOLUTION_DESIGN.md` | Problem framing, assumptions, trade-offs, and production recommendations. |
| `ADVANCED_CHURN_PREDICTION_DESIGN.md` | Proposed design for a future supervised churn prediction system; not implemented in the current script. |

## Requirements

- Python 3.7 or newer.
- No third-party Python packages are required.
- Run the commands below from the repository root (the directory containing
  `starter_kit`).

Check that Python is available:

```powershell
python --version
```

## Run the analysis

Use the included sample data and default settings:

```powershell
python starter_kit\churn_utils.py
```

The analysis prints a report in the terminal and saves the same report to:

```text
starter_kit/churn_risk_report.txt
```

To use a different input, comparison window, threshold, or report destination:

```powershell
python starter_kit\churn_utils.py `
  --data starter_kit\data\account_usage.json `
  --window 4 `
  --threshold -30 `
  --output results\churn_report.txt
```

The output directory is created if it does not already exist. Relative input
and output paths are resolved from the directory where the command is run.

### Command options

| Option | Default | Meaning |
| --- | --- | --- |
| `--data` | `starter_kit/data/account_usage.json` | JSON file containing the account records. |
| `--window` | `4` | Number of weeks in each comparison period. The analysis compares two adjacent periods, so it needs at least `2 × window` weeks. |
| `--threshold` | `-30` | Percentage-change cutoff. A result at or below `-30` is flagged as `at_risk`. |
| `--output` | `starter_kit/churn_risk_report.txt` | Text report destination. |

For example, `--window 3` compares the latest three weeks with the three weeks
immediately before them and requires at least six weekly values.

## Input data format

The JSON document must contain an `accounts` array. Each account needs a
non-empty string `account_id`, `account_name`, and `plan_tier`, plus a
`weekly_logins` array containing non-negative whole numbers. Login values must
be listed oldest to newest, with one value for each consecutive week.

Example:

```json
{
  "accounts": [
    {
      "account_id": "A-01",
      "account_name": "Northwind Traders",
      "plan_tier": "Growth",
      "weekly_logins": [28, 26, 29, 27, 30, 28, 25, 24, 14, 11, 9, 8]
    }
  ]
}
```

The current file format has no dates. The program therefore assumes that the
values represent consecutive weeks; it cannot identify missing weeks.

## How the score is calculated

With the default four-week window, the program:

1. Takes the four most recent weekly values.
2. Takes the four values immediately before those.
3. Calculates each period's average weekly logins.
4. Computes percentage change from the earlier average to the recent average:

   ```text
   (recent average - previous average) / previous average * 100
   ```

For Northwind Traders, the previous period is `[30, 28, 25, 24]`, averaging
`26.75` logins per week. The recent period is `[14, 11, 9, 8]`, averaging
`10.5`. The percentage change is approximately `-60.7%`, so the account meets
the default `-30%` risk threshold.

## Understanding the report

The report first lists accounts to contact (`at_risk`), then gives the status
and explanation for every account:

| Status | Meaning |
| --- | --- |
| `at_risk` | The recent average declined by at least the configured threshold. Consider reviewing the account and its context. |
| `monitor` | Usage declined, but not enough to cross the threshold. Keep an eye on it. |
| `healthy` | Usage is stable or higher over the comparison periods. This does not guarantee renewal. |
| `insufficient_data` | There are not enough weeks for both comparison periods. Collect more history before scoring. |
| `not_scored` | There is enough history, but the previous-period average is zero, so percentage change is undefined. |

With the sample file and default settings:

- **At risk:** Northwind Traders (`-60.7%`), Cascade Meridian (`-73.2%`).
- **Monitor:** Harborview Inc (`-17.4%`), Choppy Retail Co (`-5.1%`).
- **Healthy:** Bluepeak Corp (`+4.8%`), Solace Digital (`+41.2%`).
- **Insufficient data:** Fresh Startup Co (5 weeks), New Signup LLC (2 weeks).

Treat flagged accounts as candidates for human review, not as confirmed churn.
The report provides the account, usage change, and a short explanation so a
Customer Success owner can investigate additional context.

## Errors and troubleshooting

- **`python` is not recognized:** install Python and ensure it is available on
  `PATH`, or use the Python launcher `py` instead of `python`.
- **Input file not found:** confirm the `--data` path. Relative paths are
  interpreted from the current directory.
- **Invalid JSON or account values:** check the `accounts` structure and the
  required fields described above. The program prints an error and exits
  without producing a success report.
- **Report cannot be written:** check that the destination directory is
  writable and that the output path is not an existing directory.

## Scope and limitations

- The default four-week periods and 30% decline cutoff are initial business
  assumptions, not thresholds validated against historical churn outcomes.
- Only weekly logins are considered. Seasonality, account size, plan tier,
  product adoption, support history, contract dates, and customer feedback are
  not included in the score.
- Small or zero baselines can make percentage changes hard to interpret.
- The sample data is synthetic and contains only eight accounts.
- This is a batch script, not a deployed service: it does not schedule itself,
  store score history, send alerts, or provide a user interface.

See [SOLUTION_DESIGN.md](SOLUTION_DESIGN.md) for the design rationale and
recommended steps toward a production-ready rule-based system. See
[ADVANCED_CHURN_PREDICTION_DESIGN.md](ADVANCED_CHURN_PREDICTION_DESIGN.md) for
a separate proposal for a future model-based system.
