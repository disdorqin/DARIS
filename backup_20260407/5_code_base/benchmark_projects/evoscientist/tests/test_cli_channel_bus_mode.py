"""Tests for channel bus-mode thinking propagation."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from EvoScientist.cli import channel as channel_cli


@pytest.fixture(autouse=True)
def _restore_channel_globals():
    """Restore mutable module globals after each test."""
    original = {
        "_manager": channel_cli._manager,
        "_bus_loop": channel_cli._bus_loop,
        "_bus_thread": channel_cli._bus_thread,
        "_cli_agent": channel_cli._cli_agent,
        "_cli_thread_id": channel_cli._cli_thread_id,
    }
    yield
    channel_cli._manager = original["_manager"]
    channel_cli._bus_loop = original["_bus_loop"]
    channel_cli._bus_thread = original["_bus_thread"]
    channel_cli._cli_agent = original["_cli_agent"]
    channel_cli._cli_thread_id = original["_cli_thread_id"]


def test_auto_start_channel_passes_send_thinking(monkeypatch):
    captured = {}

    def _fake_start(config, agent, thread_id, *, send_thinking=None):
        captured["send_thinking"] = send_thinking
        captured["thread_id"] = thread_id
        captured["agent"] = agent

    monkeypatch.setattr(channel_cli, "_start_channels_bus_mode", _fake_start)
    monkeypatch.setattr(channel_cli, "_print_channel_panel", lambda _rows: None)

    config = SimpleNamespace(channel_enabled="telegram")
    agent = object()
    channel_cli._auto_start_channel(
        agent,
        "thread-1",
        config,
        send_thinking=False,
    )

    assert captured["send_thinking"] is False
    assert captured["thread_id"] == "thread-1"
    assert captured["agent"] is agent


def test_cmd_channel_running_path_passes_send_thinking(monkeypatch):
    import EvoScientist.config as config_mod

    captured = {}
    config = SimpleNamespace(channel_enabled="telegram")

    monkeypatch.setattr(config_mod, "load_config", lambda: config)
    monkeypatch.setattr(
        channel_cli, "_channels_is_running", lambda _channel_type=None: True
    )
    monkeypatch.setattr(channel_cli, "_channels_running_list", lambda: [])
    monkeypatch.setattr(channel_cli, "_print_channel_panel", lambda _rows: None)
    monkeypatch.setattr(
        channel_cli,
        "_add_channel_to_running_bus",
        lambda channel_type, cfg, *, send_thinking=None: captured.update(
            {
                "channel_type": channel_type,
                "config": cfg,
                "send_thinking": send_thinking,
            }
        ),
    )

    channel_cli._cmd_channel(
        "telegram",
        object(),
        "thread-1",
        send_thinking=False,
    )

    assert captured["channel_type"] == "telegram"
    assert captured["config"] is config
    assert captured["send_thinking"] is False


def test_cmd_channel_start_path_passes_send_thinking(monkeypatch):
    import EvoScientist.config as config_mod

    captured = {}
    config = SimpleNamespace(channel_enabled="telegram")

    monkeypatch.setattr(config_mod, "load_config", lambda: config)
    monkeypatch.setattr(
        channel_cli, "_channels_is_running", lambda _channel_type=None: False
    )
    monkeypatch.setattr(channel_cli, "_print_channel_panel", lambda _rows: None)
    monkeypatch.setattr(
        channel_cli,
        "_start_channels_bus_mode",
        lambda cfg, agent, thread_id, *, send_thinking=None: captured.update(
            {
                "config": cfg,
                "agent": agent,
                "thread_id": thread_id,
                "send_thinking": send_thinking,
            }
        ),
    )

    agent = object()
    channel_cli._cmd_channel(
        "",
        agent,
        "thread-1",
        send_thinking=False,
    )

    assert captured["config"] is config
    assert captured["agent"] is agent
    assert captured["thread_id"] == "thread-1"
    assert captured["send_thinking"] is False
