import unittest
from dataclasses import replace
from cdo_core import CDO, ConflictError


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.g = CDO()
        self.g.add("temperature", 65, evidence="sensor:1")
        self.g.add("offset", 10, evidence="calibration:1")
        self.g.add("unrelated", 42, evidence="other")
        self.g.add("adjusted", dependencies=["temperature", "offset"], operation="add")
        self.g.add("double", dependencies=["adjusted", "offset"], operation="mul")

    def test_preview_and_apply(self):
        original = self.g.snapshot()
        plan = self.g.plan("temperature", 85, evidence="sensor:2")
        self.assertEqual(plan.affected, ("temperature", "adjusted", "double"))
        self.assertEqual([r.new_value for r in plan.revisions], ["85", "95", "950"])
        self.assertEqual(self.g.snapshot(), original)
        result = self.g.apply(plan)
        self.assertEqual({c["id"]: c["value"] for c in result["cells"]}["double"], "950")
        self.assertEqual(result["hash"], plan.after_hash)
        self.assertEqual(next(c for c in result["cells"] if c["id"] == "unrelated"),
                         next(c for c in original["cells"] if c["id"] == "unrelated"))

    def test_stale_plan_rejected(self):
        plan = self.g.plan("temperature", 85, evidence="sensor:2")
        self.g.add("new", 1)
        with self.assertRaises(ConflictError):
            self.g.apply(plan)

    def test_tampered_plan_rejected(self):
        plan = self.g.plan("temperature", 85, evidence="sensor:2")
        with self.assertRaises(ConflictError):
            self.g.apply(replace(plan, after_hash="0" * 64))

    def test_only_changed_values_revised(self):
        plan = self.g.plan("temperature", 65, evidence="sensor:2")
        self.assertEqual([r.cell_id for r in plan.revisions], ["temperature"])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            self.g.add("bad", "NaN")
        with self.assertRaises(ValueError):
            self.g.add("cycle", dependencies=["cycle", "offset"], operation="add")
        with self.assertRaises(ValueError):
            self.g.add("overwrite", 5, dependencies=["offset", "temperature"], operation="add")
        with self.assertRaises(ValueError):
            self.g.plan("temperature", 85, evidence="")
        with self.assertRaises(ValueError):
            self.g.plan("adjusted", 85, evidence="source")
        with self.assertRaises(ValueError):
            self.g.add("divide", dependencies=["temperature", "offset"], operation="unknown")

    def test_zero_divisor_rolls_back(self):
        self.g.add("ratio", dependencies=["temperature", "offset"], operation="div")
        original = self.g.snapshot()
        with self.assertRaises(ValueError):
            self.g.plan("offset", 0, evidence="test")
        self.assertEqual(self.g.snapshot(), original)

    def test_deterministic_hash(self):
        first = self.g.plan("temperature", 85, evidence="sensor:2")
        second = self.g.plan("temperature", 85, evidence="sensor:2")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
