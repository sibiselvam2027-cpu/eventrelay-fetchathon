"""Prepare five multi-file Agentverse Hosted Agent projects; no secret copying."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROLES = ("coordinator", "hospitality", "audio", "facilities", "housekeeping")
MODULES = ("__init__.py", "store.py", "router.py", "asi.py", "settings.py", "fetch_agents.py", "hosted_state.py", "hosted_runtime.py")
DESCRIPTIONS = {
    "coordinator": "EventRelay coordinates event-day issues: clarify, offer, obtain crew acceptance, follow up, escalate, and require reporter-confirmed resolution in ASI:One.",
    "hospitality": "EventRelay hospitality agent handles drinking-water crew offers and explicit staff decisions.",
    "audio": "EventRelay audio agent handles microphone and speaker crew offers and explicit staff decisions.",
    "facilities": "EventRelay facilities agent handles power and lighting crew offers and explicit staff decisions.",
    "housekeeping": "EventRelay housekeeping agent handles spill and cleanup crew offers and explicit staff decisions.",
}


def main():
    missing = [name for name in MODULES if not (ROOT / "eventrelay" / name).exists()]
    if missing:
        raise SystemExit("Hosted build is not complete: " + ", ".join(missing))
    for role in ROLES:
        target = ROOT / "hosted" / role
        target.mkdir(parents=True, exist_ok=True)
        for name in MODULES:
            if name == "__init__.py":
                continue
            text = (ROOT / "eventrelay" / name).read_text(encoding="utf-8")
            # The hosted editor supports sibling files. Flatten package imports
            # so the same tested source can be uploaded without a wheel install.
            text = text.replace("from .", "from ").replace("from eventrelay.", "from ")
            if name == "settings.py":
                text = text.replace("ROOT = Path(__file__).resolve().parents[1]", "ROOT = Path('.')")
            (target / name).write_text(text, encoding="utf-8")
        (target / "agent.py").write_text(
            "# Agentverse supplies the hosted 'agent' instance.\n"
            "# Older hosted templates instead require the zero-argument Agent().\n"
            "from uagents import Agent\n"
            "from hosted_runtime import attach\n\n"
            "try:\n    agent\nexcept NameError:\n    agent = Agent()\n\n"
            "try:\n"
            f"    attach(agent, role={role!r})\n"
            "except Exception:\n    import traceback\n    print(traceback.format_exc())\n    raise\n", encoding="utf-8")
        (target / "pyproject.toml").write_text(
            "[project]\n" + f'name = "eventrelay-{role}"\nversion = "0.1.0"\ndescription = "{DESCRIPTIONS[role]}"\n'
            'requires-python = ">=3.10,<3.14"\ndependencies = ["uagents==0.25.5", "uagents-core==0.4.12", "openai"]\n', encoding="utf-8")
        example = "# Agentverse injects ASI1_API_KEY and ASI1_BASE_URL; omit empty overrides.\nASI1_MODEL=asi1\nEVENTRELAY_DEMO_MODE=1\nEVENTRELAY_COORDINATOR_ADDRESS=\nEVENTRELAY_HOSPITALITY_ADDRESS=\nEVENTRELAY_AUDIO_ADDRESS=\nEVENTRELAY_FACILITIES_ADDRESS=\nEVENTRELAY_HOUSEKEEPING_ADDRESS=\nEVENTRELAY_ORGANIZER_SENDERS=\nEVENTRELAY_STAFF_SENDERS={}\nEVENTRELAY_DEMO_DECISIONS={\"staff_arun\":\"decline\",\"staff_neha\":\"accept\",\"staff_ravi\":\"accept\",\"staff_sara\":\"accept\",\"staff_vikram\":\"accept\",\"staff_pooja\":\"accept\",\"staff_meena\":\"accept\",\"staff_kiran\":\"accept\"}\n"
        (target / ".env.example").write_text(example, encoding="utf-8", newline="\n")
        # AVCTL needs a local configuration file. This contains placeholders only;
        # real values must be put into Agent Secrets and never committed.
        if not (target / ".env").exists():
            (target / ".env").write_text(example, encoding="utf-8", newline="\n")
        else:
            # Preserve private configured values, but never mask the platform's
            # injected hosted credentials with obsolete blank placeholders.
            env_path = target / ".env"
            lines = env_path.read_text(encoding="utf-8").splitlines()
            kept = []
            for line in lines:
                name, separator, value = line.partition("=")
                if separator and name.strip() in {"ASI1_API_KEY", "ASI1_BASE_URL"} and not value.strip():
                    continue
                kept.append(line)
            env_path.write_text("\n".join(kept) + "\n", encoding="utf-8", newline="\n")
        (target / "README.md").write_text(
            f"# EventRelay {role.title()}\n\n{DESCRIPTIONS[role]}\n\n"
            "![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)\n"
            "![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)\n\n"
            "Hosted on Agentverse with direct uAgents and ACP. ASI:One is the user interface. "
            "Bundled people and physical work are explicitly simulated.\n\n"
            "Coordinator prompts: 'There is a water issue in the dining hall'; 'Drinking water has run out'; "
            "'Show status'; 'The problem is still not resolved'. Native cards guide clarification and confirmation.\n",
            encoding="utf-8")
    print("Prepared five Hosted Agent projects under hosted/. No real credentials were copied.")


if __name__ == "__main__":
    main()
