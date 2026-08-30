"""
Micro-framework dei controlli: esito singolo + helper di stampa.

Ogni modulo `cNN_*.py` espone `run(ctx) -> list[Result]`. `ctx` è un dict
condiviso fra i controlli (es. il check ingestion ci lascia il percorso dei
dati generati, che il check Excel riusa).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

PASS, FAIL, WARN, SKIP = "PASS", "FAIL", "WARN", "SKIP"

_ICON = {PASS: "[ OK ]", FAIL: "[FAIL]", WARN: "[warn]", SKIP: "[skip]"}


@dataclass
class Result:
    """Esito di un singolo controllo."""
    name: str
    status: str
    detail: str = ""
    seconds: float = 0.0

    def line(self) -> str:
        t = f" ({self.seconds:.1f}s)" if self.seconds >= 0.1 else ""
        d = f" — {self.detail}" if self.detail else ""
        return f"{_ICON[self.status]} {self.name}{t}{d}"


@dataclass
class Timer:
    """Cronometro d'appoggio: `with Timer() as t: ...` poi `t.elapsed`."""
    elapsed: float = field(default=0.0)
    _t0: float = field(default=0.0, repr=False)

    def __enter__(self) -> "Timer":
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, *exc) -> bool:
        self.elapsed = time.perf_counter() - self._t0
        return False


def ok(name: str, detail: str = "", seconds: float = 0.0) -> Result:
    return Result(name, PASS, detail, seconds)


def fail(name: str, detail: str = "", seconds: float = 0.0) -> Result:
    return Result(name, FAIL, detail, seconds)


def warn(name: str, detail: str = "", seconds: float = 0.0) -> Result:
    return Result(name, WARN, detail, seconds)


def skip(name: str, detail: str = "", seconds: float = 0.0) -> Result:
    return Result(name, SKIP, detail, seconds)


def verdict(name: str, condition: bool, detail_ok: str = "",
            detail_ko: str = "", seconds: float = 0.0,
            soft: bool = False) -> Result:
    """PASS se `condition`, altrimenti FAIL (o WARN se `soft`)."""
    if condition:
        return ok(name, detail_ok, seconds)
    return (warn if soft else fail)(name, detail_ko or detail_ok, seconds)
