import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from .sub_agents.onboarding_agent.agent import onboarding_agent
from .sub_agents.greeting_agent.agent import greeting_agent  
from .sub_agents.ip_agent.agent import ip_agent
from .prompt import ORCHESTRATION_PROMPT 

load_dotenv()

root_agent = Agent(
    name="orchestration_agent",
    model=os.getenv("MODEL_NAME"),
    description=(
        "The primary orchestration agent for the Artisan IP Verification platform. "
        "It manages the flow of user interactions by delegating tasks to specialized sub-agents, "
        "starting with a greeting and then moving to the onboarding process and then move to the ip agent"
    ),
    instruction=ORCHESTRATION_PROMPT,
    sub_agents=[greeting_agent,
                onboarding_agent ]  
)