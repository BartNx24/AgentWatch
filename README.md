# AgentWatch

Choose a business-file request and compare how permissions, task scope and selective approval affect its execution. The current prototype uses real, published invoice records and explains the exact rule behind each decision.

## Run the current version

Open this folder in VS Code. In Terminal > New Terminal, run:

```powershell
py AgentWatch.py --ui
```

Keep the terminal open. Choose a scenario, review its source data, select approval where applicable and click Run scenario. Expand Why this decision? for the requested and allowed values. Inspect the files links to the execution record and captured working files. On macOS/Linux, use python3 instead of py. Python 3.10 or newer is required; no extra packages or API keys are needed.

```powershell
py AgentWatch.py --test
```

The current version is v0.6.1. A completed assistant-generated example is in example_results/report.html. New runs are saved in results/.

## Browse all versions

Nine numbered releases, v0.1.0 through v0.6.1, are preserved in versions/. Two intermediate v0.5.0 snapshots are in revisions/. VERSION_HISTORY.md describes their changes; VERSIONS.json records their hashes and release-tag commits.

Every numbered release also has a Git tag. For example, `git show v0.3.0:AgentWatch.py` displays that retained source. The initial v0.1.0 prototype has multiple software files; its main runner is run_simulation.py.

These are saved earlier versions imported into Git on 19 November 2026. Git commit dates record the import, while original version dates and original run times remain in the archive records. Import commits use the archive-importer identity. Software and documentation were AI-assisted; individual group contributions should be evidenced through actual subsequent work.

## Project records

- [Version history](VERSION_HISTORY.md)
- [Current user guide](docs/CURRENT_GUIDE.md)
- [Implementation decisions](IMPLEMENTATION_RECORD.md)
- [Scenario list](SCENARIOS.md)
- [Data sources and credit](DATA_SOURCES.md)
- [Original screenshots](evidence/screenshots/README.md)
- [GitHub upload instructions](GITHUB_UPLOAD.md)

The prototype is a controlled authorization experiment. Tasks and rules are configured, actions use isolated working copies and approvals follow the selected response. It compares the combined effect of task checks and approval and does not isolate approval's effect alone.
