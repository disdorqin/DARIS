from __future__ import annotations

import pytest

from arise.llm_router import LLMRouter, ModelStats


# --- ModelStats ---

def test_model_stats_initial_success_rate():
    stats = ModelStats()
    assert stats.success_rate == 0.0


def test_model_stats_success_rate_calculation():
    stats = ModelStats(attempts=4, successes=3)
    assert stats.success_rate == pytest.approx(0.75)


def test_model_stats_full_success():
    stats = ModelStats(attempts=10, successes=10)
    assert stats.success_rate == 1.0


def test_model_stats_zero_attempts_no_division_error():
    stats = ModelStats(attempts=0, successes=0)
    assert stats.success_rate == 0.0


# --- LLMRouter: routing ---

def test_router_routes_by_task_type():
    router = LLMRouter({"gap_detection": "gpt-4o-mini", "synthesis": "gpt-4o"})
    assert router.get_model("gap_detection") == "gpt-4o-mini"
    assert router.get_model("synthesis") == "gpt-4o"


def test_router_falls_back_to_default():
    router = LLMRouter({"synthesis": "gpt-4o"}, default="gpt-4o-mini")
    assert router.get_model("refinement") == "gpt-4o-mini"


def test_router_default_is_gpt4o_mini_when_not_specified():
    router = LLMRouter({})
    assert router.get_model("anything") == "gpt-4o-mini"


def test_router_empty_routes_uses_default():
    router = LLMRouter(routes=None, default="claude-3-haiku")
    assert router.get_model("synthesis") == "claude-3-haiku"


def test_router_exact_route_takes_priority_over_default():
    router = LLMRouter({"synthesis": "gpt-4o"}, default="gpt-4o-mini")
    assert router.get_model("synthesis") == "gpt-4o"


# --- LLMRouter: recording stats ---

def test_router_tracks_success():
    router = LLMRouter({})
    router.record("synthesis", "gpt-4o", success=True)
    router.record("synthesis", "gpt-4o", success=False)
    stats = router.get_stats("synthesis", "gpt-4o")
    assert stats["attempts"] == 2
    assert stats["successes"] == 1
    assert stats["success_rate"] == pytest.approx(0.5)


def test_router_tracks_multiple_models_independently():
    router = LLMRouter({})
    router.record("synthesis", "gpt-4o", success=True)
    router.record("synthesis", "gpt-4o", success=True)
    router.record("synthesis", "gpt-4o-mini", success=False)
    assert router.get_stats("synthesis", "gpt-4o")["success_rate"] == 1.0
    assert router.get_stats("synthesis", "gpt-4o-mini")["success_rate"] == 0.0


def test_router_tracks_multiple_task_types_independently():
    router = LLMRouter({})
    router.record("synthesis", "gpt-4o", success=True)
    router.record("gap_detection", "gpt-4o-mini", success=False)
    assert router.get_stats("synthesis", "gpt-4o")["attempts"] == 1
    assert router.get_stats("gap_detection", "gpt-4o-mini")["attempts"] == 1


def test_router_get_stats_for_unseen_model_returns_zeroes():
    router = LLMRouter({})
    stats = router.get_stats("synthesis", "nonexistent-model")
    assert stats["attempts"] == 0
    assert stats["successes"] == 0
    assert stats["success_rate"] == 0.0


def test_router_get_stats_for_unseen_task_returns_zeroes():
    router = LLMRouter({})
    stats = router.get_stats("unknown_task", "gpt-4o")
    assert stats["attempts"] == 0


# --- LLMRouter: auto_select ---

def test_router_auto_select():
    router = LLMRouter({}, auto_select=True)
    for _ in range(10):
        router.record("synthesis", "gpt-4o", success=True)
    for _ in range(10):
        router.record("synthesis", "gpt-4o-mini", success=False)
    assert router.get_model("synthesis") == "gpt-4o"


def test_router_auto_select_requires_minimum_5_attempts():
    router = LLMRouter({"synthesis": "gpt-4o-mini"}, auto_select=True)
    # Only 4 attempts — not enough to auto-select
    for _ in range(4):
        router.record("synthesis", "gpt-4o", success=True)
    # Should fall back to route
    assert router.get_model("synthesis") == "gpt-4o-mini"


def test_router_auto_select_picks_best_after_threshold():
    router = LLMRouter({}, default="gpt-4o-mini", auto_select=True)
    # gpt-4o: 8/10 successes
    for i in range(10):
        router.record("synthesis", "gpt-4o", success=(i < 8))
    # gpt-4o-mini: 6/10 successes
    for i in range(10):
        router.record("synthesis", "gpt-4o-mini", success=(i < 6))
    assert router.get_model("synthesis") == "gpt-4o"


def test_router_auto_select_disabled_uses_routes():
    router = LLMRouter({"synthesis": "gpt-4o-mini"}, auto_select=False)
    for _ in range(10):
        router.record("synthesis", "gpt-4o", success=True)
    # auto_select is off, should use route
    assert router.get_model("synthesis") == "gpt-4o-mini"


def test_router_auto_select_falls_back_to_route_when_no_stats():
    router = LLMRouter({"synthesis": "gpt-4o"}, default="gpt-4o-mini", auto_select=True)
    # No stats recorded — best_model returns None, falls through to route
    assert router.get_model("synthesis") == "gpt-4o"


def test_router_auto_select_falls_back_to_default_when_no_route_and_no_stats():
    router = LLMRouter({}, default="claude-3-haiku", auto_select=True)
    assert router.get_model("synthesis") == "claude-3-haiku"


# --- LLMRouter: edge cases ---

def test_router_record_increments_correctly_across_many_calls():
    router = LLMRouter({})
    for i in range(100):
        router.record("synthesis", "gpt-4o", success=(i % 2 == 0))
    stats = router.get_stats("synthesis", "gpt-4o")
    assert stats["attempts"] == 100
    assert stats["successes"] == 50
    assert stats["success_rate"] == pytest.approx(0.5)


def test_router_all_task_types_route_correctly():
    routes = {
        "gap_detection": "gpt-4o-mini",
        "synthesis": "gpt-4o",
        "refinement": "gpt-4o",
        "adversarial": "gpt-4o-mini",
        "test_generation": "gpt-4o-mini",
    }
    router = LLMRouter(routes, default="gpt-4o-mini")
    for task_type, expected_model in routes.items():
        assert router.get_model(task_type) == expected_model
