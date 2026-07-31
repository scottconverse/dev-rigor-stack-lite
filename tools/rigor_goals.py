#!/usr/bin/env python3
"""rigor-goals - a self-contained, stdlib-only durable development loop.

The one point of force in dev-rigor-stack-lite: everything else is discipline,
this is a program. It cannot be talked past.

Design (behavior only):
  - Decompose a task into sequential stories, persisted to a ledger (./.rigor/) -
    survives session death and context compaction; any host resumes with `status`.
  - A story can be checkpointed only after `next` activates it.
  - A `complete` checkpoint requires non-empty evidence.
  - The final story cannot complete without a verify command + result (the unit exit gate).
  - Engagement mode is pinned in the existing plan state. Continuous and release
    engagements do not close merely because the currently known queue is exhausted.

Usage:
  rigor_goals.py create --brief "..." [--mode MODE] [--terminal "..."]
                        --goal "title::objective" [--goal ...]
  rigor_goals.py add --goal "title::objective" --authorization-source "..."
  rigor_goals.py set-next --id G001 --reason "..."
  rigor_goals.py reopen --id G001 --reason "dependency recovered"
  rigor_goals.py set-mode --mode MODE --authorization-source "..."
  rigor_goals.py next                 # activate the next story + print a handoff
  rigor_goals.py checkpoint --id G001 --status STATUS --evidence "..."
                 [--verify-cmd "<command run>" --verify-evidence "<result>"]  # required on the final story
  rigor_goals.py status
  rigor_goals.py close --evidence "..." --verify-cmd "..." --verify-evidence "..."
State directory: ./.rigor/ (run from the repo root)

Adapted from fablize's goal engine (fivetaku/fablize, MIT) - see NOTICE.md.
"""
import argparse
import json
import os
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

# Two output rules (gate findings, 0.2.1/0.2.2):
# 1. The tool's OWN strings are pure ASCII - no glyphs to garble on cp1252.
# 2. USER text (--brief/--goal/--evidence) passes through verbatim, so streams
#    must degrade (errors="replace") instead of crashing when a legacy console
#    cannot encode it. Without this, an emoji in a brief is a hard crash.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

DIR = Path(".rigor")
GOALS = DIR / "goals.json"
LEDGER = DIR / "ledger.jsonl"
LOCK = DIR / "mutation.lock"
SCHEMA_VERSION = 2
MODES = ("single_unit", "finite_program", "continuous_development", "release_workflow")
RELEASE_INTENTS = ("none", "candidate", "publish")
RESOLVED_STATUSES = {"complete", "cancelled", "out_of_scope"}
CHECKPOINT_STATUSES = (
    "complete", "failed", "blocked", "waiting_external",
    "blocked_owner", "cancelled", "out_of_scope",
)
REOPENABLE_STATUSES = {
    "failed", "blocked", "waiting_external", "blocked_owner", "cancelled", "out_of_scope",
}
DEFAULT_TERMINAL = "all declared goals complete with a final verification receipt"


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def mutation_lock():
    """Serialize CLI processes so read-modify-write commands cannot lose updates."""
    DIR.mkdir(exist_ok=True)
    try:
        descriptor = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        sys.exit("rigor-goals: another rigor-goals process holds .rigor/mutation.lock. "
                 "Wait for it; if it crashed, verify no process is active before removing the stale lock.")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"pid": os.getpid(), "created": now()}))
            handle.flush()
            os.fsync(handle.fileno())
        yield
    finally:
        try:
            LOCK.unlink()
        except FileNotFoundError:
            pass


def log(event, **kw):
    DIR.mkdir(exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now(), "event": event, **kw}, ensure_ascii=False) + "\n")


