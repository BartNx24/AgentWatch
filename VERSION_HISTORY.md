# Retained version history

Prepared on 19 November 2026 from saved source artefacts and recorded run snapshots. Original software bytes are preserved. Git commit dates record this archive import; the dates below describe the retained versions.

| Version | Recorded version date | Development change |
| --- | --- | --- |
| [v0.1.0](versions/v0.1.0) | 2026-10-29 | Multi-file starter with 30 scenarios, tests and evidence exports. |
| [v0.2.0](versions/v0.2.0) | 2026-10-29 | Consolidate the prototype and tests into one Python file. |
| [v0.2.1](versions/v0.2.1) | 2026-10-29 | Close SQLite connections so Windows can clean up exported databases. |
| [v0.3.0](versions/v0.3.0) | 2026-10-31 | Open the exact new report and clearly identify the approval setting. |
| [v0.4.0](versions/v0.4.0) | 2026-11-10 | Add a scenario suite using published UCI Wine measurements. |
| [v0.4.1](versions/v0.4.1) | 2026-11-10 | Simplify the results into a plain-language comparison. |
| [v0.5.0](versions/v0.5.0) | 2026-11-16 | Use real invoice records and retain before-and-after file evidence. |
| [v0.6.0](versions/v0.6.0) | 2026-11-18 | Choose and run a scenario from local browser controls. |
| [v0.6.1](versions/v0.6.1) | 2026-11-18 | Explain the deciding rule and preserve the ordered rule checks. |

The source header dates v0.2.1 to 29 October; its retained run snapshot was made on 31 October. Two additional intermediate v0.5.0 snapshots are in revisions/v0.5.0, identified by source hash and original run time. VERSIONS.json records file hashes and the Git commit behind each release tag.

The v0.4.x lab dataset was an intermediate prototype. The v0.5.x and v0.6.x releases use invoice scenarios. Original run metadata is retained where an exact source-hash match was available. No raw user run has been reconstructed.

## Archive verification on 19 November 2026

These checks were run during packaging in the assistant environment on Linux. They are separate from historical runs and user-provided screenshots.

| Release or snapshot | Automated tests | Result |
| --- | --- | --- |
| 0.1.0 | 21 | Passed |
| 0.2.0 | 21 | Passed |
| 0.2.1 | 22 | Passed |
| 0.3.0 | 26 | Passed |
| 0.4.0 | 26 | Passed |
| 0.4.1 | 26 | Passed |
| 0.5.0 | 30 | Passed |
| 0.6.0 | 34 | Passed |
| 0.6.1 | 36 | Passed |
| 0.5.0 revision 950733ea0b8f | 30 | Passed |
| 0.5.0 revision 8681c0e136f8 | 26 | Passed |

Full outputs and exact commands are in evidence/import_verification/.
