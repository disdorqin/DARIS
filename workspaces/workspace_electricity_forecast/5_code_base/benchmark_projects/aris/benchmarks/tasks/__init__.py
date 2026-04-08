"""Benchmark task definitions."""
from benchmarks.tasks.phase1_logs import make_phase1_tasks
from benchmarks.tasks.phase2_metrics import make_phase2_tasks
from benchmarks.tasks.phase3_config import make_phase3_tasks
from benchmarks.tasks.phase4_incident import make_phase4_tasks

def get_all_tasks(env):
    """Generate all 60 tasks for an AcmeCorpEnv."""
    return make_phase1_tasks(env) + make_phase2_tasks(env) + make_phase3_tasks(env) + make_phase4_tasks(env)

def get_quick_tasks(env):
    """Quick mode: 5 tasks per phase (20 total)."""
    tasks = get_all_tasks(env)
    return [t for t in tasks if t["difficulty"] == "easy"]
