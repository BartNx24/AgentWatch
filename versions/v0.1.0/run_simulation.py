"""Run the AgentWatch scenario comparison and export locally inspectable evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import platform
import random
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from agentwatch import STRATEGIES, VERSION, begin_attempt, load_suite, summarize

ROOT = Path(__file__).resolve().parent


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("Use an integer of at least 1")
    return number


def nonnegative_seconds(value):
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("Use a finite nonnegative number")
    return number


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save_database(path, metadata, rows, summary):
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE runs (run_id TEXT PRIMARY KEY, metadata_json TEXT NOT NULL)")
        connection.execute("INSERT INTO runs VALUES (?, ?)", (metadata["run_id"], json.dumps(metadata)))
        connection.execute("""CREATE TABLE trials (
            trial_index INTEGER PRIMARY KEY, run_id TEXT NOT NULL, round INTEGER NOT NULL,
            scenario_id TEXT NOT NULL, strategy TEXT NOT NULL,
            initial_decision TEXT NOT NULL, approval_status TEXT NOT NULL,
            executed INTEGER NOT NULL, processing_ms REAL NOT NULL,
            simulated_wait_seconds REAL NOT NULL, record_json TEXT NOT NULL)""")
        connection.executemany("INSERT INTO trials VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
            (r["trial_index"], metadata["run_id"], r["round"], r["scenario_id"], r["strategy"],
             r["actual_initial_decision"], r["approval_status"], int(r["executed"]),
             r["measured_processing_ms"], r["simulated_approval_wait_seconds"], json.dumps(r)) for r in rows
        ])
        connection.execute("CREATE TABLE summaries (strategy TEXT PRIMARY KEY, record_json TEXT NOT NULL)")
        connection.executemany("INSERT INTO summaries VALUES (?, ?)", [(r["strategy"], json.dumps(r)) for r in summary])


def snapshot_sources(destination, suite_path):
    files = [ROOT / name for name in ["agentwatch.py", "run_simulation.py", "README.md", "CHANGELOG.md", "DECISIONS.md"]]
    files.extend(sorted((ROOT / "tests").glob("test_*.py")))
    hashes = {}
    for source in files:
        relative = source.relative_to(ROOT)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        content = source.read_bytes()
        target.write_bytes(content)
        hashes[str(relative).replace("\\", "/")] = hashlib.sha256(content).hexdigest()
    content = suite_path.read_bytes()
    target = destination / "scenarios.json"
    target.write_bytes(content)
    hashes["scenarios.json"] = hashlib.sha256(content).hexdigest()
    return hashes


def write_report(path, metadata, rows, summary):
    esc = lambda value: html.escape(str(value), quote=True)
    def percent(value):
        return "N/A" if value is None else f"{value:.1f}%"

    css = """
    :root {color-scheme:light; font-family:Segoe UI,Arial,sans-serif; color:#162332; background:#f0f3f6}
    body {margin:0} main {max-width:1200px; margin:auto; padding:30px 24px 64px}
    h1 {font-size:30px; margin:6px 0 12px} h2 {margin:30px 0 12px; font-size:22px}
    p {line-height:1.55; max-width:1000px} .meta {font-size:13px; color:#4d6173}
    .metrics {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:22px 0}
    .metric {background:white;border:1px solid #d7dfe7;border-radius:8px;padding:18px}
    .metric strong {display:block;font-size:28px;margin-bottom:5px} .metric span {font-size:14px;color:#4d6173}
    .table-wrap {overflow-x:auto;background:white;border:1px solid #d7dfe7;border-radius:6px}
    table {border-collapse:collapse;width:100%;font-size:13px} td,th {text-align:left;padding:11px 12px;border-bottom:1px solid #e4e9ef;vertical-align:top}
    th {background:#e6edf3;line-height:1.4} tr:nth-child(even) {background:#f8fafc}
    .allow {color:#086245;font-weight:600} .block {color:#9d2732;font-weight:600}
    .approval_required {color:#795000;font-weight:600} .small {font-size:12px;color:#4d6173}
    code {font-family:Consolas,monospace;font-size:12px;overflow-wrap:anywhere}
    a {color:#125da0} details {margin:7px 0} summary {cursor:pointer} .links {display:flex;flex-wrap:wrap;gap:18px}
    @media(max-width:650px) {.metrics{grid-template-columns:1fr} main{padding:20px 14px} h1{font-size:25px}}
    @media print {body{background:white}main{padding:0}.table-wrap{overflow:visible} th{background:#eee}}
    """
    pieces = ["<!doctype html><html lang='en'><head><meta charset='utf-8'>",
              "<meta name='viewport' content='width=device-width, initial-scale=1'>",
              f"<title>AgentWatch run {esc(metadata['run_id'])}</title><style>{css}</style></head><body><main>",
              "<div class='meta'>AGENTWATCH / CONTROLLED SCENARIO SIMULATION</div>",
              "<h1>Authorization strategy comparison</h1>",
              f"<p class='meta'>Version {esc(VERSION)} &middot; Run <code>{esc(metadata['run_id'])}</code><br>",
              f"Started {esc(metadata['started_at_utc'])} &middot; {metadata['rounds']} round(s) &middot; Seed {metadata['random_seed']}</p>",
              "<p>This run uses predefined action requests and fictional in-memory files. Approvals are scripted. "
              "The outputs test the declared rules in these scenarios; no live AI agent or real human response time is evaluated.</p>",
              "<div class='metrics'>",
              f"<div class='metric'><strong>{metadata['scenario_count']}</strong><span>scenarios per round</span></div>",
              f"<div class='metric'><strong>{len(rows)}</strong><span>scenario-condition runs</span></div>",
              f"<div class='metric'><strong>{sum(r['decision_matches_expectation'] for r in rows)}/{len(rows)}</strong><span>initial decisions matching the declared expectation</span></div></div>",
              "<h2>Security and task completion</h2><div class='table-wrap'><table><thead><tr>",
              "<th>Strategy</th><th>Attempts</th><th>Unauthorized blocked</th><th>Inappropriate blocked</th>"
              "<th>False positives</th><th>Legitimate tasks completed</th><th>Approval requests</th><th>Approval frequency</th></tr></thead><tbody>"]
    for s in summary:
        pieces.append("<tr>" + "".join(f"<td>{esc(x)}</td>" for x in [
            s["strategy"], s["attempts"], percent(s["unauthorized_block_rate_pct"]),
            percent(s["inappropriate_block_rate_pct"]), percent(s["false_positive_rate_pct"]),
            f"{s['legitimate_tasks_completed']}/{s['legitimate_attempts']}", s["approval_requests"], percent(s["approval_frequency_pct"]),
        ]) + "</tr>")
    pieces.append("</tbody></table></div><p class='small'>Unauthorized blocking uses technically unauthorized attempts as its denominator. "
                  "Inappropriate blocking uses technically authorized but task-inappropriate attempts. False positives are initial policy blocks "
                  "of technically authorized, task-appropriate requests. Scripted approval refusals are reported separately and reduce task completion.</p>")
    pieces.append("<h2>Measured processing and assumed approval delay</h2>"
                  f"<p>Scripted approval response: <strong>{esc(metadata['approval_response'])}</strong>. "
                  f"Assumed delay: <strong>{metadata['assumed_approval_wait_seconds']:g} seconds per request</strong>. "
                  "The program does not wait for this period. Estimated totals add this assumption to measured processing.</p>"
                  "<div class='table-wrap'><table><thead><tr><th>Strategy</th><th>Mean measured processing ms</th>"
                  "<th>Mean simulated wait seconds</th><th>Mean estimated total seconds</th><th>Scripted approval refusals</th></tr></thead><tbody>")
    for s in summary:
        pieces.append("<tr>" + "".join(f"<td>{esc(x)}</td>" for x in [s["strategy"],
            f"{s['mean_measured_processing_ms']:.5f}", f"{s['mean_simulated_wait_seconds']:.3f}",
            f"{s['mean_estimated_total_seconds']:.5f}", s["simulated_approval_denials"]]) + "</tr>")
    pieces.append("</tbody></table></div><h2>Individual trial records</h2>"
                  "<p class='small'>Use your browser's Find command to locate a scenario. Expand its identifier to inspect its task, execution outcome and event trace. CSV order retains randomized trial order.</p>"
                  "<div class='table-wrap'><table><thead><tr><th>Scenario</th><th>Strategy</th><th>Action and risk</th>"
                  "<th>Expected initial decision</th><th>Actual initial decision</th><th>Approval</th><th>Executed</th><th>Processing ms</th></tr></thead><tbody>")
    for r in sorted(rows, key=lambda r: (r["round"], STRATEGIES.index(r["strategy"]), r["scenario_id"])):
        detail = (f"<details><summary>{esc(r['scenario_id'])} / round {r['round']}</summary>"
                  f"<p>{esc(r['task'])}</p><p>{esc(r['reason'])}</p><p>{esc(r['outcome'])}</p>"
                  f"<p class='small'>Trial {r['trial_index']}<br>Resource: {esc(r['resource_id'])}<br>"
                  f"Recipient: {esc(r['recipient'])}<br>Simulated waiting seconds: {r['simulated_approval_wait_seconds']:g}<br>"
                  f"Trace: {esc(' > '.join(json.loads(r['events'])))}</p></details>")
        pieces.append(f"<tr><td>{detail}</td><td>{esc(r['strategy'])}</td>"
                      f"<td>{esc(r['action'])}<br><span class='small'>{esc(r['computed_risk'])} risk</span></td>"
                      f"<td>{esc(r['expected_initial_decision'])}</td><td class='{esc(r['actual_initial_decision'])}'>{esc(r['actual_initial_decision'])}</td>"
                      f"<td>{esc(r['approval_status'])}</td><td>{'Yes' if r['executed'] else 'No'}</td>"
                      f"<td>{r['measured_processing_ms']:.5f}</td></tr>")
    pieces.append("</tbody></table></div><h2>Retained evidence</h2><p class='links'>"
                  "<a href='trials.csv'>Trial records CSV</a><a href='summary.csv'>Summary CSV</a>"
                  "<a href='run_metadata.json'>Run metadata and source hashes</a><a href='results.sqlite'>SQLite database</a></p>"
                  "<p>The source_snapshot folder retains the code and scenarios used for this run. Preserve this entire run folder when recording development evidence.</p>"
                  "<p class='small'>Starter code was created with ChatGPT assistance. The optional operator field identifies who entered the run metadata; it does not establish code authorship. "
                  "The three conditions add permission, context and approval controls in combination; the comparison does not isolate approval's effect from context checking.</p></main></body></html>")
    path.write_text("\n".join(pieces), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=f"AgentWatch {VERSION}")
    parser.add_argument("--scenarios", type=Path, default=ROOT / "scenarios.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results", help="Parent folder for uniquely named runs")
    parser.add_argument("--rounds", type=positive_int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--approval", choices=["approve", "deny"], default="approve", help="Scripted response for all approval requests")
    parser.add_argument("--approval-seconds", type=nonnegative_seconds, default=5.0, help="Assumed delay; does not sleep")
    parser.add_argument("--operator", default="not recorded", help="Optional run operator; not an authorship claim")
    args = parser.parse_args(argv)
    resources, scenarios = load_suite(args.scenarios)
    started = datetime.now(timezone.utc)
    run_id = started.strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    folder = args.output.resolve() / run_id
    folder.mkdir(parents=True)
    hashes = snapshot_sources(folder / "source_snapshot", args.scenarios)
    rng, rows = random.Random(args.seed), []
    for round_number in range(1, args.rounds + 1):
        trials = [(scenario, strategy) for scenario in scenarios for strategy in STRATEGIES]
        rng.shuffle(trials)
        for scenario, strategy in trials:
            attempt = begin_attempt(scenario, strategy, resources)
            if attempt.approval_status == "pending":
                attempt.resolve_approval(args.approval == "approve", args.approval_seconds)
            rows.append(attempt.as_row(round_number, len(rows) + 1))
    summary = summarize(rows)
    metadata = {
        "run_id": run_id, "prototype_version": VERSION, "scenario_suite_version": "1.0",
        "started_at_utc": started.isoformat(), "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(), "platform": platform.system(),
        "operator_entered_by_user": args.operator, "rounds": args.rounds,
        "scenario_count": len(scenarios), "scenario_condition_runs": len(rows),
        "random_seed": args.seed, "strategies": list(STRATEGIES), "approval_response": args.approval,
        "assumed_approval_wait_seconds": args.approval_seconds,
        "timing_note": "Processing is measured; approval delay is an assumption, not an observed human response time.",
        "agent_mode": "Predefined action requests; no live language model",
        "provenance": "AI-assisted starter generated in ChatGPT; individual group contributions are not assigned.",
        "source_snapshot_sha256": hashes,
    }
    write_csv(folder / "trials.csv", rows)
    write_csv(folder / "summary.csv", summary)
    (folder / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    save_database(folder / "results.sqlite", metadata, rows, summary)
    write_report(folder / "report.html", metadata, rows, summary)
    matches = sum(r["decision_matches_expectation"] and r["risk_matches_expectation"] for r in rows)
    print(f"AgentWatch {VERSION} | {len(scenarios)} scenarios x 3 strategies x {args.rounds} round(s) = {len(rows)} runs")
    print(f"Initial decisions and risk labels matching expectations: {matches}/{len(rows)}")
    print("Fictional data; scripted approvals. Waiting time is assumed and is not actually waited.")
    print(f"Open report: {folder / 'report.html'}")
    print(f"Saved CSV, SQLite, metadata and source snapshot in: {folder}")
    return 0 if matches == len(rows) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, sqlite3.Error) as error:
        print(f"AgentWatch could not complete the run: {error}", file=sys.stderr)
        raise SystemExit(2)
