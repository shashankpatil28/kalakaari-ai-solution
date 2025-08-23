from google.adk.agents import Agent
import os
from .sub_agents.greeting_agent.agent import greeting_agent  # Corrected import statement

from .promt import ORCHESTRATION_PROMPT 

from dotenv import load_dotenv
load_dotenv()

root_agent = Agent(
    name="orchestration_agent",
    model=os.getenv("MODEL_NAME"),
    description=(
        "The primary orchestration agent for the Artisan IP Verification platform. "
        "It manages the flow of user interactions by delegating tasks to specialized sub-agents, "
        "starting with a greeting and then moving to the onboarding process."
    ),
    instruction=ORCHESTRATION_PROMPT,
    sub_agents=[greeting_agent]  # Add the greeting_agent as a sub-agent
)