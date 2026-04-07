# DARIS v3 Execution Validation Report

- request: daris_v3_full_run
- status: success
- rounds: 1
- start: 2026-04-03T10:38:44.451679
- end: 2026-04-03T10:58:41.206657

## Mandatory Checks
- cleanup_triggered: True
- benchmark_integration_triggered: True
- skills_library_updated: True
- git_commit_records: 4

## Non-blocking failures
- OpenClaw.clone | attempts=3 | non_blocking=True | error=clone_failed
- EvoScientist.clone | attempts=3 | non_blocking=True | error=clone_failed
- SciPhi.core_logic | attempts=3 | non_blocking=True | error=probe_not_found
- PaperAgent.clone | attempts=3 | non_blocking=True | error=clone_failed
- ARIS.clone | attempts=3 | non_blocking=True | error=clone_failed
- Aider.clone | attempts=3 | non_blocking=True | error=clone_failed
- ML-Agent-Research.clone | attempts=3 | non_blocking=True | error=clone_failed
- AutoResearch.clone | attempts=3 | non_blocking=True | error=clone_failed
- Zotero.clone | attempts=3 | non_blocking=True | error=clone_failed

## Round Summary
### Round 1
- literature_json: 3_literature_workflow\structured_summary\auto_literature_20260403_105232.json
- reading_summary: 3_literature_workflow\structured_summary\agent_reading_round1.md
- innovation: 4_research_hypothesis\innovation_round1.md
- innovation_review: 4_research_hypothesis\review_report\innovation_review_round1.md
- full_test_log: 6_experiment_execution\tuning_log\auto_full_pipeline_stdout.log
