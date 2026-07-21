"""Tests for compute_tiers.py — tier computation from mainspec dependency tables.

Validates the algorithm against real mainspecs and synthetic DAG patterns.
"""

import sys
from pathlib import Path

import pytest

# Add scripts directory to path so we can import compute_tiers
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from compute_tiers import (
    CircularDependencyError,
    SliceInfo,
    analyze_mainspec,
    batch_slices,
    compute_tiers,
    feature_branch_name,
    parse_dependency_table,
    slice_branch_name,
    to_kebab,
    worktree_path,
)

PROJECT_ROOT = Path(__file__).resolve().parents[5]
SPECS_DIR = PROJECT_ROOT / "specs"


# ---------------------------------------------------------------------------
# Helper: build SliceInfo list from a compact dict
# ---------------------------------------------------------------------------


def _make_slices(deps: dict[str, list[str]]) -> list[SliceInfo]:
    """Create SliceInfo list from {number: [dep_numbers]} dict."""
    return [
        SliceInfo(number=num, name=f"Slice {num}", depends_on=dep_list)
        for num, dep_list in deps.items()
    ]


def _tier_numbers(tiers: list[list[SliceInfo]]) -> list[list[str]]:
    """Extract just the slice numbers from tier results."""
    return [sorted([s.number for s in tier]) for tier in tiers]


# ===========================================================================
# Real mainspec tests
# ===========================================================================


class TestSvgChartsTiers:
    """specs/svg-and-charts/mainspec.md → 3 tiers."""

    @pytest.fixture()
    def result(self):
        path = SPECS_DIR / "svg-and-charts" / "mainspec.md"
        return analyze_mainspec(str(path))

    def test_tier_count(self, result):
        assert len(result["tiers"]) == 3

    def test_tier_0(self, result):
        numbers = [s["number"] for s in result["tiers"][0]["slices"]]
        assert numbers == ["3.1"]

    def test_tier_1(self, result):
        numbers = sorted([s["number"] for s in result["tiers"][1]["slices"]])
        assert numbers == ["3.2", "3.3", "3.4", "3.5"]

    def test_tier_2(self, result):
        numbers = [s["number"] for s in result["tiers"][2]["slices"]]
        assert numbers == ["3.6"]

    def test_total_slices(self, result):
        assert result["total_slices"] == 6

    def test_max_parallel(self, result):
        assert result["max_parallel"] == 4

    def test_feature_branch(self, result):
        assert result["feature_branch"] == "feature/svg-and-charts"

    def test_slice_files_resolved(self, result):
        for tier in result["tiers"]:
            for s in tier["slices"]:
                assert s["file"], f"Slice {s['number']} has no resolved file"
                assert Path(s["file"]).is_absolute(), f"Slice {s['number']} file is not absolute: {s['file']}"
                assert Path(s["file"]).exists(), f"Slice {s['number']} file does not exist: {s['file']}"


class TestSceneTransitionsTiers:
    """specs/scene-transitions/mainspec.md → 4 tiers."""

    @pytest.fixture()
    def result(self):
        path = SPECS_DIR / "scene-transitions" / "mainspec.md"
        return analyze_mainspec(str(path))

    def test_tier_count(self, result):
        assert len(result["tiers"]) == 4

    def test_tier_0(self, result):
        numbers = [s["number"] for s in result["tiers"][0]["slices"]]
        assert numbers == ["2.1"]

    def test_tier_1(self, result):
        numbers = [s["number"] for s in result["tiers"][1]["slices"]]
        assert numbers == ["2.2"]

    def test_tier_2(self, result):
        numbers = sorted([s["number"] for s in result["tiers"][2]["slices"]])
        assert numbers == ["2.3", "2.5"]

    def test_tier_3(self, result):
        numbers = [s["number"] for s in result["tiers"][3]["slices"]]
        assert numbers == ["2.4"]


class TestImplementParallelTiers:
    """specs/implement-mainspec-parallel/mainspec.md → 3 tiers (linear chain)."""

    @pytest.fixture()
    def result(self):
        path = SPECS_DIR / "implement-mainspec-parallel" / "mainspec.md"
        return analyze_mainspec(str(path))

    def test_tier_count(self, result):
        assert len(result["tiers"]) == 3

    def test_tier_0(self, result):
        numbers = [s["number"] for s in result["tiers"][0]["slices"]]
        assert numbers == ["1.1"]

    def test_tier_1(self, result):
        numbers = [s["number"] for s in result["tiers"][1]["slices"]]
        assert numbers == ["1.2"]

    def test_tier_2(self, result):
        numbers = [s["number"] for s in result["tiers"][2]["slices"]]
        assert numbers == ["1.3"]


# ===========================================================================
# Synthetic DAG pattern tests
# ===========================================================================


class TestLinearChain:
    """A → B → C → D → 4 tiers, 1 slice each."""

    def test_tiers(self):
        slices = _make_slices({
            "1.1": [],
            "1.2": ["1.1"],
            "1.3": ["1.2"],
            "1.4": ["1.3"],
        })
        tiers = compute_tiers(slices)
        assert len(tiers) == 4
        for tier in tiers:
            assert len(tier) == 1


