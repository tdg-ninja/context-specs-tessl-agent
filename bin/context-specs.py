#!/usr/bin/env python3
"""Install, update, and verify reviewed Context Specs skills."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

VERSION = "0.1.0"
DEFAULT_REPO = "https://github.com/capitalone/context-specs.git"
DEFAULT_REF = "main"
MANIFEST_PATH = Path(".context-specs/manifest.json")
CATALOG_PATH = Path("catalog/skills-manifest.json")


def die(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def digest_entries(entries: list[dict[str, str]]) -> str:
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":"))
    return sha256_text(payload)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def run(args: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.PIPE).strip()


def current_git_ref(repo: Path) -> str | None:
    try:
        return run(["git", "rev-parse", "--short", "HEAD"], repo)
    except Exception:
        return None


def is_git_url(source: str) -> bool:
    return source.startswith(("http://", "https://", "git@")) or source.endswith(".git")


class Source:
    def __init__(self, root: Path, source: str, ref: str, temp: Path | None = None):
        self.root = root
        self.source = source
        self.ref = ref
        self.temp = temp

    def cleanup(self) -> None:
        if self.temp:
            shutil.rmtree(self.temp, ignore_errors=True)


def materialize_source(source: str | None, ref: str | None) -> Source:
    source = source or DEFAULT_REPO
    ref = ref or DEFAULT_REF
    if not is_git_url(source):
        root = Path(source).resolve()
        if not root.exists():
            die(f"Source does not exist: {source}")
        return Source(root, source, current_git_ref(root) or ref)

    temp = Path(tempfile.mkdtemp(prefix="context-specs-"))
    try:
        run(["git", "clone", "--quiet", "--depth", "1", "--branch", ref, source, str(temp)])
    except subprocess.CalledProcessError as e:
        shutil.rmtree(temp, ignore_errors=True)
        die(f"Could not clone {source} at {ref}: {e.stderr or e}")
    return Source(temp, source, ref, temp)


def walk_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file())


def parse_skill_meta(skill_file: Path) -> dict[str, str]:
    text = skill_file.read_text()
    meta: dict[str, str] = {}
    m = re.match(r"^---\n([\s\S]*?)\n---", text)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip()
    meta.setdefault("name", skill_file.parent.name)
    meta.setdefault("description", "")
    return meta


def review_status_for(repo: Path, rel_path: str, digest: str) -> dict[str, Any]:
    review_file = repo / "catalog" / "reviews" / f"{rel_path.replace('/', '__')}.json"
    if not review_file.exists():
        return {"status": "unreviewed"}
    review = read_json(review_file)
    if review.get("sha256") != digest:
        return {"status": "stale-review", "reviewedAt": review.get("reviewedAt"), "reviewer": review.get("reviewer")}
    return {
        "status": review.get("status", "reviewed"),
        "reviewedAt": review.get("reviewedAt"),
        "reviewer": review.get("reviewer"),
        "notes": review.get("notes", ""),
    }


def generate_catalog(args: argparse.Namespace) -> None:
    repo = Path(args.source).resolve()
    skills = []
    for skill_file in sorted((repo / "skills").rglob("SKILL.md")):
        skill_dir = skill_file.parent
        rel_dir = skill_dir.relative_to(repo).as_posix()
        meta = parse_skill_meta(skill_file)
        files = [{"path": p.relative_to(repo).as_posix(), "sha256": sha256_file(p)} for p in walk_files(skill_dir)]
        digest = digest_entries(files)
        skills.append({
            "name": meta["name"],
            "description": meta["description"],
            "sourcePath": rel_dir,
            "installPath": f".claude/skills/{meta['name']}",
            "sha256": digest,
            "review": review_status_for(repo, rel_dir, digest),
            "files": files,
        })

    subagents = []
    for file in sorted((repo / "subagents").glob("*.md")):
        rel = file.relative_to(repo).as_posix()
        digest = sha256_file(file)
        subagents.append({
            "name": file.name,
            "sourcePath": rel,
            "installPath": f".claude/agents/{file.name}",
            "sha256": digest,
            "review": review_status_for(repo, rel, digest),
        })

    reviewed_times = [
        item.get("review", {}).get("reviewedAt")
        for item in skills + subagents
        if item.get("review", {}).get("reviewedAt")
    ]
    manifest: dict[str, Any] = {
        "schemaVersion": 1,
        "package": "context-specs",
        "generatedAt": max(reviewed_times) if reviewed_times else "unreviewed",
        "sourceRevision": "catalog",
        "catalogSha256": "",
        "policy": {"installDefault": "reviewed-only"},
        "skills": skills,
        "subagents": subagents,
    }
    manifest["catalogSha256"] = sha256_text(json.dumps({**manifest, "catalogSha256": ""}, indent=2))
    out = Path(args.out).resolve() if args.out else repo / CATALOG_PATH
    write_json(out, manifest)
    print(f"Wrote {out} ({len(skills)} skills, {len(subagents)} subagents)")


def load_catalog(source: Path) -> dict[str, Any]:
    catalog_file = source / CATALOG_PATH
    if not catalog_file.exists():
        die(f"No catalog found at {catalog_file}. Run: context-specs catalog generate --source {source}")
    catalog = read_json(catalog_file)
    if "skills" not in catalog or "subagents" not in catalog:
        die(f"Invalid catalog: {catalog_file}")
    return catalog


def ensure_reviewed(catalog: dict[str, Any], allow_unreviewed: bool) -> None:
    bad = []
    for item in catalog["skills"] + catalog["subagents"]:
        status = item.get("review", {}).get("status", "unreviewed")
        if status != "reviewed":
            bad.append(f"{item['name']}: {status}")
    if bad and not allow_unreviewed:
        die("Catalog contains content that is not reviewed for its current digest:\n  " + "\n  ".join(bad) + "\nUse --allow-unreviewed only for local development.")


def verify_source_files(source: Path, catalog: dict[str, Any]) -> None:
    bad = []
    for skill in catalog["skills"]:
        for entry in skill.get("files", []):
            p = source / entry["path"]
            if not p.exists() or sha256_file(p) != entry["sha256"]:
                bad.append(entry["path"])
    for agent in catalog["subagents"]:
        p = source / agent["sourcePath"]
        if not p.exists() or sha256_file(p) != agent["sha256"]:
            bad.append(agent["sourcePath"])
    if bad:
        die("Source files do not match catalog:\n  " + "\n  ".join(bad))


def copy_tree(src: Path, dest: Path, dry_run: bool) -> None:
    if dry_run:
        return
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def install_or_update(args: argparse.Namespace, mode: str) -> None:
    target = Path(args.target).resolve()
    src = materialize_source(args.source, args.ref)
    try:
        catalog = load_catalog(src.root)
        ensure_reviewed(catalog, args.allow_unreviewed)
        verify_source_files(src.root, catalog)
        installed_skills = []
        installed_subagents = []
        for skill in catalog["skills"]:
            copy_tree(src.root / skill["sourcePath"], target / skill["installPath"], args.dry_run)
            installed_skills.append({k: skill[k] for k in ["name", "sourcePath", "installPath", "sha256", "review"]})
            print(f"{'Would install' if args.dry_run else 'Installed'} skill {skill['name']} -> {skill['installPath']}")
        for agent in catalog["subagents"]:
            dest = target / agent["installPath"]
            if not args.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src.root / agent["sourcePath"], dest)
            installed_subagents.append({k: agent[k] for k in ["name", "installPath", "sha256", "review"]})
            print(f"{'Would install' if args.dry_run else 'Installed'} subagent {agent['name']} -> {agent['installPath']}")
        lock = {
            "schemaVersion": 1,
            "package": catalog["package"],
            "installedAt": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "mode": mode,
            "source": src.source,
            "ref": src.ref,
            "catalogSha256": catalog["catalogSha256"],
            "sourceRevision": current_git_ref(src.root) or catalog["sourceRevision"],
            "policy": {"reviewedOnly": not args.allow_unreviewed},
            "skills": installed_skills,
            "subagents": installed_subagents,
        }
        if not args.dry_run:
            write_json(target / MANIFEST_PATH, lock)
        verb = "updated" if mode == "update" else "installed"
        print(f"{'Dry run complete' if args.dry_run else 'Done'}. {len(installed_skills)} skills and {len(installed_subagents)} subagents {verb}.")
    finally:
        src.cleanup()


def verify(args: argparse.Namespace) -> None:
    target = Path(args.target).resolve()
    manifest_file = target / MANIFEST_PATH
    if not manifest_file.exists():
        die(f"No {MANIFEST_PATH} found. Run context-specs install first.")
    lock = read_json(manifest_file)
    ok = True
    for skill in lock.get("skills", []):
        skill_dir = target / skill["installPath"]
        installed_files = []
        for p in walk_files(skill_dir):
            installed_files.append({"path": str((Path(skill["sourcePath"]) / p.relative_to(skill_dir)).as_posix()), "sha256": sha256_file(p)})
        digest = digest_entries(installed_files) if skill_dir.exists() else "missing"
        if digest != skill["sha256"]:
            ok = False
            print(f"FAIL skill {skill['name']}: expected {skill['sha256']}, got {digest}")
        else:
            print(f"OK   skill {skill['name']}")
        if skill.get("review", {}).get("status") != "reviewed":
            ok = False
            print(f"FAIL skill {skill['name']}: not reviewed")
    for agent in lock.get("subagents", []):
        file = target / agent["installPath"]
        digest = sha256_file(file) if file.exists() else "missing"
        if digest != agent["sha256"]:
            ok = False
            print(f"FAIL subagent {agent['name']}: expected {agent['sha256']}, got {digest}")
        else:
            print(f"OK   subagent {agent['name']}")
    if not ok:
        raise SystemExit(1)
    print(f"Verified {len(lock.get('skills', []))} skills and {len(lock.get('subagents', []))} subagents from reviewed manifest {lock.get('catalogSha256')}.")


def list_items(args: argparse.Namespace) -> None:
    src = materialize_source(args.source, args.ref)
    try:
        catalog = load_catalog(src.root)
        for skill in catalog["skills"]:
            print(f"{skill['name']}\t{skill['review']['status']}\t{skill['description']}")
        for agent in catalog["subagents"]:
            print(f"{agent['name']}\t{agent['review']['status']}\tsubagent")
    finally:
        src.cleanup()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Install, update, and verify reviewed Context Specs skills.")
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="command", required=True)

    def add_source_flags(s: argparse.ArgumentParser) -> None:
        s.add_argument("--source", help=f"Path or git URL to Context Specs source (default: {DEFAULT_REPO})")
        s.add_argument("--ref", default=DEFAULT_REF, help="Git ref when --source is a git URL")

    for name in ["install", "update"]:
        s = sub.add_parser(name)
        add_source_flags(s)
        s.add_argument("--target", default=".")
        s.add_argument("--allow-unreviewed", action="store_true", help="Install content whose current digest has not been reviewed")
        s.add_argument("--dry-run", action="store_true")
        s.set_defaults(func=lambda a, n=name: install_or_update(a, n))

    s = sub.add_parser("verify")
    s.add_argument("--target", default=".")
    s.set_defaults(func=verify)

    s = sub.add_parser("list")
    add_source_flags(s)
    s.set_defaults(func=list_items)

    s = sub.add_parser("catalog")
    cat_sub = s.add_subparsers(dest="catalog_command", required=True)
    g = cat_sub.add_parser("generate")
    g.add_argument("--source", default=".")
    g.add_argument("--out")
    g.set_defaults(func=generate_catalog)
    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
