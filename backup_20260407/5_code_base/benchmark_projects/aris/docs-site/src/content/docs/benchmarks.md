---
title: Benchmarks
---


ARISE was evaluated on two proprietary-format domains where LLMs cannot rely on training data — they must synthesize tools to make progress.

Full results, figures, and the research paper are in [`benchmarks/`](https://github.com/abekek/arise/tree/main/benchmarks) and [`paper/`](https://github.com/abekek/arise/tree/main/paper).

---

## AcmeCorp — SRE Agent Onboarding

**Domain:** Site Reliability Engineering tasks at a fictional company with proprietary log formats, a base64-encoded metrics API, and internal configuration files.

**Setup:** 60 episodes across 4 phases (15 each), seed = 42. Synthesis model: gpt-4o-mini for all ARISE runs.

**Phases:**
1. Log analysis (count errors, extract services, aggregate by time)
2. Metrics API (make HTTP calls, decode proprietary base64 format)
3. Configuration (read and reason over internal config files)
4. Incident response (multi-domain composition across logs + metrics + config)

### Results

| Model | Condition | Phase 1 (Logs) | Phase 2 (Metrics) | Phase 3 (Config) | Phase 4 (Incidents) | **Overall** | Tools |
|-------|-----------|:--------------:|:-----------------:|:----------------:|:-------------------:|:-----------:|:-----:|
| **Claude Sonnet** | **ARISE** | 60% | 73% | **100%** | **80%** | **78%** | 2 |
| GPT-4o-mini | ARISE | 20% | 67% | 93% | 47% | 57% | 21 |
| GPT-4o-mini | No tools | 33% | 7% | 93% | 60% | 48% | 0 |
| GPT-4o-mini | Fixed tools | 13% | 53% | 87% | 40% | 48% | 7 |

### Key Findings

**ARISE improves both models.** GPT-4o-mini improved from 48% to 57% (+9pp). Claude Sonnet with ARISE achieved 78%.

**Agent reasoning quality matters more than tool quantity.** Claude reached 78% with just 2 tools. GPT-4o-mini needed 21 tools to reach 57%. A strong model that uses tools well outperforms a weak model with many tools.

**Self-evolved tools beat hand-written tools.** GPT-4o-mini with ARISE (57%) outperformed GPT-4o-mini with 7 carefully hand-written fixed tools (48%). Self-evolved tools are better because the synthesis prompt includes the agent's actual failure patterns — they're shaped to match how the agent thinks.

**Phase 2 proves the core thesis.** The metrics API requires decoding a proprietary base64 format — impossible without tools. ARISE-evolved tools achieved 67–73% on this phase. Without tools: 7%.

**Phase 4 shows where model quality dominates.** Incident response requires composing tools across multiple domains. Claude composed effectively (80%). GPT-4o-mini actually scored lower with tools (47%) than without (60%) — tool-calling overhead hurt more than tool access helped.

---

## DataCorp — Data Engineering

**Domain:** Data engineering tasks with proprietary data formats, transformation pipelines, and custom validation schemas.

| Model | Condition | **Overall** |
|-------|-----------|:-----------:|
| GPT-4o-mini | **ARISE** | **92%** |
| GPT-4o-mini | No tools | 50% |

ARISE improved GPT-4o-mini by **+42 percentage points** on DataCorp tasks. The domain is heavily tool-dependent — with the right tools, even a smaller model performs well.

---

## Cost Analysis

| Run | Agent calls | Synthesis calls | Estimated cost |
|-----|------------|----------------|:--------------:|
| GPT-4o-mini + ARISE | 60 | ~64 | ~$0.44 |
| GPT-4o-mini + No tools | 60 | 0 | ~$0.18 |
| GPT-4o-mini + Fixed tools | 60 | 0 | ~$0.18 |
| Claude Sonnet + ARISE | 60 | ~5 | ~$5.50 |

Each evolution cycle costs ~$0.01–0.05 with gpt-4o-mini. Claude synthesized fewer tools (only 1 evolution cycle triggered) because its stronger reasoning handled more tasks directly.

---

## Running the Benchmarks

```bash
cd benchmarks
pip install -r requirements.txt

# AcmeCorp benchmark
python run_benchmark.py --domain acmecorp --model gpt-4o-mini --seed 42

# With ARISE disabled (no-evolution baseline)
python run_benchmark.py --domain acmecorp --model gpt-4o-mini --no-evolution

# DataCorp benchmark
python run_benchmark.py --domain datacorp --model gpt-4o-mini --seed 42
```

Results are saved to `benchmarks/results/`. Figures are generated with `python benchmarks/plot_results.py`.

See [`benchmarks/README.md`](https://github.com/abekek/arise/blob/main/benchmarks/README.md) for full documentation of the benchmark tasks, evaluation methodology, and how to add new domains.

:::note[Proprietary formats]
The AcmeCorp and DataCorp benchmarks use invented proprietary formats (log schemas, API response encodings, config syntax) that do not appear in any LLM training data. This isolates the tool-synthesis benefit from memorized knowledge.
:::