# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""PingOne AIC Explainer — coordinator plus Ping and terminology specialists."""

from functools import cached_property

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import AgentTool, url_context
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.genai import Client
from google.genai import types

MODEL = "gemini-3.5-flash"


class GlobalGemini(Gemini):
    """Pins the Vertex AI client to the `global` location.

    gemini-3 series models are served from `global`. The default ADK `Gemini`
    client inherits the Agent Runtime instance region (for example
    `us-central1`) and then fails with model-not-found. Overriding
    `api_client` keeps the runtime regional while routing model calls to the
    global endpoint.
    """

    @cached_property
    def api_client(self) -> Client:
        return Client(vertexai=True, location="global")


def _model() -> GlobalGemini:
    return GlobalGemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    )


def _search_agent(name: str) -> Agent:
    return Agent(
        name=name,
        model=_model(),
        description="Agent specialized in performing Google searches.",
        instruction="Use the GoogleSearchTool to find information on the web.",
        tools=[GoogleSearchTool()],
    )


def _url_context_agent(name: str) -> Agent:
    return Agent(
        name=name,
        model=_model(),
        description="Agent specialized in fetching content from URLs.",
        instruction="Use the UrlContextTool to retrieve content from provided URLs.",
        tools=[url_context],
    )


pingone_aic_specialist = Agent(
    name="pingone_aic_specialist",
    model=_model(),
    description="Agent that explains PingOne AIC concepts and platform.",
    instruction=(
        "Answer queries focused on PingOne AIC only. Do not dive into "
        "technical industry terminology e.g. avoid explaining what is OIDC "
        "or Adaptive Authentication."
    ),
    tools=[AgentTool(agent=_search_agent("pingone_aic_specialist_google_search_agent"))],
)

terminology_explainer = Agent(
    name="terminology_explainer",
    model=_model(),
    description=(
        "Agent that helps expand identity terminology in general, not scoped "
        "to Ping Identity platform and features"
    ),
    instruction=(
        "You'll be asked to explain generic terms in the world of digital "
        "identity. Explain terms like OAuth, SSO, SAML. Refuse anything which "
        "is not in the IAM and Identity space. For terms that you are asked "
        "to explore find external blog post that will allow user to expand "
        "their knowledge on the subject"
    ),
    tools=[
        AgentTool(agent=_search_agent("terminology_explainer_google_search_agent")),
        AgentTool(agent=_url_context_agent("terminology_explainer_url_context_agent")),
    ],
)

root_agent = Agent(
    # Keep in sync with agents-cli-manifest.yaml: agents-cli derives this name
    # from the project `name:` recorded there, and telemetry reports it as
    # gen_ai.agent.name.
    name="ping_aic_explainer",
    model=_model(),
    description="Explain PingOne products and technical terms.",
    instruction=(
        "Based on public documentation, explain user's queries about PingOne "
        "Advanced Identity Cloud products and features. You have two "
        "subagents to help you - one is focused on Ping Identity and another "
        "is for generic technology queries. By default you should provide "
        "concise responses without elaborating on generic terms. Unless user "
        "asks to explain more or describes themselves as beginners then "
        "you'll use generic query to explain the technology"
    ),
    sub_agents=[pingone_aic_specialist, terminology_explainer],
    tools=[
        AgentTool(agent=_search_agent("ping_aic_explainer_google_search_agent")),
        AgentTool(agent=_url_context_agent("ping_aic_explainer_url_context_agent")),
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
