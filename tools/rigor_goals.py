#!/usr/bin/env python3
"""rigor-goals - a self-contained, stdlib-only multi-story loop with a verification exit gate.

The one point of force in dev-rigor-stack-lite: everything else is discipline,
this is a program. It cannot be talked past.

Design (behavior only):
  - Decompose a task into sequential stories, persisted to a ledger (./.rigor/) -
    survives session death and context compaction; any host resumes with `status`.
  - A story can be checkpointed only after `next` activates it.
  - A `complete` checkpoint requires non-empty evidence.
  - The final story cannot complete without a verify command + result (the exit gate).

Usage:
  rigor_goals.py create --brief "..." --goal "title::objective" [--goal ...]
  rigor_goals.py next                 # activate the next story + print a handoff
  rigor_goals.py checkpoint --id G001 --status complete|failed|blocked --evidence "..."
                 [--verify-cmd "<command run>" --verify-evidence "<result>"]  # required on the final story
  rigor_goals.py status
State directory: ./.rigor/ (run from the repo root)

Adapted from fablize's goal engine (fivetaku/fablize, MIT) - see NOTICE.md.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Output is deliberately pure ASCII: stock Windows consoles default to cp1252
# and turn any fancier glyph into mojibake or a crash. Plain text works
# everywhere the tool does. (Gate finding, 0.2.1.)

DIR = Path(".rigor")
GOALS = DIR / "goals.json"
LEDGER = DIR / "ledger.jsonl"


def now():
    return datetime.now(timezone.utc).isoformat()


def log(event, **kw):
    DIR.mkdir(exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now(), "event": event, **kw}, ensure_ascii=False) + "\n")


def load():
    if not GOALS.exists():
        sys.exit("rigor-goals: no plan - run `create` from the repo root first.")
    return json.loads(GOALS.read_text(encoding="utf-8"))


def save(plan):
    DIR.mkdir(exist_ok=True)
    GOALS.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_create(a):
    if GOALS.exists() and not a.force:
        sys.exit("rigor-goals: a plan already exists. Check it with `status`, or replace it with --force.")
    goals = []
    for i, g in enumerate(a.goal, 1):
        if "::" not in g:
            sys.exit(f"rigor-goals: --goal format is 'title::objective' - invalid: {g}")
        title, obj = g.split("::", 1)
        goals.append({"id": f"G{i:03d}", "title": title.strip(), "objective": obj.strip(),
                      "status": "pending", "evidence": None})
    if not goals:
        sys.exit("rigor-goals: at least one --goal is required.")
    save({"brief": a.brief, "created": now(), "goals": goals})
    log("plan_created", brief=a.brief, count=len(goals))
    print(f"rigor-goals: plan created - {len(goals)} stories (state in ./.rigor/ - consider gitignoring it)")
    for g in goals:
        print(f"  {g['id']} {g['title']}: {g['objective']}")


def plan_wrapup(plan):
    """Honest end-of-plan line: 'complete' only when every story completed."""
    done = sum(1 for g in plan["goals"] if g["status"] == "complete")
    failed = sum(1 for g in plan["goals"] if g["status"] == "failed")
    blocked = sum(1 for g in plan["goals"] if g["status"] == "blocked")
    total = len(plan["goals"])
    if done == total:
        return "rigor-goals: all stories complete (gate satisfied)"
    return (f"rigor-goals: no stories remaining but plan is NOT complete - "
            f"{done}/{total} complete, {failed} failed, {blocked} blocked. "
            "Resolve or re-plan before claiming done.")


def cmd_next(a):
    plan = load()
    active = [g for g in plan["goals"] if g["status"] == "in_progress"]
    if active:
        g = active[0]
    else:
        pending = [g for g in plan["goals"] if g["status"] == "pending"]
        if not pending:
            print(plan_wrapup(plan)); return
        g = pending[0]
        g["status"] = "in_progress"
        save(plan); log("story_started", id=g["id"], title=g["title"])
    is_final = g["id"] == plan["goals"][-1]["id"]
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
    if a.status == "complete":
        if not (a.evidence and a.evidence.strip()):
            sys.exit("rigor-goals: a complete checkpoint requires non-empty --evidence.")
        if g["id"] == plan["goals"][-1]["id"]:
            if not (a.verify_cmd and a.verify_cmd.strip() and a.verify_evidence and a.verify_evidence.strip()):
                sys.exit("rigor-goals: the final story cannot complete without --verify-cmd and --verify-evidence (exit gate).")
    g["status"] = a.status
    g["evidence"] = a.evidence
    save(plan)
    log("checkpoint", id=g["id"], status=a.status, evidence=a.evidence,
        verify_cmd=a.verify_cmd, verify_evidence=a.verify_evidence)
    print(f"rigor-goals: {g['id']} -> {a.status}")
    remaining = [x for x in plan["goals"] if x["status"] in ("pending", "in_progress")]
    print(plan_wrapup(plan) if not remaining else f"rigor-goals: {len(remaining)} stories left - continue with `next`.")


def cmd_status(a):
    plan = load()
    done = sum(1 for g in plan["goals"] if g["status"] == "complete")
    print(f"rigor-goals: {done}/{len(plan['goals'])} complete - {plan['brief']}")
    mark = {"complete": "+", "in_progress": ">", "pending": ".", "failed": "x", "blocked": "#"}
    for g in plan["goals"]:
        print(f"  {mark.get(g['status'],'?')} {g['id']} [{g['status']}] {g['title']}")


def main():
    p = argparse.ArgumentParser(prog="rigor-goals")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create"); c.add_argument("--brief", required=True)
    c.add_argument("--goal", action="append", default=[]); c.add_argument("--force", action="store_true")
    sub.add_parser("next")
    k = sub.add_parser("checkpoint"); k.add_argument("--id", required=True)
    k.add_argument("--status", required=True, choices=["complete", "failed", "blocked"])
    k.add_argument("--evidence", default=""); k.add_argument("--verify-cmd", dest="verify_cmd", default="")
    k.add_argument("--verify-evidence", dest="verify_evidence", default="")
    sub.add_parser("status")
    a = p.parse_args()
    {"create": cmd_create, "next": cmd_next, "checkpoint": cmd_checkpoint, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    main()
