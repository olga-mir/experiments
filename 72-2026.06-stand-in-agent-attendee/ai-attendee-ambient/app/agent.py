from google.adk.apps import App

from app.ambient_agent import root_agent

app = App(
    root_agent=root_agent,
    name="app",
)
