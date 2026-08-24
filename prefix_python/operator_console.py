from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

OPS_VERSION = "0.1.0"
SCHEMA_VERSION = "1.0.0"
MIN_EVALUATION_DAYS = 1
MAX_EVALUATION_DAYS = 90
MIN_SEAT_COUNT = 1
MAX_SEAT_COUNT = 500

CORE_MILESTONES = ("onboarding", "install", "demo", "replay", "refusal", "rollback")
TRUST_LEVELS = ("low", "medium", "high")
ENTERPRISE_INTEREST_LEVELS = ("none", "monitoring", "active")
ISSUE_SEVERITIES = ("low", "medium", "high", "critical")
ISSUE_STATUSES = ("open", "resolved")
PROGRAM_REQUIRED_KEYS = (
    "controlled_release_label",
    "evaluation_days",
    "program_id",
    "program_name",
    "release_bundle",
    "schema_version",
    "version",
)
INVITE_REQUIRED_KEYS = (
    "cohort_id",
    "cohort_name",
    "duration_days",
    "evaluation_license_id",
    "evaluation_start_on",
    "evaluation_ends_on",
    "invite_id",
    "operator_email",
    "operator_name",
    "program_id",
    "release_bundle",
    "schema_version",
    "seat_count",
    "stage",
    "team_id",
    "team_name",
    "version",
)
ENROLLMENT_REQUIRED_KEYS = (
    "activated_on",
    "cohort_id",
    "cohort_name",
    "evaluation_ends_on",
    "evaluation_license_id",
    "evaluation_start_on",
    "invite_id",
    "operator_email",
    "operator_name",
    "program_id",
    "release_bundle",
    "schema_version",
    "seat_count",
    "stage",
    "team_id",
    "team_name",
    "version",
)
CHECKPOINT_REQUIRED_KEYS = (
    "all_core_milestones_complete",
    "checkpoint_date",
    "enterprise_interest",
    "metrics",
    "milestones",
    "notes",
    "schema_version",
    "team_id",
    "trust_level",
    "version",
)
ISSUE_REQUIRED_KEYS = (
    "category",
    "issue_date",
    "schema_version",
    "severity",
    "status",
    "summary",
    "team_id",
    "version",
)


