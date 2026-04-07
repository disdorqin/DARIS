from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RegistryEntry:
    name: str
    description: str
    implementation: str
    test_suite: str
    version: int = 1
    author: str = ""
    downloads: int = 0
    avg_success_rate: float = 0.0
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
