"""Transparent, rule-based churn-risk screening for weekly account logins."""

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union


DEFAULT_WINDOW = 4
DEFAULT_DECLINE_THRESHOLD_PCT = -30.0


@dataclass
class AccountAnalysis:
    account_id: str
    account_name: str
    plan_tier: str
    weeks_observed: int
    previous_average: Optional[float]
    recent_average: Optional[float]
    trend_pct: Optional[float]
    status: str
    reason: str


def _validate_window(window: int) -> None:
    if isinstance(window, bool) or not isinstance(window, int) or window < 1:
        raise ValueError("window must be a positive integer")


def _validate_weekly_logins(weekly_logins: Sequence[int]) -> None:
    if isinstance(weekly_logins, (str, bytes)) or not isinstance(
        weekly_logins, Sequence
    ):
        raise ValueError("weekly_logins must be a sequence of non-negative integers")
    if any(
        isinstance(logins, bool) or not isinstance(logins, int) or logins < 0
        for logins in weekly_logins
    ):
        raise ValueError("weekly_logins must contain only non-negative integers")


def _period_averages(
    weekly_logins: Sequence[int], window: int
) -> Optional[Tuple[float, float]]:
    if len(weekly_logins) < window * 2:
        return None
    previous = weekly_logins[-window * 2 : -window]
    recent = weekly_logins[-window:]
    return sum(previous) / window, sum(recent) / window


