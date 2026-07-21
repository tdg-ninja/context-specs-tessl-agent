#!/usr/bin/env python3
"""Compute parallelizable tiers from a mainspec's Slice Dependency Map.

Parses the markdown dependency table, builds a DAG, runs topological sort
to group slices into tiers, and outputs JSON with tier assignments and
naming conventions.

Usage:
    python compute_tiers.py <mainspec.md>
"""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


class CircularDependencyError(Exception):
    """Raised when the dependency graph contains a cycle."""

    pass


@dataclass
class SliceInfo:
    number: str
    name: str
    depends_on: list[str] = field(default_factory=list)
    blocks: list[str] = field(default_factory=list)
    file: str = ""


def _parse_refs(col: str) -> list[str]:
    """Parse a comma-separated list of slice references.

    Returns empty list for '—', '–', '-', 'Nothing', or empty string.
    """
    col = col.strip()
    if col in ("—", "–", "-", "Nothing", ""):
        return []
    return [ref.strip() for ref in col.split(",") if ref.strip()]


def parse_dependency_table(content: str) -> list[SliceInfo]:
    """Parse the Slice Dependency Map table from mainspec content.

    Expects a section headed '## Slice Dependency Map' with a markdown table
    having at minimum Slice and Depends On columns. Blocks column is optional.
    """
    lines = content.split("\n")

    # Find the "## Slice Dependency Map" section
    in_section = False
    table_lines = []
    for line in lines:
        if re.match(r"^##\s+Slice Dependency Map", line):
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            if line.startswith("|"):
                table_lines.append(line)

    if len(table_lines) < 3:
        raise ValueError(
            "No valid dependency table found in 'Slice Dependency Map' section"
        )

    # Determine column indices from header
    header_cols = [c.strip().lower() for c in table_lines[0].split("|")]
    # Filter empty strings from leading/trailing pipes
    col_map = {}
    for i, col in enumerate(header_cols):
        if "slice" in col and "slice" not in col_map:
            col_map["slice"] = i
        elif "depends" in col:
            col_map["depends_on"] = i
        elif "blocks" in col:
            col_map["blocks"] = i

    if "slice" not in col_map or "depends_on" not in col_map:
        raise ValueError(
            f"Table must have 'Slice' and 'Depends On' columns. Found: {header_cols}"
        )

    has_blocks = "blocks" in col_map

    # Parse data rows (skip header + separator)
    slices = []
    for row in table_lines[2:]:
        cols = [c.strip() for c in row.split("|")]
        if len(cols) <= col_map["slice"]:
            continue

        slice_col = cols[col_map["slice"]].strip()
        depends_col = cols[col_map["depends_on"]].strip()
        blocks_col = cols[col_map["blocks"]].strip() if has_blocks and len(cols) > col_map["blocks"] else ""

        # Parse slice column: "X.Y — Name" or "X.Y - Name"
        match = re.match(r"^([\d.]+)\s*[—–\-]\s*(.+)$", slice_col)
        if not match:
            continue

        number = match.group(1)
        name = match.group(2).strip()

        slices.append(
            SliceInfo(
                number=number,
                name=name,
                depends_on=_parse_refs(depends_col),
                blocks=_parse_refs(blocks_col),
                file="",
            )
        )

    return slices


def compute_tiers(slices: list[SliceInfo]) -> list[list[SliceInfo]]:
    """Compute parallelizable tiers via topological sort.

    Tier 0 = slices with no dependencies.
    Tier N = slices whose ALL dependencies are in tiers 0..N-1.

    Raises CircularDependencyError if the graph has cycles.
    """
    if not slices:
        return []

    remaining = {s.number: s for s in slices}
    assigned: set[str] = set()
    tiers: list[list[SliceInfo]] = []

    while remaining:
        current_tier = [
            s
            for s in remaining.values()
            if all(dep in assigned for dep in s.depends_on)
        ]

        if not current_tier:
            raise CircularDependencyError(
                f"Circular dependency detected. Remaining slices: {list(remaining.keys())}"
            )

        # Sort by slice number for deterministic output
        current_tier.sort(key=lambda s: [int(x) for x in s.number.split(".")])
        tiers.append(current_tier)

        for s in current_tier:
            assigned.add(s.number)
            del remaining[s.number]

    return tiers


def to_kebab(name: str) -> str:
    """Convert a name to kebab-case.

    Handles CamelCase, spaces, and special characters.
    """
    # Insert hyphens before uppercase letters (CamelCase → camel-case)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name)
    # Replace non-alphanumeric with hyphens
    s = re.sub(r"[^a-z0-9]+", "-", s.lower())
    # Collapse multiple hyphens, strip leading/trailing
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def feature_branch_name(mainspec_name: str) -> str:
    """Compute feature branch name from mainspec directory name."""
    return f"feature/{mainspec_name}"


def slice_branch_name(number: str, name: str) -> str:
    """Compute slice branch name."""
    return f"slice/{number}-{to_kebab(name)}"


def worktree_path(mainspec_name: str, number: str, name: str) -> str:
    """Compute worktree path for a slice, namespaced under the mainspec."""
    return f".claude/worktrees/{mainspec_name}/slice-{number}-{to_kebab(name)}"


def batch_slices(slices: list, max_agents: int = 7) -> list[list]:
    """Split a tier's slices into batches of max_agents."""
    if not slices:
        return []
    return [slices[i : i + max_agents] for i in range(0, len(slices), max_agents)]


def resolve_slice_files(slices: list[SliceInfo], mainspec_path: str) -> None:
    """Resolve slice file paths to absolute paths from the slices/ directory.

    Mutates each SliceInfo.file in place. Paths are absolute so subagents
    in worktrees can read them regardless of working directory.
    """
    spec_dir = Path(mainspec_path).resolve().parent
    slices_dir = spec_dir / "slices"

    if not slices_dir.exists():
        return

    files = list(slices_dir.glob("*.md"))
    for s in slices:
        for f in files:
            if f.name.startswith(f"{s.number}-"):
                s.file = str(f.resolve())
                break


def analyze_mainspec(mainspec_path: str) -> dict:
    """Full analysis: parse, compute tiers, resolve files, return JSON-ready dict."""
    path = Path(mainspec_path)
    content = path.read_text()

    mainspec_name = path.parent.name

    slices = parse_dependency_table(content)
    resolve_slice_files(slices, mainspec_path)
    tiers = compute_tiers(slices)

    max_parallel = max(len(t) for t in tiers) if tiers else 0

    return {
        "mainspec_name": mainspec_name,
        "feature_branch": feature_branch_name(mainspec_name),
        "tiers": [
            {
                "tier": i,
                "slices": [
                    {"number": s.number, "name": s.name, "file": s.file}
                    for s in tier
                ],
            }
            for i, tier in enumerate(tiers)
        ],
        "total_slices": sum(len(t) for t in tiers),
        "max_parallel": max_parallel,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: compute_tiers.py <mainspec.md>", file=sys.stderr)
        sys.exit(1)

    result = analyze_mainspec(sys.argv[1])
    print(json.dumps(result, indent=2))
