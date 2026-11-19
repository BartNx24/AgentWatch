# AgentWatch Starter

Version 0.1.0 - created 29 October 2026 with ChatGPT assistance.

This is a working starting point for the AgentWatch proposal. It compares three authorization strategies across 30 fictional scenarios, five in each of six categories. One round produces 90 scenario-condition records.

The agent is simulated by predefined action requests. Technical permissions and task scope are structured inputs. The program does not interpret arbitrary natural-language instructions or call a language model. Expected decisions are stored separately in scenarios.json and are not used by the runtime policy.

## Where to create and run it

Use your Windows computer and VS Code. Keep AgentWatch in its own folder, such as C:\Users\kbart\Documents\AgentWatch_Starter.

1. Install Python 3.10 or newer from https://www.python.org/downloads/ if it is not installed.
2. Install VS Code from https://code.visualstudio.com/ if needed. Its Microsoft Python extension is useful for editing and selecting your interpreter.
3. Extract the ZIP. Open the AgentWatch_Starter folder in VS Code using File > Open Folder. You should see run_simulation.py directly inside the opened folder.
4. Open Terminal > New Terminal in VS Code.
5. Run:

    py --version

    py run_simulation.py

If Windows does not recognize py but recognizes python, use python in place of py for every command below. If neither command works, finish installing Python and reopen VS Code.

No extra packages, account, API key, hosting or internet connection are required to run this starter after Python is installed. It uses Python's standard library.

Official setup guidance: https://code.visualstudio.com/docs/python/python-tutorial and https://docs.python.org/3/using/windows.html

## What to open after a run

The terminal prints the full path to report.html. In File Explorer, open results, then the newly created run folder, then double-click report.html to view the comparison in your browser. Each run has a unique folder name, so rerunning does not overwrite earlier results.

Each run contains:

- report.html: comparison tables and expandable trial details.
- trials.csv: all 90 trial records per round, in the randomized execution order.
- summary.csv: blocking, false positives, task completion, approvals and timing summaries.
- results.sqlite: the same run and trial records in SQLite.
- run_metadata.json: UTC timestamps, prototype version, Python version, seed, assumptions and file hashes.
- source_snapshot: copies of the source code and scenario suite used for that run.

All delete, share, export and update actions change only in-memory mock records. The program writes its evidence outputs into the selected results directory.

## Run the automated checks

From the same VS Code terminal:

    py -m unittest discover -s tests -v

These tests cover the declared scenario decisions, approval grant and refusal, no execution while pending, replay prevention, resource and recipient scope, risk classification, mock-workspace isolation, result metrics and CSV/SQLite exports. They check the starter's behavior; they do not establish security against real autonomous agents.

The tests also run under pytest if you later install it for the methodology in your proposal. The standard-library command above requires no installation beyond Python.

## Try a meaningful comparison

Default run, scripted approval granted:

    py run_simulation.py --operator "Bart"

Second run, scripted approval refused:

    py run_simulation.py --approval deny --operator "Bart"

Repeated rounds with a different assumed delay:

    py run_simulation.py --rounds 3 --seed 42 --approval-seconds 10

The approval mode is a scripted response for every approval request. It is not a real person making decisions. The delay is an explicit assumption: the program adds it to estimated total time without sleeping. Processing time is measured separately. Repeated deterministic runs can characterize processing variation; they do not create new scenario coverage or justify statistical generalization.

For the default suite with all scripted approvals granted, the declared expected comparison is:

| Strategy | Unauthorized blocked | Authorized but inappropriate blocked | Legitimate tasks completed | Approval requests |
| --- | --- | --- | --- | --- |
| unrestricted | 0 of 10 | 0 of 10 | 10 of 10 | 0 |
| permissions | 10 of 10 | 0 of 10 | 10 of 10 | 0 |
| combined | 10 of 10 | 10 of 10 | 10 of 10 | 5 |

The figures above are expected behavior for this predefined suite. Inspect each actual run before reporting its results. Correct behavior in the unrestricted baseline deliberately includes execution of inappropriate mock actions.

In refusal mode, five legitimate high-risk requests remain unexecuted in the combined condition. Their refusals are recorded separately from false positives. The false-positive metric counts legitimate requests incorrectly blocked by the authorization policy before approval.

## Scenarios to inspect first

- AL01: legitimate low-risk reading of a public brochure.
- UL01: a task-appropriate read without technical permission.
- IH02: an agent asked to summarize a report tries to delete it despite having delete permission.
- AH01: a permitted, task-appropriate high-risk share needs approval.
- IH05: sharing is permitted, but the proposed recipient is outside the assigned task.

Expand the scenario identifier in the report to inspect the reason, outcome and event sequence. All addresses ending in fictional.invalid are fictitious labels; nothing is sent to them.

## Build your development evidence

This package is one initial release. It contains no earlier development history. Keep an unchanged copy as your starting reference.

Run it yourself, retain the complete results folder, and capture screenshots of actual outputs. Log your actual run date, the version shown in the report and your own work. The optional operator name is user-entered run metadata, not proof of code authorship.

For a later iteration, make a justified change, save the revised code and previous version, add or update a relevant test, and keep the results from both versions. Explain why the change was needed and which member implemented, tested or reviewed it. Use evidence_log.csv and contributions.csv as editable registers. Leave unknown contributions unassigned until confirmed.

The program's structured task rules are supplied explicitly for each scenario. A later iteration could evaluate less ideal inputs, test incorrect risk labels or task scopes, or add a FastAPI interface. Such changes need a documented evaluation plan. Human approval's additional benefit cannot be isolated by comparing permissions alone against a condition that adds both context checks and approval; see DECISIONS.md.

## Files to edit

- scenarios.json: fictional tasks, proposed actions, technical grants, task scopes, ground-truth labels and independent expected decisions. Keep five scenarios in each of the six categories for this protocol.
- agentwatch.py: policy decisions, the approval state and mock execution.
- run_simulation.py: experiment runner, evidence exports and report generation.
- tests/test_agentwatch.py: regression and integration checks.

Human-review each AI-generated scenario and rule before adopting it into your study. Record corrections and validation as your contributions. This starter supports the research proposal but is not a production authorization boundary.

## Troubleshooting

If the terminal says it cannot find run_simulation.py, open the folder containing that file and create a new terminal there.

If Python reports a version or syntax problem, check py --version. Python 3.10 or newer is required.

If a run reports a decision mismatch, inspect trials.csv before changing expected labels. Determine whether the policy or the expectation is wrong, document the reason and add a test for the corrected behavior.
