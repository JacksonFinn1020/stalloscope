#!/usr/bin/env python3
"""Unit tests for DockerPullTracker — mid-progress must be in (0, 100)."""

from __future__ import annotations

import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GBP_PATH = ROOT / "gbp"


def load_gbp():
    return SourceFileLoader("gbp_mod", str(GBP_PATH)).load_module()


class TestDockerPullTracker(unittest.TestCase):
    def setUp(self):
        self.gbp = load_gbp()
        self.tracker = self.gbp.DockerPullTracker()

    def test_mb_download_and_average(self):
        sim = (
            "aaa111: Downloading [====>] 12.5MB/50MB\r"
            "bbb222: Waiting\r"
            "bbb222: Downloading [=>] 5MB/20MB\r"
        )
        prog, detail, phase = self.tracker.feed_text(sim)
        self.assertIsNotNone(prog)
        self.assertGreater(prog, 0)
        self.assertLess(prog, 100)
        # aaa=25, bbb=25 → avg 25
        self.assertAlmostEqual(prog, 25.0, delta=0.6)
        self.assertIn("Downloading", detail or "")

    def test_extract_pct_and_complete(self):
        t = self.gbp.DockerPullTracker()
        t.feed_fragment("aaa111: Downloading [==========>] 50MB/50MB")
        t.feed_fragment("aaa111: Download complete")
        t.feed_fragment("aaa111: Extracting [=====>] 60%")
        prog, _, phase = t.feed_fragment("aaa111: Extracting [=====>] 60%")
        self.assertEqual(phase, "extracting")
        self.assertAlmostEqual(prog, 60.0, delta=0.1)
        t.feed_fragment("aaa111: Pull complete")
        self.assertEqual(t.overall, 100.0)

    def test_already_exists_is_100(self):
        t = self.gbp.DockerPullTracker()
        t.feed_fragment("ccc333: Already exists")
        self.assertEqual(t.overall, 100.0)

    def test_cr_split_mid_progress(self):
        frags = self.gbp.split_progress_fragments(
            "aaa111: Downloading [=>] 2.5MB/50MB\raaa111: Downloading [====>] 12.5MB/50MB\n"
        )
        self.assertEqual(len(frags), 2)
        t = self.gbp.DockerPullTracker()
        mid_progress = []
        for f in frags:
            p, _, _ = t.feed_fragment(f)
            if p is not None:
                mid_progress.append(p)
        self.assertTrue(any(0 < p < 100 for p in mid_progress), mid_progress)
        # first frag 2.5/50 = 5%
        self.assertAlmostEqual(mid_progress[0], 5.0, delta=0.2)


if __name__ == "__main__":
    unittest.main()