@dataclass(frozen=True)
class OpsError(Exception):
    message: str


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="prefix-python-ops",
        description="Deterministic founding-operator operations for PREFIX for Python.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a deterministic founding-operator workspace.")
    init_parser.add_argument("--root", required=True, help="Workspace root for founding-operator operations.")
    init_parser.add_argument("--program-name", default="PREFIX Founding Operator Cohort")
    init_parser.add_argument("--evaluation-days", type=int, default=30)
    init_parser.add_argument("--release-bundle", required=True)
    init_parser.add_argument("--release-sha256", help="Optional explicit bundle hash.")
    init_parser.set_defaults(handler=_cmd_init)

    invite_parser = subparsers.add_parser("invite", help="Generate a deterministic invite and evaluation license.")
    invite_parser.add_argument("--root", required=True)
    invite_parser.add_argument("--cohort-name", required=True)
    invite_parser.add_argument("--team-name", required=True)
    invite_parser.add_argument("--operator-name", required=True)
    invite_parser.add_argument("--operator-email", required=True)
    invite_parser.add_argument("--seat-count", type=int, required=True)
    invite_parser.add_argument("--start-date", required=True)
    invite_parser.add_argument("--duration-days", type=int)
    invite_parser.set_defaults(handler=_cmd_invite)

    activate_parser = subparsers.add_parser("activate", help="Activate an invited team into the evaluation cohort.")
    activate_parser.add_argument("--root", required=True)
    activate_parser.add_argument("--invite-id", required=True)
    activate_parser.add_argument("--activation-date", required=True)
    activate_parser.set_defaults(handler=_cmd_activate)

    checkpoint_parser = subparsers.add_parser("checkpoint", help="Record a deterministic evaluation checkpoint.")
    checkpoint_parser.add_argument("--root", required=True)
    checkpoint_parser.add_argument("--team-id", required=True)
    checkpoint_parser.add_argument("--checkpoint-date", required=True)
    checkpoint_parser.add_argument("--onboarding", choices=("complete", "incomplete"), required=True)
    checkpoint_parser.add_argument("--install", choices=("complete", "incomplete"), required=True)
    checkpoint_parser.add_argument("--demo", choices=("complete", "incomplete"), required=True)
    checkpoint_parser.add_argument("--replay", choices=("complete", "incomplete"), required=True)
    checkpoint_parser.add_argument("--refusal", choices=("complete", "incomplete"), required=True)
    checkpoint_parser.add_argument("--rollback", choices=("complete", "incomplete"), required=True)
    checkpoint_parser.add_argument("--trust-level", choices=TRUST_LEVELS, required=True)
    checkpoint_parser.add_argument("--enterprise-interest", choices=ENTERPRISE_INTEREST_LEVELS, required=True)
    checkpoint_parser.add_argument("--replay-count", type=int, default=0)
    checkpoint_parser.add_argument("--refusal-count", type=int, default=0)
    checkpoint_parser.add_argument("--rollback-count", type=int, default=0)
    checkpoint_parser.add_argument("--open-issues", type=int, default=0)
    checkpoint_parser.add_argument("--notes", default="")
    checkpoint_parser.set_defaults(handler=_cmd_checkpoint)

    issue_parser = subparsers.add_parser("issue", help="Record a deterministic operator issue.")
    issue_parser.add_argument("--root", required=True)
    issue_parser.add_argument("--team-id", required=True)
    issue_parser.add_argument("--issue-date", required=True)
    issue_parser.add_argument("--severity", choices=ISSUE_SEVERITIES, required=True)
    issue_parser.add_argument("--category", required=True)
    issue_parser.add_argument("--summary", required=True)
    issue_parser.add_argument("--status", choices=ISSUE_STATUSES, required=True)
    issue_parser.set_defaults(handler=_cmd_issue)

    summary_parser = subparsers.add_parser("cohort-summary", help="Generate a cohort summary report.")
    summary_parser.add_argument("--root", required=True)
    summary_parser.add_argument("--as-of", required=True)
    summary_parser.set_defaults(handler=_cmd_cohort_summary)

    reminders_parser = subparsers.add_parser("reminders", help="Generate deterministic operator reminders.")
    reminders_parser.add_argument("--root", required=True)
    reminders_parser.add_argument("--as-of", required=True)
    reminders_parser.set_defaults(handler=_cmd_reminders)

    conversion_parser = subparsers.add_parser("conversion-summary", help="Generate conversion readiness and enterprise follow-up summary.")
    conversion_parser.add_argument("--root", required=True)
    conversion_parser.add_argument("--as-of", required=True)
    conversion_parser.set_defaults(handler=_cmd_conversion_summary)

    distribution_parser = subparsers.add_parser("distribution-manifest", help="Generate release distribution manifest for active operators.")
    distribution_parser.add_argument("--root", required=True)
    distribution_parser.add_argument("--as-of", required=True)
    distribution_parser.set_defaults(handler=_cmd_distribution_manifest)

    args = parser.parse_args(argv)
    try:
        payload = args.handler(args)
        _emit(payload)
        return 0 if payload.get("status") == "OK" else 2
    except OpsError as exc:
        _emit({"status": "BLOCKED", "reason": exc.message, "version": OPS_VERSION})
        return 2
    except Exception:
        _emit(
            {
                "status": "BLOCKED",
                "reason": "PREFIX operator console blocked due to an unexpected internal condition.",
                "version": OPS_VERSION,
            }
        )
        return 2


def _cmd_init(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.root).resolve()
    bundle_path = Path(args.release_bundle).resolve()
    bundle_sha256 = _verify_release_bundle_path(bundle_path, args.release_sha256)
    evaluation_days = _require_int_range(args.evaluation_days, "evaluation_days", MIN_EVALUATION_DAYS, MAX_EVALUATION_DAYS)
    program_name = _require_non_empty_text(args.program_name, "program_name")
    _ensure_workspace_dirs(root)
    payload = {
        "controlled_release_label": "Controlled Evaluation Release",
        "evaluation_days": evaluation_days,
        "program_id": _stable_id({"program_name": program_name, "release_bundle_sha256": bundle_sha256}),
        "program_name": program_name,
        "release_bundle": {"path": str(bundle_path), "sha256": bundle_sha256},
        "schema_version": SCHEMA_VERSION,
        "version": OPS_VERSION,
    }
    _write_record(root / "program.json", payload)
    return {
        "bundle_sha256": bundle_sha256,
        "program_id": payload["program_id"],
        "root": str(root),
        "status": "OK",
        "version": OPS_VERSION,
        "workspace_ready": True,
    }


