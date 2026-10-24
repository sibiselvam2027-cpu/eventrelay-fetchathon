# Agentverse supplies the hosted 'agent' instance.
# Older hosted templates instead require the zero-argument Agent().
from uagents import Agent
from hosted_runtime import attach

try:
    agent
except NameError:
    agent = Agent()

try:
    attach(agent, role='audio')
except Exception:
    import traceback
    print(traceback.format_exc())
    raise
