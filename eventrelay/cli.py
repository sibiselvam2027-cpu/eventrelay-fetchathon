"""Local conversation console. Vendor behavior here is explicitly simulated."""

from __future__ import annotations

import argparse
import json
import os

from .asi import ASIError, extract_intent
from .router import ConversationService, local_intent
from .settings import load_environment, local_path
from .store import EventStore


def make_service():
    store = EventStore(local_path("EVENTRELAY_DB", "data/eventrelay.db"))
    store.seed_demo()
    return ConversationService(local_path("EVENTRELAY_STATE_DB", "data/conversations.db"), store)


def main():
    parser = argparse.ArgumentParser(description="EventRelay local demo console")
    parser.add_argument("--live-llm", action="store_true", help="Interpret natural-language requests through ASI1")
    parser.add_argument("--actor", default="reporter_local_demo")
    args = parser.parse_args()
    load_environment()
    service = make_service()
    print("EventRelay — synthetic wedding demonstration")
    print("This console uses local workflow calls; use fetch_agents for actual multi-agent messages.")
    print("Try: There is a water issue in the dining hall")
    print("Then: drinking water | decline | accept | start | done: Water refilled | confirm")
    print("Type exit to leave. Physical work and demo staff actions are simulated.")
    while True:
        try:
            text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text.casefold() in {"exit", "quit"}:
            break
        if not text:
            continue
        try:
            explicit = local_intent(text)
            if args.live_llm and explicit.get("action") == "report":
                intent = extract_intent(text, service.context(args.actor))
                print("[ASI1 intent interpretation]")
            else:
                intent = explicit
                print("[Local command parser]")
            response = service.handle(args.actor, text, intent=intent)
            print("\nEventRelay: " + response["text"])
        except ASIError as exc:
            print("\nEventRelay: " + str(exc))


if __name__ == "__main__":
    main()
