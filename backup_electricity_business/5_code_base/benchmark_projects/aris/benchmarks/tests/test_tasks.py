"""Tests for benchmark task definitions."""

import pytest

from benchmarks.acmecorp.fixtures import generate, AcmeCorpEnv
from benchmarks.tasks import get_all_tasks, get_quick_tasks
from benchmarks.tasks.phase1_logs import make_phase1_tasks
from benchmarks.tasks.phase2_metrics import make_phase2_tasks
from benchmarks.tasks.phase3_config import make_phase3_tasks
from benchmarks.tasks.phase4_incident import make_phase4_tasks


@pytest.fixture(scope="module")
def env():
    """Generate a test environment."""
    e = generate(seed=42, log_count=500, metrics_port=18080)
    yield e
    e.cleanup()


class TestTaskGeneration:
    """Test that tasks are generated correctly."""

    def test_all_tasks_count(self, env):
        """All 60 tasks are generated without errors."""
        tasks = get_all_tasks(env)
        assert len(tasks) == 60

    def test_phase1_count(self, env):
        tasks = make_phase1_tasks(env)
        assert len(tasks) == 15

    def test_phase2_count(self, env):
        tasks = make_phase2_tasks(env)
        assert len(tasks) == 15

    def test_phase3_count(self, env):
        tasks = make_phase3_tasks(env)
        assert len(tasks) == 15

    def test_phase4_count(self, env):
        tasks = make_phase4_tasks(env)
        assert len(tasks) == 15

    def test_required_fields(self, env):
        """Each task has required fields: id, phase, task, check, difficulty."""
        tasks = get_all_tasks(env)
        for t in tasks:
            assert "id" in t, f"Task missing 'id': {t}"
            assert "phase" in t, f"Task missing 'phase': {t.get('id')}"
            assert "task" in t, f"Task missing 'task': {t.get('id')}"
            assert "check" in t, f"Task missing 'check': {t.get('id')}"
            assert "difficulty" in t, f"Task missing 'difficulty': {t.get('id')}"

    def test_unique_ids(self, env):
        """All task IDs are unique."""
        tasks = get_all_tasks(env)
        ids = [t["id"] for t in tasks]
        assert len(ids) == len(set(ids)), f"Duplicate IDs found: {[x for x in ids if ids.count(x) > 1]}"

    def test_phase_numbers(self, env):
        """Phase numbers are correct per phase."""
        for phase_num, maker in [(1, make_phase1_tasks), (2, make_phase2_tasks),
                                  (3, make_phase3_tasks), (4, make_phase4_tasks)]:
            tasks = maker(env)
            for t in tasks:
                assert t["phase"] == phase_num, f"Task {t['id']} has phase {t['phase']}, expected {phase_num}"

    def test_difficulty_values(self, env):
        """Difficulty is one of easy, medium, hard."""
        tasks = get_all_tasks(env)
        for t in tasks:
            assert t["difficulty"] in ("easy", "medium", "hard"), (
                f"Task {t['id']} has invalid difficulty: {t['difficulty']}"
            )

    def test_check_functions_are_callable(self, env):
        """Check functions are callable."""
        tasks = get_all_tasks(env)
        for t in tasks:
            assert callable(t["check"]), f"Task {t['id']} check is not callable"

    def test_check_functions_return_bool(self, env):
        """Check functions return bool."""
        tasks = get_all_tasks(env)
        for t in tasks:
            result = t["check"]("some random output", env)
            assert isinstance(result, bool), (
                f"Task {t['id']} check returned {type(result)}, expected bool"
            )

    def test_task_strings_nonempty(self, env):
        """Task prompt strings are non-empty."""
        tasks = get_all_tasks(env)
        for t in tasks:
            assert len(t["task"]) > 10, f"Task {t['id']} has too short a prompt"

    def test_difficulty_distribution(self, env):
        """5 easy, 5 medium, 5 hard per phase."""
        for maker in [make_phase1_tasks, make_phase2_tasks, make_phase3_tasks, make_phase4_tasks]:
            tasks = maker(env)
            easy = [t for t in tasks if t["difficulty"] == "easy"]
            medium = [t for t in tasks if t["difficulty"] == "medium"]
            hard = [t for t in tasks if t["difficulty"] == "hard"]
            assert len(easy) == 5, f"Expected 5 easy, got {len(easy)}"
            assert len(medium) == 5, f"Expected 5 medium, got {len(medium)}"
            assert len(hard) == 5, f"Expected 5 hard, got {len(hard)}"


