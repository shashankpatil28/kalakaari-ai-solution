# agentic/agents/sub_agents/ip_agent/agent.py

import os
#from google.ai.generativelanguage.tools import tool # We can leave the import, but won't use it
from google.adk.agents import Agent
from .prompt import IP_PROMPT
from dotenv import load_dotenv

load_dotenv()

ip_agent = Agent(
    name="ip_agent",
    model=os.getenv("MODEL_NAME"),
    description="A temporary agent to receive and display data from the onboarding process.",
    instruction=IP_PROMPT,
    tools=[]  # <-- Temporarily remove the tool
)