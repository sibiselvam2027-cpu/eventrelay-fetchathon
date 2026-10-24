"""Prepare local configuration; no key, private seed or token is displayed."""

from pathlib import Path
import secrets

root = Path(__file__).resolve().parent
target = root / ".env"
text = target.read_text(encoding="utf-8-sig") if target.exists() else (root / ".env.example").read_text(encoding="utf-8")
lines = text.splitlines()
found = False
for index, line in enumerate(lines):
    if line.startswith("EVENTRELAY_AGENT_SEED="):
        found = True
        if not line.partition("=")[2].strip():
            lines[index] = "EVENTRELAY_AGENT_SEED=" + secrets.token_hex(32)
if not found:
    lines.append("EVENTRELAY_AGENT_SEED=" + secrets.token_hex(32))
target.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("Private local settings prepared. Synthetic demo mode is enabled. No credentials were printed.")
