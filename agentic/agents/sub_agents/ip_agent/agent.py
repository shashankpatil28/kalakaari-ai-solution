# ip_agent/agent.py
import os
from google.adk.agents import Agent
from .prompt import IP_PROMPT
from .tools import verify_artwork_uniqueness, call_master_ip_service
from dotenv import load_dotenv

load_dotenv()

ip_agent = Agent(
    name="ip_agent",
    model=os.getenv("MODEL_NAME"),
    description="Verifies artwork uniqueness (cosine similarity) before submitting to the Master IP service.",
    instruction=IP_PROMPT,
    tools=[verify_artwork_uniqueness, call_master_ip_service]
)
