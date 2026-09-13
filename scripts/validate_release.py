"""Check release boundaries and local links before packaging or uploading."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/story-screen-studio"
EXPECTED = {"story-studio", "story-craft", "story-beats", "story-audit",
            "screen-adaptation", "novel-writing", "novel-writer-cn", "storyteller"}
LICENSES = {"wgwtest--novel-writing--LICENSE.txt",
            "YangsonHung--awesome-agent-skills--LICENSE.txt",
            "xcrrr--claude-skills--LICENSE.txt"}

def validate():
    assert {p.name for p in (PLUGIN / "skills").iterdir()} == EXPECTED, "Unexpected skill"
    assert {p.name for p in (PLUGIN / "licenses").iterdir()} == LICENSES, "License inventory"
    manifest = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text())
    assert manifest["name"] == "story-screen-studio"
    market = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text())
    assert market["plugins"][0]["source"]["path"] == "./plugins/story-screen-studio"
    files = sorted(p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.relative_to(ROOT).parts)
    for p in files:
        assert not p.is_symlink(), f"Symlink: {p}"
        assert p.suffix.lower() not in {".docx", ".xlsx", ".pdf", ".zip", ".pyc"}, p
        content = p.read_text(encoding="utf-8")
        if p.suffix == ".md":
            for target in re.findall(r"\]\(([^)]+)\)", content):
                target = target.split("#")[0]
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                dest = (p.parent / target).resolve()
                assert dest.is_relative_to(ROOT) and dest.exists(), f"Broken/escaping link {p}: {target}"
        if p.name != "validate_release.py":
            assert "/Users/" not in content, f"Private path: {p}"
            assert "BEGIN OPENSSH PRIVATE KEY" not in content, p
    checksums = ROOT / "SHA256SUMS.txt"
    if checksums.exists():
        for line in checksums.read_text().splitlines():
            digest, rel = line.split("  ", 1)
            assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, rel
        listed = {line.split("  ", 1)[1] for line in checksums.read_text().splitlines()}
        assert listed == {str(p.relative_to(ROOT)) for p in files if p != checksums}, "Checksum inventory"
    print(f"PASS: 8 skills, 3 MIT notices, {len(files)} files; local links and release boundaries valid.")

if __name__ == "__main__":
    validate()