def validate_plan(plan):
    """Reject malformed state before a command can reinterpret or mutate it."""
    if not isinstance(plan, dict):
        sys.exit("rigor-goals: invalid plan state: root must be an object.")
    if not isinstance(plan.get("plan_id"), str) or not plan["plan_id"].strip():
        sys.exit("rigor-goals: invalid plan state: plan_id must be non-empty.")
    goals = plan.get("goals")
    if not isinstance(goals, list) or not goals:
        sys.exit("rigor-goals: invalid plan state: goals must be a non-empty list.")
    seen = set()
    active = 0
    valid_statuses = {"pending", "in_progress", *CHECKPOINT_STATUSES}
    for goal in goals:
        if not isinstance(goal, dict):
            sys.exit("rigor-goals: invalid plan state: every goal must be an object.")
        goal_id = goal.get("id")
        if not (isinstance(goal_id, str) and goal_id.startswith("G")
                and goal_id[1:].isdigit()):
            sys.exit(f"rigor-goals: invalid plan state: malformed goal id {goal_id!r}.")
        if goal_id in seen:
            sys.exit(f"rigor-goals: invalid plan state: duplicate goal id {goal_id}.")
        seen.add(goal_id)
        if not isinstance(goal.get("title"), str) or not isinstance(goal.get("objective"), str):
            sys.exit(f"rigor-goals: invalid plan state: {goal_id} title/objective must be strings.")
        if goal.get("status") not in valid_statuses:
            sys.exit(f"rigor-goals: invalid plan state: {goal_id} has unsupported status {goal.get('status')!r}.")
        if goal.get("status") == "complete" and not (
                isinstance(goal.get("evidence"), str) and goal["evidence"].strip()):
            sys.exit(f"rigor-goals: invalid plan state: complete goal {goal_id} requires evidence.")
        active += goal.get("status") == "in_progress"
    if active > 1:
        sys.exit("rigor-goals: invalid plan state: multiple goals are in_progress.")
    if plan.get("mode") not in MODES:
        sys.exit(f"rigor-goals: unsupported engagement mode: {plan.get('mode')!r}.")
    if plan.get("release_intent") not in RELEASE_INTENTS:
        sys.exit(f"rigor-goals: invalid plan state: unsupported release intent {plan.get('release_intent')!r}.")
    if plan["mode"] == "release_workflow" and plan["release_intent"] == "none":
        sys.exit("rigor-goals: invalid plan state: release_workflow requires candidate or publish intent.")
    if plan["mode"] != "release_workflow" and plan["release_intent"] != "none":
        sys.exit("rigor-goals: invalid plan state: release intent applies only to release_workflow.")
    if not isinstance(plan.get("terminal_predicate"), str) or not plan["terminal_predicate"].strip():
        sys.exit("rigor-goals: invalid plan state: terminal_predicate must be non-empty.")
    if not isinstance(plan.get("closed"), bool):
        sys.exit("rigor-goals: invalid plan state: closed must be boolean.")
    if plan["closed"]:
        unresolved_goals = [goal for goal in goals if goal["status"] not in RESOLVED_STATUSES]
        if unresolved_goals:
            sys.exit("rigor-goals: invalid plan state: closed engagement has unresolved goals.")
        if plan.get("closure_kind") == "final_checkpoint":
            receipt = plan.get("last_verification")
            if not isinstance(receipt, dict) or not all(
                    isinstance(receipt.get(key), str) and receipt[key].strip()
                    for key in ("command", "evidence")):
                sys.exit("rigor-goals: invalid plan state: final checkpoint closure lacks verification receipt.")
        elif plan.get("closure_kind") == "explicit_close":
            receipt = plan.get("closure")
            if not isinstance(receipt, dict) or not all(
                    isinstance(receipt.get(key), str) and receipt[key].strip()
                    for key in ("terminal_predicate", "evidence", "verify_cmd", "verify_evidence")):
                sys.exit("rigor-goals: invalid plan state: explicit closure lacks structural receipt.")
            if receipt["terminal_predicate"] != plan["terminal_predicate"]:
                sys.exit("rigor-goals: invalid plan state: closure terminal does not match the plan.")
            if receipt.get("release_intent") != plan["release_intent"]:
                sys.exit("rigor-goals: invalid plan state: closure release intent does not match the plan.")
            if plan["mode"] in ("continuous_development", "release_workflow") and not (
                    isinstance(receipt.get("authorization_source"), str)
                    and receipt["authorization_source"].strip()):
                sys.exit("rigor-goals: invalid plan state: continuing closure lacks authorization receipt.")
        else:
            sys.exit("rigor-goals: invalid plan state: closed engagement lacks a supported closure_kind.")
    selected = plan.get("next_goal_id")
    if selected is not None:
        target = next((goal for goal in goals if goal["id"] == selected), None)
        if target is None or target["status"] != "pending":
            sys.exit("rigor-goals: invalid plan state: next_goal_id must identify a pending goal.")


