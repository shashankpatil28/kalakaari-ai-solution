
import os

from google.adk.agents import Agent
from .promt import GREETING_PROMPT

from dotenv import load_dotenv
load_dotenv()

greeting_agent = Agent(
    name="greeting_agent",
    model=os.getenv("MODEL_NAME"),
    description="A simple greeting agent that introduces the Artisan IP platform.",
    instruction=GREETING_PROMPT,
    tools=[]  # This agent does not need any tools
)