class TestFullFanout:
    """A → {B, C, D, E} → 2 tiers: [A], [B, C, D, E]."""

    def test_tiers(self):
        slices = _make_slices({
            "1.1": [],
            "1.2": ["1.1"],
            "1.3": ["1.1"],
            "1.4": ["1.1"],
            "1.5": ["1.1"],
        })
        tiers = compute_tiers(slices)
        assert _tier_numbers(tiers) == [["1.1"], ["1.2", "1.3", "1.4", "1.5"]]


class TestDiamond:
    """A → {B, C}, {B, C} → D → 3 tiers: [A], [B, C], [D]."""

    def test_tiers(self):
        slices = _make_slices({
            "1.1": [],
            "1.2": ["1.1"],
            "1.3": ["1.1"],
            "1.4": ["1.2", "1.3"],
        })
        tiers = compute_tiers(slices)
        assert _tier_numbers(tiers) == [["1.1"], ["1.2", "1.3"], ["1.4"]]


class TestCircularDependency:
    """A → B → C → A → raises CircularDependencyError."""

    def test_raises(self):
        slices = _make_slices({
            "1.1": ["1.3"],
            "1.2": ["1.1"],
            "1.3": ["1.2"],
        })
        with pytest.raises(CircularDependencyError):
            compute_tiers(slices)


class TestNoDependencies:
    """{A, B, C} independent → 1 tier: [A, B, C]."""

    def test_tiers(self):
        slices = _make_slices({
            "1.1": [],
            "1.2": [],
            "1.3": [],
        })
        tiers = compute_tiers(slices)
        assert len(tiers) == 1
        assert _tier_numbers(tiers) == [["1.1", "1.2", "1.3"]]


# ===========================================================================
# Naming convention tests
# ===========================================================================


class TestFeatureBranchNaming:
    def test_basic(self):
        assert feature_branch_name("svg-and-charts") == "feature/svg-and-charts"

    def test_with_hyphens(self):
        assert feature_branch_name("implement-mainspec-parallel") == "feature/implement-mainspec-parallel"


class TestSliceBranchNaming:
    def test_basic(self):
        assert slice_branch_name("3.3", "barchart") == "slice/3.3-barchart"

    def test_multi_word(self):
        assert slice_branch_name("3.1", "svg path utilities") == "slice/3.1-svg-path-utilities"


class TestWorktreePath:
    def test_basic(self):
        assert worktree_path("svg-and-charts", "3.3", "barchart") == ".claude/worktrees/svg-and-charts/slice-3.3-barchart"

    def test_multi_word(self):
        assert worktree_path("scene-transitions", "2.1", "scene plan types") == ".claude/worktrees/scene-transitions/slice-2.1-scene-plan-types"


class TestToKebab:
    def test_lowercase(self):
        assert to_kebab("barchart") == "barchart"

    def test_camelcase(self):
        assert to_kebab("BarChart") == "bar-chart"

    def test_spaces(self):
        assert to_kebab("SVG Path Utilities") == "svg-path-utilities"

    def test_special_chars(self):
        assert to_kebab("Registry, Docs & Planner") == "registry-docs-planner"


# ===========================================================================
# Batching tests
# ===========================================================================


class TestBatching:
    def test_large_tier(self):
        """12 slices with max_agents=7 → 2 batches: [7, 5]."""
        items = list(range(12))
        batches = batch_slices(items, max_agents=7)
        assert len(batches) == 2
        assert len(batches[0]) == 7
        assert len(batches[1]) == 5

    def test_exact_fit(self):
        """7 slices with max_agents=7 → 1 batch."""
        items = list(range(7))
        batches = batch_slices(items, max_agents=7)
        assert len(batches) == 1
        assert len(batches[0]) == 7

    def test_small_tier(self):
        """3 slices with max_agents=7 → 1 batch."""
        items = list(range(3))
        batches = batch_slices(items, max_agents=7)
        assert len(batches) == 1
        assert len(batches[0]) == 3

    def test_empty(self):
        assert batch_slices([], max_agents=7) == []


# ===========================================================================
# Table parsing tests
# ===========================================================================


class TestParseDependencyTable:
    def test_basic_table(self):
        content = """## Slice Dependency Map

| Slice | Depends On | Blocks |
|-------|-----------|--------|
| 1.1 — Foundation | — | 1.2 |
| 1.2 — Feature | 1.1 | — |
"""
        slices = parse_dependency_table(content)
        assert len(slices) == 2
        assert slices[0].number == "1.1"
        assert slices[0].name == "Foundation"
        assert slices[0].depends_on == []
        assert slices[1].depends_on == ["1.1"]

    def test_missing_section_raises(self):
        with pytest.raises(ValueError):
            parse_dependency_table("# No dependency table here")

    def test_multiple_deps(self):
        content = """## Slice Dependency Map

| Slice | Depends On | Blocks |
|-------|-----------|--------|
| 1.3 — Final | 1.1, 1.2 | — |
"""
        slices = parse_dependency_table(content)
        assert slices[0].depends_on == ["1.1", "1.2"]