def _cmd_invite(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.root).resolve()
    program = _load_verified_program(root)
    start_on = _parse_date(args.start_date)
    duration_days = _require_int_range(
        args.duration_days if args.duration_days is not None else program["evaluation_days"],
        "duration_days",
        MIN_EVALUATION_DAYS,
        MAX_EVALUATION_DAYS,
    )
    seat_count = _require_int_range(args.seat_count, "seat_count", MIN_SEAT_COUNT, MAX_SEAT_COUNT)
    cohort_name = _require_non_empty_text(args.cohort_name, "cohort_name")
    team_name = _require_non_empty_text(args.team_name, "team_name")
    operator_name = _require_non_empty_text(args.operator_name, "operator_name")
    operator_email = _normalize_email(args.operator_email)
    team_id = _slug_id("team", team_name, operator_email, cohort_name)
    cohort_id = _slug_id("cohort", cohort_name)
    _ensure_unique_team_identity(root, team_id)
    invite_payload = {
        "cohort_id": cohort_id,
        "cohort_name": cohort_name,
        "duration_days": duration_days,
        "evaluation_license_id": _slug_id("lic", team_id, start_on.isoformat(), str(duration_days)),
        "evaluation_start_on": start_on.isoformat(),
        "evaluation_ends_on": (start_on + timedelta(days=duration_days)).isoformat(),
        "invite_id": _slug_id("invite", team_id, start_on.isoformat(), str(duration_days)),
        "operator_email": operator_email,
        "operator_name": operator_name,
        "program_id": program["program_id"],
        "release_bundle": program["release_bundle"],
        "schema_version": SCHEMA_VERSION,
        "seat_count": seat_count,
        "stage": "invited",
        "team_id": team_id,
        "team_name": team_name,
        "version": OPS_VERSION,
    }
    _ensure_unique_license_identity(root, invite_payload["evaluation_license_id"])
    _write_record(
        root / "cohorts" / f"{cohort_id}.json",
        {"cohort_id": cohort_id, "cohort_name": cohort_name, "schema_version": SCHEMA_VERSION, "version": OPS_VERSION},
    )
    invite_path = root / "invites" / f"{invite_payload['invite_id']}.json"
    _write_record(invite_path, invite_payload)
    _write_event(root, "invite_created", invite_payload)
    return {
        "invite_id": invite_payload["invite_id"],
        "license_id": invite_payload["evaluation_license_id"],
        "status": "OK",
        "team_id": team_id,
        "version": OPS_VERSION,
    }


def _cmd_activate(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.root).resolve()
    program = _load_verified_program(root)
    invite = _load_json(root / "invites" / f"{args.invite_id}.json", "invite", INVITE_REQUIRED_KEYS)
    _ensure_release_bundle_matches_program(invite["release_bundle"], program["release_bundle"], "invite")
    activation_on = _parse_date(args.activation_date)
    start_on = _parse_date(str(invite["evaluation_start_on"]))
    end_on = _parse_date(str(invite["evaluation_ends_on"]))
    if activation_on < start_on:
        raise OpsError("PREFIX operator console refused activation because activation precedes the invited evaluation start date.")
    if activation_on > end_on:
        raise OpsError("PREFIX operator console refused activation because the invited evaluation window has already expired.")
    enrollment_payload = {
        "activated_on": activation_on.isoformat(),
        "cohort_id": invite["cohort_id"],
        "cohort_name": invite["cohort_name"],
        "evaluation_ends_on": invite["evaluation_ends_on"],
        "evaluation_license_id": invite["evaluation_license_id"],
        "evaluation_start_on": invite["evaluation_start_on"],
        "invite_id": invite["invite_id"],
        "operator_email": invite["operator_email"],
        "operator_name": invite["operator_name"],
        "program_id": invite["program_id"],
        "release_bundle": invite["release_bundle"],
        "schema_version": SCHEMA_VERSION,
        "seat_count": int(invite["seat_count"]),
        "stage": "active",
        "team_id": invite["team_id"],
        "team_name": invite["team_name"],
        "version": OPS_VERSION,
    }
    enrollment_path = root / "enrollments" / f"{invite['team_id']}.json"
    _write_record(enrollment_path, enrollment_payload)
    _write_event(root, "evaluation_activated", enrollment_payload)
    return {
        "evaluation_ends_on": enrollment_payload["evaluation_ends_on"],
        "license_id": enrollment_payload["evaluation_license_id"],
        "status": "OK",
        "team_id": invite["team_id"],
        "version": OPS_VERSION,
    }


