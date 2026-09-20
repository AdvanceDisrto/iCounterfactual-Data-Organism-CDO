"""CEX-001: deterministic, synthetic research only; no real model quality claims."""
from dataclasses import dataclass
from hashlib import sha256
import json
import math


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True)
class Action:
    name: str
    cost: int
    gain: float
    verified: bool = True

    def __post_init__(self):
        if not self.name or not isinstance(self.cost, int) or isinstance(self.cost, bool) or self.cost <= 0:
            raise ValueError("action requires name and positive integer cost")
        if not math.isfinite(self.gain) or self.gain < 0:
            raise ValueError("gain must be finite and nonnegative")


class Exchange:
    """Choose maximal predicted marginal quality per unit cost, subject to verification.

    Synthetic gains are estimates supplied by the caller, not observed model quality.
    The independent verifier is called after each execution and at final stopping.
    """

    def __init__(self, budget=100, min_gain_per_unit=0.001):
        if not isinstance(budget, int) or isinstance(budget, bool) or budget <= 0:
            raise ValueError("budget must be a positive integer")
        if not math.isfinite(min_gain_per_unit) or min_gain_per_unit < 0:
            raise ValueError("invalid stopping threshold")
        self.budget = budget
        self.threshold = min_gain_per_unit

    def run(self, actions, executor=None, verifier=None):
        actions = tuple(actions)
        if len({a.name for a in actions}) != len(actions):
            raise ValueError("action names must be unique")
        executor = executor or (lambda action: action.gain)
        verifier = verifier or (lambda action, observed: action.verified and math.isfinite(observed) and observed >= 0)
        remaining = list(actions)
        spent = 0
        quality = 0.0
        receipts = []
        previous = "0" * 64
        reason = None
        while True:
            feasible = [a for a in remaining if a.cost <= self.budget - spent]
            if not feasible:
                reason = "budget_or_exhausted"
                break
            # Counterfactuals are predictions of each feasible *next* action, not executed outcomes.
            counterfactuals = [{"action": a.name, "cost": a.cost, "predicted_gain": a.gain,
                                "predicted_quality": quality + a.gain, "gain_per_unit": a.gain / a.cost}
                               for a in sorted(feasible, key=lambda a: a.name)]
            chosen = max(feasible, key=lambda a: (a.gain / a.cost, a.gain, -a.cost, a.name))
            if chosen.gain / chosen.cost <= self.threshold:
                reason = "marginal_gain_below_threshold"
                break
            observed = float(executor(chosen))
            if not math.isfinite(observed) or observed < 0:
                raise ValueError("executor returned invalid observed quality gain")
            passed = bool(verifier(chosen, observed))
            spent += chosen.cost  # Charge actual executed action even if verification fails.
            if passed:
                quality += observed
            record = {"sequence": len(receipts), "action": chosen.name, "cost": chosen.cost,
                      "spent": spent, "remaining": self.budget - spent,
                      "predicted_gain": chosen.gain, "observed_gain": observed,
                      "verified": passed, "credited_quality": quality,
                      "counterfactuals": counterfactuals, "previous_hash": previous}
            record["hash"] = sha256(canonical(record).encode()).hexdigest()
            previous = record["hash"]
            receipts.append(record)
            remaining.remove(chosen)
            if not passed:
                reason = "verification_failed"
                break
        # Stopping is verified by recomputing the rule, not by trusting a model's confidence.
        feasible = [a for a in remaining if a.cost <= self.budget - spent]
        valid_stop = (reason == "verification_failed" or not feasible or
                      max(a.gain / a.cost for a in feasible) <= self.threshold)
        if not valid_stop:
            raise AssertionError("unverified stop")
        return {"budget": self.budget, "spent": spent, "quality": quality,
                "stop_reason": reason, "stop_verified": valid_stop,
                "unspent": self.budget - spent, "receipts": receipts,
                "final_hash": previous}


def verify_receipts(result):
    """Verify hash chain and arithmetic; does not attest to real-world execution."""
    if result["budget"] <= 0 or result["spent"] > result["budget"]:
        return False
    previous = "0" * 64
    spent = 0
    quality = 0.0
    for i, record in enumerate(result["receipts"]):
        data = dict(record)
        digest = data.pop("hash", None)
        if digest != sha256(canonical(data).encode()).hexdigest():
            return False
        if data["sequence"] != i or data["previous_hash"] != previous or data["cost"] <= 0:
            return False
        spent += data["cost"]
        if data["verified"]:
            quality += data["observed_gain"]
        if data["spent"] != spent or data["remaining"] != result["budget"] - spent or not math.isclose(data["credited_quality"], quality):
            return False
        previous = digest
    return (previous == result["final_hash"] and spent == result["spent"] and
            result["unspent"] == result["budget"] - spent and
            math.isclose(quality, result["quality"]) and result["stop_verified"] is True)