def load():
    if not GOALS.exists():
        sys.exit("rigor-goals: no plan - run `create` from the repo root first.")
    try:
        plan = json.loads(GOALS.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        sys.exit(f"rigor-goals: cannot read plan state: {exc}")
    if not isinstance(plan, dict):
        sys.exit("rigor-goals: invalid plan state: root must be an object.")
    schema = plan.get("schema_version", 1)
    if schema == 1:
        plan.update({
            "schema_version": SCHEMA_VERSION,
            "mode": "finite_program",
            "terminal_predicate": DEFAULT_TERMINAL,
            "release_intent": "none",
            "next_goal_id": None,
            "next_action": None,
            "closed": False,
        })
        save(plan)
        log("plan_migrated", plan_id=plan.get("plan_id"), from_schema=1,
            to_schema=SCHEMA_VERSION, mode="finite_program")
    elif schema != SCHEMA_VERSION:
        sys.exit(f"rigor-goals: unsupported plan schema {schema}; expected {SCHEMA_VERSION}.")
    validate_plan(plan)
    return plan


def save(plan):
    validate_plan(plan)
    DIR.mkdir(exist_ok=True)
    tmp = DIR / f".goals.{uuid.uuid4().hex}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(plan, ensure_ascii=False, indent=1))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(tmp), str(GOALS))
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def parse_goal(spec):
    if "::" not in spec:
        sys.exit(f"rigor-goals: --goal format is 'title::objective' - invalid: {spec}")
    title, objective = spec.split("::", 1)
    title = title.strip()
    objective = objective.strip()
    if not title or not objective:
        sys.exit(f"rigor-goals: goal title and objective must be non-empty: {spec}")
    return title, objective


def unresolved(plan, exclude_id=None):
    return [g for g in plan["goals"]
            if g["id"] != exclude_id and g["status"] not in RESOLVED_STATUSES]


def is_final_active(plan, goal):
    return not unresolved(plan, exclude_id=goal["id"])


def cmd_create(a):
    replaced = None
    if GOALS.exists():
        if not a.force:
            sys.exit("rigor-goals: a plan already exists. Check it with `status`, or replace it with --force.")
        # Replacement must be loud: a silently vanished plan is how a job's
        # history gets rewritten without anyone noticing. (Gate incident, 0.2.2.)
        try:
            old = json.loads(GOALS.read_text(encoding="utf-8"))
            if not isinstance(old, dict) or not isinstance(old.get("goals"), list) or any(
                    not isinstance(goal, dict) for goal in old["goals"]):
                sys.exit("rigor-goals: invalid plan state: refusing --force replacement of malformed goals.")
            replaced = old
            if (old.get("mode") in ("continuous_development", "release_workflow")
                    and not a.authorization_source.strip()):
                sys.exit(f"rigor-goals: replacing active {old.get('mode')} requires --authorization-source.")
            done = sum(1 for g in old.get("goals", []) if g.get("status") == "complete")
            print(f"rigor-goals: REPLACING plan '{old.get('brief', '?')}' "
                  f"(plan {old.get('plan_id', 'unknown')}, {done}/{len(old.get('goals', []))} complete, "
                  f"created {old.get('created', '?')})")
        except (json.JSONDecodeError, OSError) as exc:
            sys.exit(f"rigor-goals: invalid plan state: refusing --force replacement: {exc}")
    if a.mode in ("continuous_development", "release_workflow") and not a.terminal.strip():
        sys.exit(f"rigor-goals: {a.mode} requires an explicit --terminal predicate.")
    if a.mode == "release_workflow" and a.release_intent == "none":
        sys.exit("rigor-goals: release_workflow requires --release-intent candidate or publish.")
    if a.mode != "release_workflow" and a.release_intent != "none":
        sys.exit("rigor-goals: --release-intent applies only to release_workflow.")
    terminal = a.terminal.strip() or DEFAULT_TERMINAL
    goals = []
    for i, spec in enumerate(a.goal, 1):
        title, obj = parse_goal(spec)
        goals.append({"id": f"G{i:03d}", "title": title, "objective": obj,
                      "status": "pending", "evidence": None})
    if not goals:
        sys.exit("rigor-goals: at least one --goal is required.")
    plan_id = uuid.uuid4().hex[:12]
    plan = {
        "schema_version": SCHEMA_VERSION,
        "plan_id": plan_id,
        "brief": a.brief,
        "created": now(),
        "mode": a.mode,
        "terminal_predicate": terminal,
        "release_intent": a.release_intent,
        "next_goal_id": None,
        "next_action": None,
        "closed": False,
        "goals": goals,
    }
    save(plan)
    log("plan_created", plan_id=plan_id, brief=a.brief, count=len(goals),
        mode=a.mode, terminal_predicate=terminal, release_intent=a.release_intent)
    if replaced is not None:
        log("plan_replaced", plan_id=plan_id, old_plan_id=replaced.get("plan_id"),
            new_plan_id=plan_id, old_mode=replaced.get("mode", "legacy"), new_mode=a.mode,
            authorization_source=a.authorization_source.strip() or None)
    print(f"rigor-goals: plan created - {len(goals)} stories; mode {a.mode} "
          "(state in ./.rigor/ - consider gitignoring it)")
    for g in goals:
        print(f"  {g['id']} {g['title']}: {g['objective']}")


def plan_wrapup(plan):
    """Honest queue/plan line with mode-aware completion semantics."""
    done = sum(1 for g in plan["goals"] if g["status"] == "complete")
    failed = sum(1 for g in plan["goals"] if g["status"] == "failed")
    blocked = sum(1 for g in plan["goals"] if g["status"] == "blocked")
    total = len(plan["goals"])
    if plan.get("closed") and plan.get("closure_kind") == "final_checkpoint":
        if done == total:
            return "rigor-goals: all stories complete (gate satisfied)"
        return (f"rigor-goals: all stories resolved (gate satisfied) - {done}/{total} complete; "
                "authorized cancelled/out_of_scope outcomes are recorded in the ledger")
    if plan.get("closed"):
        return "rigor-goals: engagement closed with a recorded structural evidence receipt"
    if (done == total and plan["mode"] in ("single_unit", "finite_program")
            and plan["terminal_predicate"] == DEFAULT_TERMINAL):
        return "rigor-goals: all stories complete (gate satisfied)"
    remaining = unresolved(plan)
    if not remaining and plan["mode"] in ("continuous_development", "release_workflow"):
        return ("rigor-goals: current queue exhausted but engagement remains ACTIVE - NOT COMPLETE. "
                "Reconcile authorized scope, use `add`/`set-next`, or record an authorized `close`.")
    if not remaining:
        return ("rigor-goals: current queue resolved but the custom terminal requires explicit close - "
                "record structural terminal evidence with `close`.")
    waiting = sum(1 for g in plan["goals"] if g["status"] == "waiting_external")
    owner = sum(1 for g in plan["goals"] if g["status"] == "blocked_owner")
    return (f"rigor-goals: no stories remaining but plan is NOT complete - "
            f"{done}/{total} complete, {failed} failed, {blocked} blocked, "
            f"{waiting} waiting_external, {owner} blocked_owner. "
            "Resolve or re-plan before claiming done.")


def cmd_add(a):
    plan = load()
    if plan.get("closed"):
        sys.exit("rigor-goals: cannot add to a closed engagement.")
    source = a.authorization_source.strip()
    if not source:
        sys.exit("rigor-goals: add requires non-empty --authorization-source.")
    title, objective = parse_goal(a.goal)
    highest = max((int(g["id"][1:]) for g in plan["goals"]), default=0)
    goal = {"id": f"G{highest + 1:03d}", "title": title, "objective": objective,
            "status": "pending", "evidence": None}
    plan["goals"].append(goal)
    save(plan)
    log("goal_added", plan_id=plan.get("plan_id"), id=goal["id"], title=title,
        objective=objective, authorization_source=source)
    print(f"rigor-goals: ADDING {goal['id']} {title} (authorization: {source})")


def cmd_set_next(a):
    plan = load()
    if plan.get("closed"):
        sys.exit("rigor-goals: cannot select next work in a closed engagement.")
    goal = next((g for g in plan["goals"] if g["id"] == a.id), None)
    if not goal:
        sys.exit(f"rigor-goals: {a.id} not found.")
    if goal["status"] != "pending":
        sys.exit(f"rigor-goals: {a.id} is not pending ({goal['status']}).")
    reason = a.reason.strip()
    if not reason:
        sys.exit("rigor-goals: set-next requires non-empty --reason.")
    plan["next_goal_id"] = goal["id"]
    plan["next_action"] = f"activate {goal['id']} {goal['title']}"
    save(plan)
    log("next_goal_set", plan_id=plan.get("plan_id"), id=goal["id"],
        reason=reason, next_action=plan["next_action"])
    print(f"rigor-goals: SET-NEXT {goal['id']} {goal['title']} (reason: {reason})")


def cmd_reopen(a):
    plan = load()
    if plan.get("closed"):
        sys.exit("rigor-goals: cannot reopen work in a closed engagement.")
    goal = next((g for g in plan["goals"] if g["id"] == a.id), None)
    if not goal:
        sys.exit(f"rigor-goals: {a.id} not found.")
    if goal["status"] not in REOPENABLE_STATUSES:
        sys.exit(f"rigor-goals: {a.id} cannot be reopened from {goal['status']}.")
    reason = a.reason.strip()
    if not reason:
        sys.exit("rigor-goals: reopen requires non-empty --reason.")
    authorization_source = a.authorization_source.strip()
    if goal["status"] in ("cancelled", "out_of_scope") and not authorization_source:
        sys.exit(f"rigor-goals: reopening {goal['status']} work requires --authorization-source.")
    previous_status = goal["status"]
    previous_evidence = goal.get("evidence")
    goal["status"] = "pending"
    goal["evidence"] = None
    save(plan)
    log("goal_reopened", plan_id=plan.get("plan_id"), id=goal["id"],
        previous_status=previous_status, previous_evidence=previous_evidence,
        reason=reason, authorization_source=authorization_source or None)
    print(f"rigor-goals: REOPENING {goal['id']} from {previous_status} (reason: {reason})")


def cmd_set_mode(a):
    plan = load()
    if plan.get("closed"):
        sys.exit("rigor-goals: cannot change mode on a closed engagement.")
    source = a.authorization_source.strip()
    if not source:
        sys.exit("rigor-goals: set-mode requires --authorization-source.")
    terminal = a.terminal.strip()
    if a.mode in ("continuous_development", "release_workflow") and not terminal:
        sys.exit(f"rigor-goals: {a.mode} requires an explicit --terminal predicate.")
    if a.mode == "release_workflow" and a.release_intent == "none":
        sys.exit("rigor-goals: release_workflow requires --release-intent candidate or publish.")
    old_mode = plan["mode"]
    old_terminal = plan["terminal_predicate"]
    old_intent = plan["release_intent"]
    plan["mode"] = a.mode
    plan["terminal_predicate"] = terminal or DEFAULT_TERMINAL
    plan["release_intent"] = a.release_intent if a.mode == "release_workflow" else "none"
    save(plan)
    log("mode_changed", plan_id=plan.get("plan_id"), from_mode=old_mode,
        to_mode=plan["mode"], from_terminal=old_terminal,
        to_terminal=plan["terminal_predicate"], from_release_intent=old_intent,
        to_release_intent=plan["release_intent"], authorization_source=source)
    print(f"rigor-goals: SET-MODE {old_mode} -> {plan['mode']} (authorization: {source})")


def cmd_next(a):
    plan = load()
    if plan.get("closed"):
        print(plan_wrapup(plan)); return
    active = [g for g in plan["goals"] if g["status"] == "in_progress"]
    if active:
        g = active[0]
    else:
        pending = [g for g in plan["goals"] if g["status"] == "pending"]
        if not pending:
            print(plan_wrapup(plan)); return
        selected = plan.get("next_goal_id")
        g = next((item for item in pending if item["id"] == selected), pending[0])
        g["status"] = "in_progress"
        if selected == g["id"]:
            plan["next_goal_id"] = None
            plan["next_action"] = None
        save(plan)
        log("story_started", plan_id=plan.get("plan_id"), id=g["id"], title=g["title"])
    is_final = is_final_active(plan, g)
    print(f"=== rigor-goals handoff - {g['id']} {g['title']}")
    print(f"Objective: {g['objective']}")
    print("Rule: work this story only. Produce evidence as you go.")
    if is_final:
        print("** Final story - the complete checkpoint requires --verify-cmd and --verify-evidence (exit gate).")
    print(f"On completion: rigor_goals.py checkpoint --id {g['id']} --status complete --evidence \"<evidence>\""
          + (" --verify-cmd \"<command>\" --verify-evidence \"<result>\"" if is_final else ""))


def cmd_checkpoint(a):
    plan = load()
    g = next((x for x in plan["goals"] if x["id"] == a.id), None)
    if not g:
        sys.exit(f"rigor-goals: {a.id} not found.")
    if g["status"] != "in_progress":
        sys.exit(f"rigor-goals: {a.id} is not active ({g['status']}) - activate it with `next` first.")
    final_active = is_final_active(plan, g)
    authorization_source = a.authorization_source.strip()
    if a.status == "complete":
        if not (a.evidence and a.evidence.strip()):
            sys.exit("rigor-goals: a complete checkpoint requires non-empty --evidence.")
        if final_active:
            if not (a.verify_cmd and a.verify_cmd.strip() and a.verify_evidence and a.verify_evidence.strip()):
                sys.exit("rigor-goals: the final story cannot complete without --verify-cmd and --verify-evidence (exit gate).")
    if a.status in ("cancelled", "out_of_scope"):
        if not (a.evidence and a.evidence.strip()):
            sys.exit(f"rigor-goals: {a.status} requires non-empty --evidence.")
        if not authorization_source:
            sys.exit(f"rigor-goals: {a.status} requires --authorization-source.")
    g["status"] = a.status
    g["evidence"] = a.evidence
    if a.status == "complete" and final_active:
        plan["last_verification"] = {
            "command": a.verify_cmd,
            "evidence": a.verify_evidence,
            "recorded_at": now(),
        }
        if (plan["mode"] in ("single_unit", "finite_program")
                and plan["terminal_predicate"] == DEFAULT_TERMINAL):
            plan["closed"] = True
            plan["closed_at"] = now()
            plan["closure_kind"] = "final_checkpoint"
    save(plan)
    log("checkpoint", plan_id=plan.get("plan_id"), id=g["id"], status=a.status, evidence=a.evidence,
        verify_cmd=a.verify_cmd, verify_evidence=a.verify_evidence,
        authorization_source=authorization_source or None)
    print(f"rigor-goals: {g['id']} -> {a.status}")
    remaining = unresolved(plan)
    actionable = [item for item in remaining if item["status"] in ("pending", "in_progress")]
    print(plan_wrapup(plan) if not actionable
          else f"rigor-goals: {len(remaining)} stories left - continue with `next`.")


def cmd_close(a):
    plan = load()
    if plan.get("closed"):
        print(plan_wrapup(plan)); return
    remaining = unresolved(plan)
    if remaining:
        ids = ", ".join(f"{g['id']}:{g['status']}" for g in remaining)
        sys.exit(f"rigor-goals: cannot close with unresolved work: {ids}.")
    if not (a.evidence.strip() and a.verify_cmd.strip() and a.verify_evidence.strip()):
        sys.exit("rigor-goals: close requires --evidence, --verify-cmd, and --verify-evidence receipts.")
    source = a.authorization_source.strip()
    if plan["mode"] in ("continuous_development", "release_workflow") and not source:
        sys.exit(f"rigor-goals: closing {plan['mode']} requires --authorization-source.")
    plan["closed"] = True
    plan["closed_at"] = now()
    plan["closure_kind"] = "explicit_close"
    plan["closure"] = {
        "terminal_predicate": plan["terminal_predicate"],
        "release_intent": plan["release_intent"],
        "evidence": a.evidence,
        "verify_cmd": a.verify_cmd,
        "verify_evidence": a.verify_evidence,
        "authorization_source": source or None,
    }
    save(plan)
    log("plan_closed", plan_id=plan.get("plan_id"), mode=plan["mode"],
        terminal_predicate=plan["terminal_predicate"], release_intent=plan["release_intent"],
        evidence=a.evidence, verify_cmd=a.verify_cmd,
        verify_evidence=a.verify_evidence, authorization_source=source or None)
    print("rigor-goals: engagement closure receipt recorded; this records workflow "
          "completeness and does not verify truth or execute the command.")


def cmd_status(a):
    plan = load()
    done = sum(1 for g in plan["goals"] if g["status"] == "complete")
    state = "CLOSED" if plan.get("closed") else "ACTIVE"
    print(f"rigor-goals: {done}/{len(plan['goals'])} complete - {plan['brief']} "
          f"(plan {plan.get('plan_id', 'unknown')}, mode {plan['mode']}, {state})")
    print(f"  Terminal: {plan['terminal_predicate']}")
    if plan["mode"] == "release_workflow":
        print(f"  Release intent: {plan['release_intent']}")
    mark = {"complete": "+", "in_progress": ">", "pending": ".", "failed": "x",
            "blocked": "#", "waiting_external": "w", "blocked_owner": "o",
            "cancelled": "c", "out_of_scope": "-"}
    for g in plan["goals"]:
        print(f"  {mark.get(g['status'],'?')} {g['id']} [{g['status']}] {g['title']}")


def main():
    p = argparse.ArgumentParser(prog="rigor-goals")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create"); c.add_argument("--brief", required=True)
    c.add_argument("--goal", action="append", default=[]); c.add_argument("--force", action="store_true")
    c.add_argument("--authorization-source", default="")
    c.add_argument("--mode", choices=MODES, default="finite_program")
    c.add_argument("--terminal", default="")
    c.add_argument("--release-intent", choices=RELEASE_INTENTS, default="none")
    add = sub.add_parser("add"); add.add_argument("--goal", required=True)
    add.add_argument("--authorization-source", default="")
    select = sub.add_parser("set-next"); select.add_argument("--id", required=True)
    select.add_argument("--reason", required=True)
    reopen = sub.add_parser("reopen"); reopen.add_argument("--id", required=True)
    reopen.add_argument("--reason", default="")
    reopen.add_argument("--authorization-source", default="")
    mode = sub.add_parser("set-mode"); mode.add_argument("--mode", choices=MODES, required=True)
    mode.add_argument("--terminal", default="")
    mode.add_argument("--release-intent", choices=RELEASE_INTENTS, default="none")
    mode.add_argument("--authorization-source", default="")
    sub.add_parser("next")
    k = sub.add_parser("checkpoint"); k.add_argument("--id", required=True)
    k.add_argument("--status", required=True, choices=CHECKPOINT_STATUSES)
    k.add_argument("--evidence", default=""); k.add_argument("--verify-cmd", dest="verify_cmd", default="")
    k.add_argument("--verify-evidence", dest="verify_evidence", default="")
    k.add_argument("--authorization-source", default="")
    sub.add_parser("status")
    close = sub.add_parser("close"); close.add_argument("--evidence", default="")
    close.add_argument("--verify-cmd", dest="verify_cmd", default="")
    close.add_argument("--verify-evidence", dest="verify_evidence", default="")
    close.add_argument("--authorization-source", default="")
    a = p.parse_args()
    with mutation_lock():
        {"create": cmd_create, "add": cmd_add, "set-next": cmd_set_next,
         "reopen": cmd_reopen, "set-mode": cmd_set_mode,
         "next": cmd_next, "checkpoint": cmd_checkpoint, "status": cmd_status,
         "close": cmd_close}[a.cmd](a)


if __name__ == "__main__":
    main()