def _cmd_checkpoint(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.root).resolve()
    program = _load_verified_program(root)
    enrollment = _load_verified_enrollment(root, args.team_id, program)
    checkpoint_on = _parse_date(args.checkpoint_date)
    activation_on = _parse_date(str(enrollment["activated_on"]))
    evaluation_end_on = _parse_date(str(enrollment["evaluation_ends_on"]))
    if checkpoint_on < activation_on:
        raise OpsError("PREFIX operator console refused the checkpoint because it predates activation.")
    if checkpoint_on > evaluation_end_on:
        raise OpsError("PREFIX operator console refused the checkpoint because it falls outside the evaluation term.")
    milestone_state = {name: getattr(args, name) == "complete" for name in CORE_MILESTONES}
    payload = {
        "all_core_milestones_complete": all(milestone_state.values()),
        "checkpoint_date": checkpoint_on.isoformat(),
        "enterprise_interest": args.enterprise_interest,
        "metrics": {
            "open_issues": _require_non_negative_int(args.open_issues, "open_issues"),
            "refusal_count": _require_non_negative_int(args.refusal_count, "refusal_count"),
            "replay_count": _require_non_negative_int(args.replay_count, "replay_count"),
            "rollback_count": _require_non_negative_int(args.rollback_count, "rollback_count"),
        },
        "milestones": milestone_state,
        "notes": args.notes.strip(),
        "schema_version": SCHEMA_VERSION,
        "team_id": args.team_id,
        "trust_level": args.trust_level,
        "version": OPS_VERSION,
    }
    checkpoint_id = _slug_id("checkpoint", args.team_id, checkpoint_on.isoformat())
    _write_record(root / "checkpoints" / f"{checkpoint_id}.json", payload)
    _write_event(root, "checkpoint_recorded", payload)
    return {
        "checkpoint_id": checkpoint_id,
        "status": "OK",
        "team_id": args.team_id,
        "version": OPS_VERSION,
    }


def _cmd_issue(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.root).resolve()
    program = _load_verified_program(root)
    enrollment = _load_verified_enrollment(root, args.team_id, program)
    issue_on = _parse_date(args.issue_date)
    activation_on = _parse_date(str(enrollment["activated_on"]))
    evaluation_end_on = _parse_date(str(enrollment["evaluation_ends_on"]))
    if issue_on < activation_on:
        raise OpsError("PREFIX operator console refused the issue record because it predates activation.")
    if issue_on > evaluation_end_on:
        raise OpsError("PREFIX operator console refused the issue record because it falls outside the evaluation term.")
    category = _require_non_empty_text(args.category, "category")
    summary = _require_non_empty_text(args.summary, "summary")
    payload = {
        "category": category,
        "issue_date": issue_on.isoformat(),
        "schema_version": SCHEMA_VERSION,
        "severity": args.severity,
        "status": args.status,
        "summary": summary,
        "team_id": args.team_id,
        "version": OPS_VERSION,
    }
    issue_id = _slug_id("issue", args.team_id, issue_on.isoformat(), category, summary)
    _write_record(root / "issues" / f"{issue_id}.json", payload)
    _write_event(root, "issue_recorded", payload)
    return {"issue_id": issue_id, "status": "OK", "team_id": args.team_id, "version": OPS_VERSION}


def _cmd_cohort_summary(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.root).resolve()
    as_of = _parse_date(args.as_of)
    report = _build_cohort_summary(root, as_of)
    path = root / "reports" / f"cohort-summary-{as_of.isoformat()}.json"
    _write_report(path, report)
    return {"report_path": str(path), "status": "OK", "summary": report["summary"], "version": OPS_VERSION}


def _cmd_reminders(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.root).resolve()
    as_of = _parse_date(args.as_of)
    report = _build_reminders_report(root, as_of)
    path = root / "reports" / f"reminders-{as_of.isoformat()}.json"
    _write_report(path, report)
    return {"count": len(report["reminders"]), "report_path": str(path), "status": "OK", "version": OPS_VERSION}


def _cmd_conversion_summary(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.root).resolve()
    as_of = _parse_date(args.as_of)
    report = _build_conversion_summary(root, as_of)
    path = root / "reports" / f"conversion-summary-{as_of.isoformat()}.json"
    _write_report(path, report)
    return {"report_path": str(path), "status": "OK", "summary": report["summary"], "version": OPS_VERSION}


def _cmd_distribution_manifest(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.root).resolve()
    as_of = _parse_date(args.as_of)
    report = _build_distribution_manifest(root, as_of)
    path = root / "reports" / f"distribution-manifest-{as_of.isoformat()}.json"
    _write_report(path, report)
    return {"distribution_count": len(report["distributions"]), "report_path": str(path), "status": "OK", "version": OPS_VERSION}


