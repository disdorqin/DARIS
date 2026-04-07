---
title: Dashboard
---


ARISE includes two dashboard modes for monitoring your skill library and trajectory history: a terminal TUI (requires no browser) and a web UI.

## Terminal TUI

```bash
arise dashboard ./arise_skills
arise dashboard ./arise_skills --trajectories-path ./arise_trajectories
```

Requires `arise-ai[dashboard]` (installs `rich`).

The TUI displays:

**Skill Library panel (left)**
- Library version number
- Active / Testing / Deprecated skill counts
- Table of active skills: name, success rate, invocation count, origin (manual/synthesized/refined/patched), skill ID
- Top performers highlighted

**Trajectory History panel (right)**
- Rolling list of recent episodes: task (truncated), reward score, step count, timestamp
- Success/failure color-coded by reward threshold (≥0.5 = success)
- Recent success rate across last 50 episodes

**Evolution History panel (bottom)**
- One row per evolution cycle: timestamp, gaps detected, tools synthesized, tools promoted, rejected tools, duration
- Tools promoted shown in green; rejected tools with rejection reason

The TUI refreshes every few seconds. Press `q` or `Ctrl-C` to quit.

## Web UI

```bash
arise dashboard ./arise_skills --web
arise dashboard ./arise_skills --web --port 9000
arise dashboard ./arise_skills --web --trajectories-path ./arise_trajectories
```

Requires `arise-ai[dashboard]` (installs `rich` + `fastapi`). Opens a browser tab at `http://localhost:8501` (or the port you specify).

The web UI provides the same information as the TUI but in a browser, with:

**Overview tab**
- Library stats card: version, active/testing/deprecated counts, average success rate
- Skills table: sortable by success rate, invocations, or name; click a row to expand the implementation and test suite

**Trajectories tab**
- Paginated list of recent trajectories
- Filter by reward threshold (successes only, failures only, or all)
- Click a trajectory to expand and see each step: tool called, inputs, output or error, latency

**Evolution tab**
- Timeline of evolution cycles
- For each cycle: which gaps were detected, which tools were synthesized vs. rejected, total duration and cost

## Programmatic Access

The same data is available from Python without the dashboard:

```python
# Library stats
print(arise.stats)
# {
#   "active": 4,
#   "testing": 1,
#   "deprecated": 2,
#   "total_skills": 7,
#   "library_version": 8,
#   "avg_success_rate": 0.847,
#   "recent_success_rate": 0.9,
#   "top_performers": [...],
#   "episodes_run": 42,
# }

# Last evolution report
report = arise.last_evolution
print(report.tools_promoted)   # ["compute_sha256"]
print(report.tools_rejected)   # [{"name": "fetch_api", "reason": "sandbox failure"}]
print(report.duration_ms)      # 45000

# Full history
for r in arise.evolution_history:
    print(r.timestamp, r.tools_promoted)

# Active skills
for skill in arise.skills:
    print(skill.name, skill.success_rate, skill.invocation_count)
```

:::tip[CLI alternatives]
For quick checks without starting the full dashboard:

```bash
arise status ./arise_skills       # library summary
arise skills ./arise_skills       # active skills table
arise inspect ./arise_skills <id> # full skill detail
```
:::
