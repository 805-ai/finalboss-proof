#!/usr/bin/env python3
"""Scrub host paths from V3.11 public proof evidence text; regenerate manifests."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import zipfile

HOME_PREFIX = "/home/ubuntu/"
ENGINE_PREFIX = "/var/lib/finalboss-one-engine"
SCRUB_FILES = (
    "evidence/RUN_BINDING.txt",
    "evidence/LIVE_WELDED_GATE_SNAPSHOT_20260824T215133Z.txt",
    "evidence/target_battery.json",
    "evidence/SOURCE_COLLECTION_HASHES.sha256",
)


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scrub_text(text: str) -> str:
    return text.replace(HOME_PREFIX, "[SOURCE_ARCHIVE]/").replace(ENGINE_PREFIX, "[ENGINE_ROOT]")


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} IN.zip OUT.zip", file=sys.stderr)
        return 2
    in_zip = pathlib.Path(sys.argv[1])
    out_zip = pathlib.Path(sys.argv[2])
    work = pathlib.Path("/tmp/v311-scrub-work")
    if work.exists():
        import shutil

        shutil.rmtree(work)
    work.mkdir(parents=True)
    with zipfile.ZipFile(in_zip) as zf:
        zf.extractall(work)
    roots = [p for p in work.iterdir() if p.is_dir()]
    if len(roots) != 1:
        raise SystemExit(f"expected one top-level dir, got {roots}")
    pkt = roots[0]

    for rel in SCRUB_FILES:
        path = pkt / rel
        original = path.read_text(encoding="utf-8")
        scrubbed = scrub_text(original)
        if scrubbed == original:
            raise SystemExit(f"no path scrub applied: {rel}")
        path.write_text(scrubbed, encoding="utf-8")

    # Update SOURCE_TARGET_MANIFEST for scrubbed custody-mapped files
    stm = pkt / "evidence/SOURCE_TARGET_MANIFEST.sha256"
    updates = {
        "./RUN_BINDING.txt": sha256_file(pkt / "evidence/RUN_BINDING.txt"),
        "./state/target_battery.json": sha256_file(pkt / "evidence/target_battery.json"),
    }
    new_lines = []
    for line in stm.read_text(encoding="utf-8").splitlines():
        digest, rel = line[:64], line[66:]
        if rel in updates:
            new_lines.append(f"{updates[rel]}  {rel}")
        else:
            new_lines.append(line)
    stm.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    record_path = pkt / "PUBLIC_PROOF_RECORD.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["provenance"]["source_target_manifest_sha256"] = sha256_file(stm)
    record["provenance"]["source_collection_manifest_sha256"] = sha256_file(
        pkt / "evidence/SOURCE_COLLECTION_HASHES.sha256"
    )
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    entries = []
    for path in sorted(pkt.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(pkt).as_posix()
        if rel in {"MANIFEST.sha256", "MANIFEST.sha256.sha256"}:
            continue
        entries.append(f"{sha256_file(path)}  {rel}")
    manifest = pkt / "MANIFEST.sha256"
    manifest.write_text("\n".join(entries) + "\n", encoding="utf-8")
    (pkt / "MANIFEST.sha256.sha256").write_text(
        f"{sha256_file(manifest)}  MANIFEST.sha256\n", encoding="utf-8"
    )

    # Path scan must be clean
    for path in pkt.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if "/home/ubuntu" in text or "/var/lib/finalboss-one-engine" in text:
            raise SystemExit(f"path leak remains in {path.relative_to(pkt)}")
        if "805-ai/grok-final-boss" in text or "grok-final-boss" in text:
            raise SystemExit(f"private repo ref in {path.relative_to(pkt)}")

    # Deterministic ZIP: fixed date (2026-08-24) and sorted members.
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(pkt.rglob("*")):
            if path.is_file():
                arc = path.relative_to(work).as_posix()
                info = zipfile.ZipInfo(arc, date_time=(2026, 8, 24, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                zf.writestr(info, path.read_bytes())

    digest = sha256_file(out_zip)
    print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