def load_accounts(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load and validate account records from a JSON file."""
    with Path(path).open(encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict) or not isinstance(data.get("accounts"), list):
        raise ValueError("JSON input must contain an 'accounts' list")

    required_strings = ("account_id", "account_name", "plan_tier")
    for index, account in enumerate(data["accounts"]):
        if not isinstance(account, dict):
            raise ValueError(f"accounts[{index}] must be a JSON object")
        for field in required_strings:
            if not isinstance(account.get(field), str) or not account[field].strip():
                raise ValueError(
                    f"accounts[{index}].{field} must be a non-empty string"
                )
        if "weekly_logins" not in account:
            raise ValueError(f"accounts[{index}].weekly_logins is required")
        _validate_weekly_logins(account["weekly_logins"])

    return data["accounts"]


def compute_trend_pct(
    weekly_logins: Sequence[int], window: int = DEFAULT_WINDOW
) -> Optional[float]:
    """
    Compare recent and previous equal-length periods as a percentage change.

    Return None if there is not enough history or the previous-period average
    is zero, since a percentage change cannot be calculated in those cases.
    """
    _validate_window(window)
    _validate_weekly_logins(weekly_logins)
    averages = _period_averages(weekly_logins, window)
    if averages is None:
        return None

    previous_average, recent_average = averages
    if previous_average == 0:
        return None
    return (recent_average - previous_average) / previous_average * 100


def analyze_account(
    account: Dict[str, Any],
    window: int = DEFAULT_WINDOW,
    decline_threshold_pct: float = DEFAULT_DECLINE_THRESHOLD_PCT,
) -> AccountAnalysis:
    """Calculate an explainable status for a single account."""
    _validate_window(window)
    if not isinstance(decline_threshold_pct, (int, float)) or not math.isfinite(
        decline_threshold_pct
    ):
        raise ValueError("decline_threshold_pct must be a finite number")
    _validate_weekly_logins(account.get("weekly_logins"))

    account_id = account.get("account_id", "unknown")
    account_name = account.get("account_name", "Unknown account")
    plan_tier = account.get("plan_tier", "Unknown")
    for field, value in (
        ("account_id", account_id),
        ("account_name", account_name),
        ("plan_tier", plan_tier),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string")

    weekly_logins = account["weekly_logins"]
    averages = _period_averages(weekly_logins, window)
    if averages is None:
        return AccountAnalysis(
            account_id=account_id,
            account_name=account_name,
            plan_tier=plan_tier,
            weeks_observed=len(weekly_logins),
            previous_average=None,
            recent_average=None,
            trend_pct=None,
            status="insufficient_data",
            reason=(
                f"Needs at least {window * 2} weeks to compare two "
                f"{window}-week periods; has {len(weekly_logins)}."
            ),
        )

    previous_average, recent_average = averages
    trend_pct = compute_trend_pct(weekly_logins, window)
    if trend_pct is None:
        return AccountAnalysis(
            account_id=account_id,
            account_name=account_name,
            plan_tier=plan_tier,
            weeks_observed=len(weekly_logins),
            previous_average=previous_average,
            recent_average=recent_average,
            trend_pct=None,
            status="not_scored",
            reason="Previous-period average is zero, so percentage change is undefined.",
        )

    if trend_pct <= decline_threshold_pct:
        status = "at_risk"
        reason = (
            f"Logins declined {abs(trend_pct):.1f}%: "
            f"{previous_average:.1f} to {recent_average:.1f} average per week."
        )
    elif trend_pct < 0:
        status = "monitor"
        reason = (
            f"Logins declined {abs(trend_pct):.1f}%, below the "
            f"{abs(decline_threshold_pct):.1f}% risk threshold."
        )
    else:
        status = "healthy"
        reason = f"Logins are stable or increasing ({trend_pct:+.1f}%)."

    return AccountAnalysis(
        account_id=account_id,
        account_name=account_name,
        plan_tier=plan_tier,
        weeks_observed=len(weekly_logins),
        previous_average=previous_average,
        recent_average=recent_average,
        trend_pct=trend_pct,
        status=status,
        reason=reason,
    )


def flag_at_risk(
    account: Dict[str, Any],
    window: int = DEFAULT_WINDOW,
    decline_threshold_pct: float = DEFAULT_DECLINE_THRESHOLD_PCT,
) -> bool:
    """Return True only when sufficient history meets the decline threshold."""
    return (
        analyze_account(account, window, decline_threshold_pct).status == "at_risk"
    )


def format_report(analyses: Sequence[AccountAnalysis]) -> str:
    """Format account results as a concise human-readable report."""
    at_risk = [analysis for analysis in analyses if analysis.status == "at_risk"]
    lines = ["CHURN RISK SCREEN", "================="]
    if at_risk:
        lines.append("Accounts to contact:")
        for analysis in at_risk:
            lines.append(
                f"- {analysis.account_name} ({analysis.account_id}, "
                f"{analysis.plan_tier}): {analysis.reason}"
            )
    else:
        lines.append("No accounts currently meet the risk threshold.")

    lines.extend(["", "All accounts:"])
    for analysis in analyses:
        trend = (
            f"{analysis.trend_pct:+.1f}%"
            if analysis.trend_pct is not None
            else "not scored"
        )
        lines.append(
            f"- {analysis.account_id} | {analysis.account_name} | "
            f"{analysis.status} | trend {trend} | {analysis.reason}"
        )
    return "\n".join(lines)


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    starter_dir = Path(__file__).resolve().parent
    default_data = starter_dir / "data" / "account_usage.json"
    default_output = starter_dir / "churn_risk_report.txt"
    parser = argparse.ArgumentParser(
        description="Flag accounts with a material decline in weekly logins."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=default_data,
        help=f"Path to the account JSON file (default: {default_data})",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=DEFAULT_WINDOW,
        help="Weeks in each comparison period (default: 4)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_DECLINE_THRESHOLD_PCT,
        help="Decline percentage at or below which an account is flagged (default: -30)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=f"Path for the text report (default: {default_output})",
    )
    args = parser.parse_args(argv)
    try:
        _validate_window(args.window)
    except ValueError as error:
        parser.error(str(error))
    if not math.isfinite(args.threshold):
        parser.error("--threshold must be a finite number")
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        accounts = load_accounts(args.data)
        analyses = [
            analyze_account(account, args.window, args.threshold)
            for account in accounts
        ]
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    report = format_report(analyses)
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")
    except OSError as error:
        print(f"Error writing report to {args.output}: {error}", file=sys.stderr)
        return 2

    print(report)
    print(f"\nReport saved to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
