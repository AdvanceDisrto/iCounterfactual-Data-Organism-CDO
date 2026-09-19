"""Deterministic, dependency-aware counterfactual data engine.

Expressions are a deliberately limited DSL; no eval, shell, network or arbitrary
Python execution. Repair is a preview until an explicit version-checked apply.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from typing import Any, Mapping
import json
import operator
import threading


class CycleError(ValueError):
    """A dependency cycle was detected."""


class ConflictError(RuntimeError):
    """The graph changed after a repair was planned."""


OPS = {"add": operator.add, "sub": operator.sub, "mul": operator.mul,
       "div": operator.truediv, "min": min, "max": max}


def number(value: Any) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("expected a finite numeric value")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("invalid numeric value") from exc
    if not result.is_finite():
        raise ValueError("nonfinite numeric value")
    return result


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def digest(value: Any) -> str:
    return sha256(canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Cell:
    id: str
    value: str
    evidence: str = ""
    dependencies: tuple[str, ...] = ()
    operation: str | None = None
    revision: int = 1
    fingerprint: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "value": self.value, "evidence": self.evidence,
                "dependencies": list(self.dependencies), "operation": self.operation,
                "revision": self.revision, "fingerprint": self.fingerprint}


@dataclass(frozen=True)
class Revision:
    cell_id: str
    old_value: str
    new_value: str
    old_revision: int
    new_revision: int

    def as_dict(self) -> dict[str, Any]:
        return vars(self).copy()


@dataclass(frozen=True)
class RepairPlan:
    base_version: int
    target: str
    replacement: str
    evidence: str
    affected: tuple[str, ...]
    revisions: tuple[Revision, ...]
    before_hash: str
    after_hash: str

    def as_dict(self) -> dict[str, Any]:
        return {"base_version": self.base_version, "target": self.target,
                "replacement": self.replacement, "evidence": self.evidence,
                "affected": list(self.affected),
                "revisions": [r.as_dict() for r in self.revisions],
                "before_hash": self.before_hash, "after_hash": self.after_hash}


class CDO:
    """In-memory proof-of-concept with deterministic lineage and optimistic commits.

    Supports numeric source cells and derived operations, not arbitrary facts or
    automatically generated semantic dependencies. Production requires persistence,
    authentication and domain-specific verifiers.
    """

    def __init__(self) -> None:
        self._cells: dict[str, Cell] = {}
        self._version = 0
        self._lock = threading.RLock()

    @property
    def version(self) -> int:
        with self._lock:
            return self._version

    def _hash(self, cells: Mapping[str, Cell]) -> str:
        return digest({k: cells[k].as_dict() for k in sorted(cells)})

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {"version": self._version, "hash": self._hash(self._cells),
                    "cells": [self._cells[k].as_dict() for k in sorted(self._cells)]}

    def _evaluate(self, operation: str, dependencies: tuple[str, ...], cells: Mapping[str, Cell]) -> str:
        if operation not in OPS:
            raise ValueError("unsupported operation")
        if len(dependencies) != 2:
            raise ValueError("derived cells require exactly two dependencies")
        values = [number(cells[key].value) for key in dependencies]
        if operation == "div" and values[1] == 0:
            raise ValueError("division by zero")
        result = OPS[operation](*values)
        if not result.is_finite():
            raise ValueError("nonfinite result")
        return str(result)

    def add(self, cell_id: str, value: Any = None, *, evidence: str = "",
            dependencies: tuple[str, ...] | list[str] = (), operation: str | None = None) -> Cell:
        with self._lock:
            if not isinstance(cell_id, str) or not cell_id or len(cell_id) > 128:
                raise ValueError("cell id must be 1-128 characters")
            if cell_id in self._cells:
                raise ValueError("duplicate cell id")
            if not isinstance(evidence, str):
                raise ValueError("evidence must be text")
            deps = tuple(dependencies)
            if any(not isinstance(d, str) or d not in self._cells for d in deps):
                raise ValueError("dependencies must exist before the derived cell")
            if len(set(deps)) != len(deps):
                raise ValueError("duplicate dependencies")
            if operation is None:
                if deps:
                    raise ValueError("source cells cannot have dependencies")
                result = str(number(value))
            else:
                if value is not None:
                    raise ValueError("derived value must be computed, not supplied")
                result = self._evaluate(operation, deps, self._cells)
            fp = digest({"id": cell_id, "value": result, "evidence": evidence,
                         "dependencies": deps, "operation": operation, "revision": 1})
            cell = Cell(cell_id, result, evidence, deps, operation, 1, fp)
            self._cells[cell_id] = cell
            self._version += 1
            return cell

    def _affected(self, target: str) -> tuple[str, ...]:
        if target not in self._cells:
            raise KeyError(target)
        # add() accepts existing dependencies only, so insertion order is topological.
        # Unaffected parents are valid dependencies and must not block propagation.
        affected = {target}
        ordered = [target]
        for key, cell in self._cells.items():
            if key != target and any(parent in affected for parent in cell.dependencies):
                affected.add(key)
                ordered.append(key)
        return tuple(ordered)

    def plan(self, cell_id: str, replacement: Any, *, evidence: str) -> RepairPlan:
        with self._lock:
            if not isinstance(evidence, str) or not evidence.strip():
                raise ValueError("replacement requires a nonempty evidence reference")
            if cell_id not in self._cells:
                raise KeyError(cell_id)
            if self._cells[cell_id].operation is not None:
                raise ValueError("only source cells can be corrected")
            value = str(number(replacement))
            before = self._hash(self._cells)
            staged = self._cells.copy()
            affected = self._affected(cell_id)
            revisions: list[Revision] = []
            for key in affected:
                previous = staged[key]
                next_value = value if key == cell_id else self._evaluate(previous.operation, previous.dependencies, staged)
                if next_value != previous.value or (key == cell_id and evidence != previous.evidence):
                    updated_revision = previous.revision + 1
                    next_evidence = evidence if key == cell_id else previous.evidence
                    fingerprint = digest({"id": key, "value": next_value, "evidence": next_evidence,
                                          "dependencies": previous.dependencies, "operation": previous.operation,
                                          "revision": updated_revision})
                    staged[key] = Cell(key, next_value, next_evidence, previous.dependencies,
                                       previous.operation, updated_revision, fingerprint)
                    revisions.append(Revision(key, previous.value, next_value,
                                              previous.revision, updated_revision))
            return RepairPlan(self._version, cell_id, value, evidence, affected,
                              tuple(revisions), before, self._hash(staged))

    def apply(self, plan: RepairPlan) -> dict[str, Any]:
        with self._lock:
            if self._version != plan.base_version or self._hash(self._cells) != plan.before_hash:
                raise ConflictError("graph changed since repair was planned")
            verified = self.plan(plan.target, plan.replacement, evidence=plan.evidence)
            if verified != plan:
                raise ConflictError("repair proposal failed deterministic verification")
            staged = self._cells.copy()
            for revision in plan.revisions:
                previous = staged[revision.cell_id]
                next_evidence = plan.evidence if revision.cell_id == plan.target else previous.evidence
                staged[revision.cell_id] = Cell(previous.id, revision.new_value, next_evidence,
                                                 previous.dependencies, previous.operation,
                                                 revision.new_revision,
                                                 digest({"id": previous.id, "value": revision.new_value,
                                                         "evidence": next_evidence, "dependencies": previous.dependencies,
                                                         "operation": previous.operation,
                                                         "revision": revision.new_revision}))
            if self._hash(staged) != plan.after_hash:
                raise ConflictError("postcondition hash mismatch")
            self._cells = staged
            self._version += 1
            return self.snapshot()