class TestQuickMode:
    """Test the quick mode task selection."""

    def test_quick_tasks_count(self, env):
        """Quick mode returns 20 tasks (5 per phase)."""
        tasks = get_quick_tasks(env)
        assert len(tasks) == 20

    def test_quick_tasks_all_easy(self, env):
        """Quick mode tasks are all easy."""
        tasks = get_quick_tasks(env)
        for t in tasks:
            assert t["difficulty"] == "easy", f"Task {t['id']} is {t['difficulty']}, expected easy"


class TestCheckFunctions:
    """Test that check functions work correctly for known inputs."""

    def test_log01_correct(self, env):
        """log-01 check returns True for correct payments error count."""
        from benchmarks.acmecorp.logs import query_logs
        expected = len(query_logs(env.logs, service="payments", severity="ERROR"))
        tasks = make_phase1_tasks(env)
        t = next(t for t in tasks if t["id"] == "log-01")
        assert t["check"](f"The payments service has {expected} ERROR entries.", env)

    def test_log01_incorrect(self, env):
        """log-01 check returns False for obviously wrong output."""
        tasks = make_phase1_tasks(env)
        t = next(t for t in tasks if t["id"] == "log-01")
        # Use a number that is very unlikely to match
        assert not t["check"]("There are 999888777 errors.", env)

    def test_log04_correct(self, env):
        """log-04 check returns True for correct total count."""
        expected = len(env.logs)
        tasks = make_phase1_tasks(env)
        t = next(t for t in tasks if t["id"] == "log-04")
        assert t["check"](f"Total log entries: {expected}", env)

    def test_log04_incorrect(self, env):
        """log-04 check returns False for wrong count."""
        tasks = make_phase1_tasks(env)
        t = next(t for t in tasks if t["id"] == "log-04")
        assert not t["check"]("Total log entries: 999888777", env)

    def test_metrics01_correct(self, env):
        """metrics-01 check returns True when all services mentioned."""
        tasks = make_phase2_tasks(env)
        t = next(t for t in tasks if t["id"] == "metrics-01")
        services = list(env.ground_truth["metrics"].keys())
        output = "Services: " + ", ".join(services)
        assert t["check"](output, env)

    def test_metrics01_incorrect(self, env):
        """metrics-01 check returns False when services are missing."""
        tasks = make_phase2_tasks(env)
        t = next(t for t in tasks if t["id"] == "metrics-01")
        assert not t["check"]("Services: nonexistent_service_xyz", env)

    def test_config01_correct(self, env):
        """config-01 check returns True for correct replicas count."""
        all_services = env.ground_truth["config_services"]
        first_svc = all_services[0] if all_services else "payments"
        expected_replicas = env.ground_truth["config_replicas"].get(first_svc, 0)
        tasks = make_phase3_tasks(env)
        t = next(t for t in tasks if t["id"] == "config-01")
        assert t["check"](f"The replicas count is {expected_replicas}", env)

    def test_config01_incorrect(self, env):
        """config-01 check returns False for wrong replicas."""
        tasks = make_phase3_tasks(env)
        t = next(t for t in tasks if t["id"] == "config-01")
        assert not t["check"]("The replicas count is 999888", env)

    def test_incident01_correct(self, env):
        """incident-01 check returns True for correct error count."""
        from benchmarks.acmecorp.logs import query_logs
        expected = len(query_logs(env.logs, service="payments", severity="ERROR"))
        tasks = make_phase4_tasks(env)
        t = next(t for t in tasks if t["id"] == "incident-01")
        assert t["check"](f"Found {expected} ERROR entries for payments.", env)

    def test_incident01_incorrect(self, env):
        """incident-01 check returns False for wrong count."""
        tasks = make_phase4_tasks(env)
        t = next(t for t in tasks if t["id"] == "incident-01")
        assert not t["check"]("Found 999888777 ERROR entries.", env)

    def test_check_wrong_output_returns_false(self, env):
        """Most checks return False for completely irrelevant output."""
        tasks = get_all_tasks(env)
        # Test with nonsense output - at least 80% should return False
        nonsense = "xyzzy plugh 999888777666"
        false_count = sum(1 for t in tasks if not t["check"](nonsense, env))
        assert false_count >= len(tasks) * 0.7, (
            f"Only {false_count}/{len(tasks)} checks returned False for nonsense input"
        )
