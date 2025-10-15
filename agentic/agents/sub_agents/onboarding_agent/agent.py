import os
import uuid
from google.adk.agents import Agent
from .prompt import ONBOARDING_PROMPT

onboarding_agent = Agent(
    name="onboarding_agent",
    model=os.getenv("MODEL_NAME"),
    description="Collects artisan details, structures them, then calls ip_agent.",
    instruction=ONBOARDING_PROMPT,
    tools=[], # <-- ADD THE TOOL HERE
    sub_agents=[]
)