def _build_cohort_summary(root: Path, as_of: date) -> dict[str, object]:
    program = _load_verified_program(root)
    enrollments = _load_verified_enrollments(root, program)
    checkpoints = _load_all_json(root / "checkpoints", CHECKPOINT_REQUIRED_KEYS)
    issues = _load_all_json(root / "issues", ISSUE_REQUIRED_KEYS)
    latest_checkpoints = _latest_checkpoints(checkpoints)
    issue_lookup = _issues_by_team(issues)
    teams = []
    for enrollment in enrollments:
        team = _team_snapshot(enrollment, latest_checkpoints.get(enrollment["team_id"]), issue_lookup.get(enrollment["team_id"], []), as_of)
        teams.append(team)
    teams.sort(key=lambda item: item["team_name"])
    return {
        "as_of": as_of.isoformat(),
        "bundle_hash_verified": True,
        "program_id": program["program_id"],
        "schema_version": SCHEMA_VERSION,
        "summary": {
            "active_teams": sum(1 for team in teams if team["lifecycle_state"] == "active"),
            "conversion_ready_teams": sum(1 for team in teams if team["conversion_ready"]),
            "expiring_soon_teams": sum(1 for team in teams if 0 <= team["days_remaining"] <= 7),
            "total_seats": sum(int(team["seat_count"]) for team in teams),
            "total_teams": len(teams),
        },
        "teams": teams,
        "version": OPS_VERSION,
        "workspace_fingerprint": _workspace_fingerprint(root),
    }


def _build_reminders_report(root: Path, as_of: date) -> dict[str, object]:
    program = _load_verified_program(root)
    enrollments = _load_verified_enrollments(root, program)
    checkpoints = _latest_checkpoints(_load_all_json(root / "checkpoints", CHECKPOINT_REQUIRED_KEYS))
    reminders: list[dict[str, object]] = []
    for enrollment in enrollments:
        snapshot = _team_snapshot(enrollment, checkpoints.get(enrollment["team_id"]), [], as_of)
        milestones = snapshot["milestones"]
        if snapshot["days_elapsed"] >= 3 and not milestones["onboarding"]:
            reminders.append(_reminder(snapshot, "onboarding_checkpoint_due", "Onboarding checkpoint has not been completed by day 3."))
        if snapshot["days_elapsed"] >= 7 and not milestones["demo"]:
            reminders.append(_reminder(snapshot, "demo_walkthrough_due", "The deterministic demo walkthrough has not been completed by day 7."))
        if snapshot["days_elapsed"] >= 14 and not milestones["replay"]:
            reminders.append(_reminder(snapshot, "replay_validation_due", "Replay validation has not been completed by day 14."))
        if snapshot["days_elapsed"] >= 14 and not milestones["rollback"]:
            reminders.append(_reminder(snapshot, "rollback_validation_due", "Rollback validation has not been completed by day 14."))
        if 0 <= snapshot["days_remaining"] <= 9 and not snapshot["conversion_ready"]:
            reminders.append(_reminder(snapshot, "conversion_review_window", "The evaluation is within nine days of expiry and is not yet conversion-ready."))
        if snapshot["days_remaining"] < 0:
            reminders.append(_reminder(snapshot, "evaluation_expired", "The evaluation term has expired and requires closure or conversion."))
    reminders.sort(key=lambda item: (item["team_name"], item["reminder_code"]))
    return {
        "as_of": as_of.isoformat(),
        "bundle_hash_verified": True,
        "reminders": reminders,
        "schema_version": SCHEMA_VERSION,
        "version": OPS_VERSION,
        "workspace_fingerprint": _workspace_fingerprint(root),
    }


def _build_conversion_summary(root: Path, as_of: date) -> dict[str, object]:
    program = _load_verified_program(root)
    enrollments = _load_verified_enrollments(root, program)
    checkpoints = _latest_checkpoints(_load_all_json(root / "checkpoints", CHECKPOINT_REQUIRED_KEYS))
    issues = _issues_by_team(_load_all_json(root / "issues", ISSUE_REQUIRED_KEYS))
    teams = []
    for enrollment in enrollments:
        snapshot = _team_snapshot(enrollment, checkpoints.get(enrollment["team_id"]), issues.get(enrollment["team_id"], []), as_of)
        teams.append(
            {
                "conversion_ready": snapshot["conversion_ready"],
                "days_remaining": snapshot["days_remaining"],
                "enterprise_followup_recommended": snapshot["enterprise_followup_recommended"],
                "evaluation_license_id": snapshot["evaluation_license_id"],
                "lifecycle_state": snapshot["lifecycle_state"],
                "open_issue_count": snapshot["open_issue_count"],
                "team_id": snapshot["team_id"],
                "team_name": snapshot["team_name"],
                "trust_level": snapshot["trust_level"],
            }
        )
    teams.sort(key=lambda item: item["team_name"])
    return {
        "as_of": as_of.isoformat(),
        "bundle_hash_verified": True,
        "schema_version": SCHEMA_VERSION,
        "summary": {
            "conversion_ready_teams": sum(1 for item in teams if item["conversion_ready"]),
            "enterprise_followup_teams": sum(1 for item in teams if item["enterprise_followup_recommended"]),
            "teams_nearing_expiry": sum(1 for item in teams if 0 <= item["days_remaining"] <= 9),
            "total_teams": len(teams),
        },
        "teams": teams,
        "version": OPS_VERSION,
        "workspace_fingerprint": _workspace_fingerprint(root),
    }


