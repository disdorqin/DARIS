from arise.rewards.learned import LearnedReward
from arise.types import Trajectory


def make_trajectory(outcome="success"):
    return Trajectory(task="test task", outcome=outcome, steps=[])


def test_learned_reward_falls_back_before_threshold():
    lr = LearnedReward(min_examples=10)
    t = make_trajectory(outcome="success")
    reward = lr(t)
    assert reward == 1.0  # task_success fallback


def test_learned_reward_stores_feedback():
    lr = LearnedReward()
    t = make_trajectory()
    lr.add_feedback(t, 0.8)
    assert len(lr.examples) == 1


def test_learned_reward_caps_examples():
    lr = LearnedReward(max_examples=5)
    for i in range(10):
        lr.add_feedback(make_trajectory(), float(i) / 10)
    assert len(lr.examples) == 5


def test_learned_reward_persists():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        lr = LearnedReward(persist_path=d)
        lr.add_feedback(make_trajectory(), 0.9)
        # Reload
        lr2 = LearnedReward(persist_path=d)
        assert len(lr2.examples) == 1
        assert lr2.examples[0].human_score == 0.9


def test_learned_reward_uses_llm_after_threshold():
    # Mock llm_call to return "0.75"
    from unittest.mock import patch
    lr = LearnedReward(min_examples=2)
    lr.add_feedback(make_trajectory(outcome="good"), 1.0)
    lr.add_feedback(make_trajectory(outcome="Error: failed"), 0.0)
    with patch("arise.rewards.learned.llm_call", return_value="0.75"):
        reward = lr(make_trajectory())
    assert reward == 0.75


def test_learned_reward_fallback_on_llm_error():
    from unittest.mock import patch
    lr = LearnedReward(min_examples=2)
    lr.add_feedback(make_trajectory(outcome="good"), 1.0)
    lr.add_feedback(make_trajectory(outcome="bad"), 0.0)
    with patch("arise.rewards.learned.llm_call", side_effect=Exception("API error")):
        reward = lr(make_trajectory(outcome="success"))
    assert reward == 1.0  # falls back to task_success
