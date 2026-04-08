from __future__ import annotations

import importlib.util
from pathlib import Path


_IMPL_PATH = Path(__file__).resolve().parent / "2_agent_system" / "aliyun_connector.py"
_SPEC = importlib.util.spec_from_file_location("_aliyun_connector_impl", _IMPL_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load aliyun connector implementation from {_IMPL_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

AliyunConnector = _MODULE.AliyunConnector
create_connector_from_env = _MODULE.create_connector_from_env