def _build_distribution_manifest(root: Path, as_of: date) -> dict[str, object]:
    program = _load_verified_program(root)
    enrollments = _load_verified_enrollments(root, program)
    distributions = []
    for enrollment in sorted(enrollments, key=lambda item: item["team_name"]):
        distributions.append(
            {
                "as_of": as_of.isoformat(),
                "bundle_hash_verified": True,
                "evaluation_license_id": enrollment["evaluation_license_id"],
                "release_bundle_path": enrollment["release_bundle"]["path"],
                "release_bundle_sha256": enrollment["release_bundle"]["sha256"],
                "team_id": enrollment["team_id"],
                "team_name": enrollment["team_name"],
            }
        )
    return {
        "bundle_hash_verified": True,
        "distributions": distributions,
        "program_id": program["program_id"],
        "schema_version": SCHEMA_VERSION,
        "version": OPS_VERSION,
        "workspace_fingerprint": _workspace_fingerprint(root),
    }


def _team_snapshot(
    enrollment: dict[str, object],
    checkpoint: dict[str, object] | None,
    issues: list[dict[str, object]],
    as_of: date,
) -> dict[str, object]:
    start_on = _parse_date(str(enrollment["evaluation_start_on"]))
    end_on = _parse_date(str(enrollment["evaluation_ends_on"]))
    days_elapsed = (as_of - start_on).days
    days_remaining = (end_on - as_of).days
    milestones = {name: False for name in CORE_MILESTONES}
    trust_level = "low"
    enterprise_interest = "none"
    metrics = {"open_issues": 0, "refusal_count": 0, "replay_count": 0, "rollback_count": 0}
    if checkpoint is not None:
        milestones.update({key: bool(value) for key, value in checkpoint["milestones"].items()})
        trust_level = str(checkpoint["trust_level"])
        enterprise_interest = str(checkpoint["enterprise_interest"])
        metrics = {key: int(value) for key, value in checkpoint["metrics"].items()}
    open_issue_count = sum(1 for issue in issues if issue["status"] == "open")
    conversion_ready = days_remaining >= 0 and all(milestones.values()) and trust_level in {"medium", "high"} and open_issue_count == 0
    enterprise_followup_recommended = conversion_ready or enterprise_interest == "active" or int(enrollment["seat_count"]) >= 10
    lifecycle_state = "expired" if days_remaining < 0 else "active"
    return {
        "conversion_ready": conversion_ready,
        "days_elapsed": max(days_elapsed, 0),
        "days_remaining": days_remaining,
        "enterprise_followup_recommended": enterprise_followup_recommended,
        "enterprise_interest": enterprise_interest,
        "evaluation_license_id": enrollment["evaluation_license_id"],
        "lifecycle_state": lifecycle_state,
        "milestones": milestones,
        "open_issue_count": open_issue_count,
        "seat_count": int(enrollment["seat_count"]),
        "team_id": enrollment["team_id"],
        "team_name": enrollment["team_name"],
        "trust_level": trust_level,
        "usage_metrics": metrics,
    }


def _reminder(snapshot: dict[str, object], code: str, message: str) -> dict[str, object]:
    return {
        "days_remaining": snapshot["days_remaining"],
        "message": message,
        "reminder_code": code,
        "team_id": snapshot["team_id"],
        "team_name": snapshot["team_name"],
    }


