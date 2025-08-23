import os
from google.adk.agents import Agent
from .prompt import ONBOARDING_PROMPT

from dotenv import load_dotenv
load_dotenv()

onboarding_agent = Agent(
    name="onboarding_agent",
    model=os.getenv("MODEL_NAME"),
    description="Collects artisan details and completes onboarding.",
    instruction=ONBOARDING_PROMPT,
    tools=[]  # Later we can add a backend API calls
)
