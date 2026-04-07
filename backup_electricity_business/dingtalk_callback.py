from __future__ import annotations

import importlib.util
from pathlib import Path


_IMPL_PATH = Path(__file__).resolve().parent / "2_agent_system" / "dingtalk_callback.py"
_SPEC = importlib.util.spec_from_file_location("_dingtalk_callback_impl", _IMPL_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load dingtalk callback implementation from {_IMPL_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

DingTalkCallbackHandler = _MODULE.DingTalkCallbackHandler
DingTalkCallbackServer = _MODULE.DingTalkCallbackServer
create_callback_server = _MODULE.create_callback_server
start_callback_server = _MODULE.start_callback_server
stop_callback_server = _MODULE.stop_callback_server