def _latest_checkpoints(checkpoints: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    latest: dict[str, dict[str, object]] = {}
    for checkpoint in checkpoints:
        team_id = str(checkpoint["team_id"])
        existing = latest.get(team_id)
        if existing is None or str(checkpoint["checkpoint_date"]) > str(existing["checkpoint_date"]):
            latest[team_id] = checkpoint
    return latest


def _issues_by_team(issues: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for issue in issues:
        grouped.setdefault(str(issue["team_id"]), []).append(issue)
    return grouped


def _ensure_workspace_dirs(root: Path) -> None:
    for relative in ("cohorts", "invites", "enrollments", "checkpoints", "issues", "reports", "events"):
        (root / relative).mkdir(parents=True, exist_ok=True)


def _load_verified_program(root: Path) -> dict[str, object]:
    program = _load_json(root / "program.json", "program", PROGRAM_REQUIRED_KEYS)
    _verify_release_bundle_record(program["release_bundle"], "program")
    return program


def _load_verified_enrollment(root: Path, team_id: str, program: dict[str, object]) -> dict[str, object]:
    enrollment = _load_json(root / "enrollments" / f"{team_id}.json", "enrollment", ENROLLMENT_REQUIRED_KEYS)
    _ensure_release_bundle_matches_program(enrollment["release_bundle"], program["release_bundle"], "enrollment")
    return enrollment


def _load_verified_enrollments(root: Path, program: dict[str, object]) -> list[dict[str, object]]:
    enrollments = _load_all_json(root / "enrollments", ENROLLMENT_REQUIRED_KEYS)
    for enrollment in enrollments:
        _ensure_release_bundle_matches_program(enrollment["release_bundle"], program["release_bundle"], "enrollment")
    return enrollments


def _load_json(path: Path, label: str, required_keys: Iterable[str]) -> dict[str, object]:
    if not path.exists() or not path.is_file():
        raise OpsError(f"PREFIX operator console could not find the required {label} record `{path}`.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OpsError(f"PREFIX operator console found a malformed {label} record at `{path}`.") from exc
    if not isinstance(payload, dict):
        raise OpsError(f"PREFIX operator console expected `{path}` to contain a JSON object.")
    missing = sorted(set(required_keys) - set(payload.keys()))
    if missing:
        raise OpsError(f"PREFIX operator console found an incomplete {label} record at `{path}`. Missing keys: {', '.join(missing)}.")
    return payload


def _load_all_json(folder: Path, required_keys: Iterable[str]) -> list[dict[str, object]]:
    if not folder.exists():
        return []
    payloads: list[dict[str, object]] = []
    for path in sorted(folder.glob("*.json")):
        payloads.append(_load_json(path, path.stem, required_keys))
    return payloads


def _verify_release_bundle_path(bundle_path: Path, expected_sha256: str | None) -> str:
    if not bundle_path.exists() or not bundle_path.is_file():
        raise OpsError(f"PREFIX operator console could not find the release bundle `{bundle_path}`.")
    actual_sha256 = _sha256_file(bundle_path)
    if expected_sha256 is None:
        return actual_sha256
    normalized_expected = _normalize_sha256(expected_sha256, "release_sha256")
    if actual_sha256 != normalized_expected:
        raise OpsError("PREFIX operator console refused initialization because the supplied release hash does not match the bundle on disk.")
    return actual_sha256


def _verify_release_bundle_record(bundle_record: object, label: str) -> None:
    if not isinstance(bundle_record, dict):
        raise OpsError(f"PREFIX operator console found a malformed release bundle record in the {label} record.")
    if "path" not in bundle_record or "sha256" not in bundle_record:
        raise OpsError(f"PREFIX operator console found an incomplete release bundle record in the {label} record.")
    bundle_path = Path(str(bundle_record["path"])).resolve()
    expected_sha256 = _normalize_sha256(str(bundle_record["sha256"]), f"{label}_release_bundle_sha256")
    if not bundle_path.exists() or not bundle_path.is_file():
        raise OpsError(f"PREFIX operator console could not verify the pinned release bundle `{bundle_path}` for the {label} record.")
    actual_sha256 = _sha256_file(bundle_path)
    if actual_sha256 != expected_sha256:
        raise OpsError(f"PREFIX operator console detected a release bundle hash mismatch for the {label} record.")


def _ensure_release_bundle_matches_program(bundle_record: object, program_bundle: object, label: str) -> None:
    _verify_release_bundle_record(bundle_record, label)
    if not isinstance(bundle_record, dict) or not isinstance(program_bundle, dict):
        raise OpsError(f"PREFIX operator console found a malformed release bundle comparison while validating the {label} record.")
    if str(bundle_record["path"]) != str(program_bundle["path"]) or str(bundle_record["sha256"]) != str(program_bundle["sha256"]):
        raise OpsError(f"PREFIX operator console detected release bundle drift between the program record and the {label} record.")


def _ensure_unique_team_identity(root: Path, team_id: str) -> None:
    existing_paths = [root / "enrollments" / f"{team_id}.json"]
    existing_paths.extend(sorted((root / "invites").glob("*.json")))
    for path in existing_paths:
        if not path.exists() or not path.is_file():
            continue
        if path.name == f"{team_id}.json":
            raise OpsError(f"PREFIX operator console refused to create a duplicate team enrollment for `{team_id}`.")
        payload = _load_json(path, path.stem, INVITE_REQUIRED_KEYS)
        if str(payload["team_id"]) == team_id:
            raise OpsError(f"PREFIX operator console refused to create a second invite for the existing team `{team_id}`.")


def _ensure_unique_license_identity(root: Path, license_id: str) -> None:
    for folder, required_keys in ((root / "invites", INVITE_REQUIRED_KEYS), (root / "enrollments", ENROLLMENT_REQUIRED_KEYS)):
        for path in sorted(folder.glob("*.json")):
            payload = _load_json(path, path.stem, required_keys)
            if str(payload["evaluation_license_id"]) == license_id:
                raise OpsError(f"PREFIX operator console refused to create a duplicate evaluation license `{license_id}`.")


def _workspace_fingerprint(root: Path) -> str:
    records: list[dict[str, object]] = []
    for folder_name in ("program.json", "cohorts", "invites", "enrollments", "checkpoints", "issues", "events"):
        target = root / folder_name
        if target.is_file():
            records.append({"path": str(target.relative_to(root)).replace("\\", "/"), "sha256": _sha256_text(target.read_text(encoding="utf-8"))})
            continue
        if not target.exists():
            continue
        for path in sorted(target.glob("*.json")):
            records.append({"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": _sha256_text(path.read_text(encoding="utf-8"))})
    return _stable_id(records)


def _write_event(root: Path, event_type: str, payload: dict[str, object]) -> None:
    event_payload = {
        "event_id": _stable_id({"event_type": event_type, "payload": payload}),
        "event_type": event_type,
        "payload_hash": _sha256_text(_canonical_json(payload)),
        "schema_version": SCHEMA_VERSION,
        "version": OPS_VERSION,
    }
    _write_record(root / "events" / f"{event_payload['event_id']}.json", event_payload)


def _write_record(path: Path, payload: dict[str, object]) -> None:
    serialized = _canonical_json(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing != serialized:
            raise OpsError(f"PREFIX operator console refused to overwrite an existing deterministic record `{path}` with different content.")
        return
    path.write_text(serialized, encoding="utf-8")


def _write_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_canonical_json(payload), encoding="utf-8")


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _stable_id(payload: object) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()[:16]


def _slug_id(prefix: str, *parts: str) -> str:
    normalized = {"parts": [part.strip().lower() for part in parts], "prefix": prefix}
    return f"{prefix}-{_stable_id(normalized)}"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise OpsError(f"PREFIX operator console expected an ISO date, received `{value}`.") from exc


def _require_non_empty_text(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise OpsError(f"PREFIX operator console requires a non-empty `{label}` value.")
    return normalized


def _normalize_email(value: str) -> str:
    normalized = _require_non_empty_text(value, "operator_email").lower()
    if normalized.count("@") != 1 or " " in normalized:
        raise OpsError(f"PREFIX operator console requires a valid `operator_email` value, received `{value}`.")
    local_part, domain_part = normalized.split("@")
    if not local_part or not domain_part or "." not in domain_part:
        raise OpsError(f"PREFIX operator console requires a valid `operator_email` value, received `{value}`.")
    return normalized


def _require_int_range(value: object, label: str, minimum: int, maximum: int) -> int:
    if not isinstance(value, int):
        raise OpsError(f"PREFIX operator console requires `{label}` to be an integer.")
    if value < minimum or value > maximum:
        raise OpsError(f"PREFIX operator console requires `{label}` to be between {minimum} and {maximum}.")
    return value


def _require_non_negative_int(value: object, label: str) -> int:
    if not isinstance(value, int):
        raise OpsError(f"PREFIX operator console requires `{label}` to be an integer.")
    if value < 0:
        raise OpsError(f"PREFIX operator console requires `{label}` to be zero or greater.")
    return value


def _normalize_sha256(value: str, label: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise OpsError(f"PREFIX operator console expected `{label}` to be a lowercase SHA-256 hex digest.")
    return normalized


def _emit(payload: dict[str, object]) -> None:
    print(_canonical_json(payload), end="")


if __name__ == "__main__":
    raise SystemExit(main())
