"""
Unit tests for the optimization engine wrapper around rules.resolve_rules().
Run from repo root or backend/:
  cd backend && PYTHONPATH=. python -m unittest tests.test_optimization_engine -v
"""

from __future__ import annotations

import unittest

from app.core.optimization_engine import generate_reasoning, optimize_configuration


class TestOptimizeConfiguration(unittest.TestCase):
    def test_case1_coding_on_m3_with_plenty_of_ram(self):
        """16GB RAM, battery 80%, coding workload → coder model + larger context."""
        hardware = {
            "device": "MacBook Air M3",
            "cpu": "Apple M3",
            "cores": 8,
            "ram_gb": 16,
        }
        system = {
            "battery_pct": 80,
            "charging": False,
            "available_ram_gb": 12,
            "thermal": "nominal",
            "swap_usage_high": False,
        }

        result = optimize_configuration(
            hardware, system, workload="coding", mode="automatic"
        )

        self.assertEqual(result["model"], "qwen2.5-coder:7b")
        self.assertEqual(result["quant"], "Q4_K_M")
        self.assertEqual(result["context_length"], 16384)
        self.assertIn("reasoning", result)
        self.assertTrue(len(result["reasoning"]) > 0)
        # Reasoning should mention coding / model / quant in some form
        joined = " ".join(result["reasoning"]).lower()
        self.assertIn("coding", joined)
        self.assertIn("q4_k_m", joined)

    def test_case2_low_battery_unplugged(self):
        """Battery < 20% and not charging → battery_saver, small model, fewer threads."""
        hardware = {
            "device": "MacBook Air M3",
            "cpu": "Apple M3",
            "cores": 8,
            "ram_gb": 16,
        }
        system = {
            "battery_pct": 15,
            "charging": False,
            "available_ram_gb": 8,
            "thermal": "nominal",
            "swap_usage_high": False,
        }

        result = optimize_configuration(
            hardware, system, workload="chat", mode="automatic"
        )

        self.assertEqual(result["profile"], "battery_saver")
        self.assertEqual(result["model"], "llama3.2:3b")  # smaller model
        self.assertEqual(result["threads"], 4)  # reduced threads
        self.assertEqual(result["quant"], "Q4_K_M")
        self.assertEqual(result["context_length"], 8192)

        joined = " ".join(result["reasoning"]).lower()
        self.assertIn("battery", joined)

    def test_case3_low_available_ram(self):
        """Available RAM < 2GB → memory optimization (Q4, capped context, fewer threads)."""
        hardware = {
            "device": "MacBook Air M3",
            "cpu": "Apple M3",
            "cores": 8,
            "ram_gb": 16,
        }
        system = {
            "battery_pct": 70,
            "charging": True,
            "available_ram_gb": 1.0,
            "thermal": "nominal",
            "swap_usage_high": False,
            "current_threads": 8,
        }

        result = optimize_configuration(
            hardware, system, workload="chat", mode="automatic"
        )

        # Memory rules: Q4_K_M, threads max(2, current//2)=4, context 8192
        self.assertEqual(result["quant"], "Q4_K_M")
        self.assertEqual(result["context_length"], 8192)
        self.assertEqual(result["threads"], 4)

        joined = " ".join(result["reasoning"]).lower()
        self.assertTrue(
            "memory" in joined or "ram" in joined,
            f"Expected memory/RAM reasoning, got: {result['reasoning']}",
        )

    def test_manual_quality_mode_skips_rules(self):
        """Manual mode returns baseline profile regardless of system pressure."""
        hardware = {"cores": 8, "ram_gb": 16, "device": "MacBook Air M3"}
        system = {
            "battery_pct": 10,
            "charging": False,
            "available_ram_gb": 0.5,
            "thermal": "hot",
            "swap_usage_high": True,
        }

        result = optimize_configuration(
            hardware, system, workload="coding", mode="quality"
        )

        self.assertEqual(result["profile"], "quality")
        self.assertEqual(result["model"], "qwen3:8b")
        self.assertEqual(result["extra_flag"], "--think=false")
        joined = " ".join(result["reasoning"]).lower()
        self.assertIn("manual", joined)

    def test_missing_cores_raises(self):
        with self.assertRaises(ValueError):
            optimize_configuration({"ram_gb": 16}, {"battery_pct": 50})


class TestGenerateReasoning(unittest.TestCase):
    def test_returns_list_of_strings(self):
        reasons = generate_reasoning(
            hardware={"device": "MacBook Air M3", "cores": 8, "ram_gb": 16},
            system={"battery_pct": 50, "charging": True, "thermal": "nominal"},
            workload="coding",
            mode="automatic",
            config={
                "model": "qwen2.5-coder:7b",
                "quant": "Q4_K_M",
                "threads": 8,
                "context_length": 16384,
                "profile": "automatic",
            },
        )
        self.assertIsInstance(reasons, list)
        self.assertTrue(all(isinstance(r, str) and r for r in reasons))


if __name__ == "__main__":
    unittest.main()
