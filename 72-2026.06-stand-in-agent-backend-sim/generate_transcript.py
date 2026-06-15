#!/usr/bin/env python3
"""
Converts the raw podcast debrief into timed, speaker-attributed transcript.json.
Run: uv run generate_transcript.py
"""
import json
from pathlib import Path

WPM = 150  # words per minute
SPW = 60 / WPM  # seconds per word
GAP = 1.5  # seconds gap between speakers

ENTRIES = [
    ("Tim", "Welcome to the Cloud Security Podcast by Google. I'm Tim Peacock, and joining me today as always is Anton Chuvakin. We're recording live at Google Cloud Next 2026 from the PwC showcase space."),
    ("Anton", "Great to be here Tim. And we have a fantastic guest with us today: Matt Gregson, Principal at PwC US. Matt, welcome to the show."),
    ("Matt", "Thanks Anton, thanks Tim. Really excited to be here at Next and to talk about something we're seeing transform security operations in real time."),
    ("Tim", "And that transformation is around agentic AI in the SOC. Matt, before we get into the future, let's ground ourselves. What does the market actually look like today when it comes to AI in security operations?"),
    ("Matt", "So when you look at the market right now, it's clearly bifurcated into two distinct operating models. The first and most mature is what I'd call the co-pilot model."),
    ("Matt", "Co-pilots use large language models — Gemini and others — integrated via Model Context Protocol servers directly into SecOps platforms. Analysts are querying telemetry through natural language interfaces, parsing alerts, generating trend reports. That's in production at scale today."),
    ("Anton", "And the second model?"),
    ("Matt", "The second model is true agentic integration — where AI agents actively participate in or orchestrate remediation pipelines. And I'll be direct: that's still largely in pilot or proof-of-concept phase across most enterprises."),
    ("Matt", "Organizations are evaluating very carefully where to safely inject agentic decision-making into pre-existing deterministic workflows. The plumbing gets complex fast."),
    ("Tim", "What's the primary friction point holding enterprises back from fully autonomous operation?"),
    ("Matt", "It's organizational comfort and trust — full stop. The long-term vision of the industry absolutely mandates autonomous containment and remediation. But security leadership is carefully, methodically testing governance and safety guardrails before they're willing to grant AI agents full execution rights over infrastructure containment."),
    ("Anton", "Which makes total sense when you think about the blast radius of a badly scoped autonomous action."),
    ("Matt", "Exactly. And this brings me to a concept I find really useful: the Agentic Overton Window."),
    ("Tim", "Tell us about that."),
    ("Matt", "The Agentic Overton Window defines the boundary of autonomous response behaviors that an enterprise finds acceptable and trustworthy at any given moment. Historically, deterministic SOAR workflows established very narrow autonomous boxes — automatically deleting verified phishing emails from corporate mailboxes, for instance."),
    ("Matt", "That was a win. Organizations got comfortable with it. The modern security mission is to systematically expand that window over the coming years, pushing these contained execution boxes into broader, more complex environmental scopes."),
    ("Anton", "So you're not blowing the window open — you're methodically widening it as you build confidence."),
    ("Matt", "Right. You earn autonomy incrementally. And the business returns when you do expand it are significant at every level of the organization."),
    ("Tim", "Break that down for us — what's the value story at the board level versus the operational level?"),
    ("Matt", "At the executive board and C-suite level, the primary outcome is structural risk reduction. You're talking about a dramatic contraction in Mean Time to Respond — MTTR. That's the number the board understands. That's the number that maps to breach cost and regulatory exposure."),
    ("Anton", "And at the operational level?"),
    ("Matt", "At the operational level, the integration of autonomous agents addresses the escalating speed of modern threat actors. You're allowing organizations to match the velocity of highly accelerated attack lifecycles. The adversary is moving fast. Your response infrastructure needs to match that tempo."),
    ("Tim", "Speaking of threat actors — there's a lot of hype around AI-enabled attackers. How much of that is real versus marketing noise?"),
    ("Matt", "It's real, and it manifests in very specific, measurable technical impacts. Let me give you two that I think are most important."),
    ("Matt", "First: automated vulnerability exploitation. Attackers are using specialized LLM pipelines as automated zero-day factories. The resource, time, and financial barriers to discover and weaponize novel vulnerabilities have collapsed. The window between vulnerability disclosure and active widespread exploitation is effectively gone."),
    ("Anton", "That's not hypothetical anymore. We're seeing that in the wild."),
    ("Matt", "Exactly. The second point is important though: despite AI acceleration, threat actors still rely heavily on well-documented structural attack paths. LSASS memory dumping, lateral movement, standard privilege escalation — the post-exploitation mechanics haven't fundamentally changed."),
    ("Matt", "That's actually a window of opportunity for defenders. Because those mechanics are still visible, security teams can still intercept these paths post-initial access — provided their response infrastructure operates at machine speed to match."),
    ("Tim", "Let's talk about the future. Anton, you've been thinking a lot about what the SOC looks like in 2030 — which is actually only four years away."),
    ("Anton", "It's close. And the honest answer is that the fundamental role of the human analyst is undergoing a structural shift rather than outright elimination. Due to systemic IT inertia — legacy architecture dependencies, mainframes, unpatched environments — traditional Tier 1 manual triage won't disappear entirely."),
    ("Anton", "But in modernized organizations, human workload shifts dramatically. Three areas in particular stand out."),
    ("Anton", "First: Agent Supervision. Human analysts become supervisors — reviewing high-speed autonomous actions, validating containment decisions, auditing agent behavioral strings. You're no longer triaging every alert; you're auditing what your agents did and catching edge cases."),
    ("Anton", "Second: Detection Engineering and Automation Architecture. Human effort pivots toward constructing, tuning, and maintaining the underlying detection engines, deterministic playbooks, and contextual frameworks that fuel the agentic systems in the first place."),
    ("Anton", "And third: Threat Landscape Tracking. Continuously aligning your technical defenses with the shifting strategies of global threat actors. That strategic intelligence function remains deeply human."),
    ("Tim", "Matt, what does an organization need to have in place before they can realistically adopt an agentic SOC architecture? What are the prerequisites?"),
    ("Matt", "Organizations cannot bypass foundational security hygiene by deploying an AI agent. True readiness requires specific technical prerequisites that have to exist first."),
    ("Matt", "First: centralized data platforms. A unified, high-scale data engine with clean, comprehensive telemetry across host systems, networks, and identity providers. Your agent can't enrich context it can't access."),
    ("Matt", "Second: integrated core infrastructure. Centralized platform APIs that grant orchestration layers immediate, programmatic execution control over firewalls, IAM systems, and Identity Providers. If your agent can't call an API to block an endpoint, agentic remediation is theoretical."),
    ("Anton", "That second point is where a lot of organizations are stuck. They have the data; they don't have unified control plane APIs."),
    ("Matt", "It's the single biggest blocker I see in the field. The tool sprawl problem hasn't been solved yet in most enterprises."),
    ("Matt", "And the third prerequisite is deterministic SOAR foundations. High-functioning, well-engineered SOAR playbooks must exist before you introduce agents. The optimal architecture executes deterministic logic first — routine enrichment, threat intel lookups, known variable parsing — and then passes the highly curated context to an LLM agent for advanced reasoning."),
    ("Matt", "This structure preserves analytical accuracy and prevents catastrophic context loss if an agent fails mid-execution. The deterministic layer is your safety net."),
    ("Tim", "Let's talk about the economics and performance of LLM pipelines in this context. Where does the math actually work?"),
    ("Matt", "This is a critical design consideration that I don't think gets enough attention. Passing raw, unfiltered event streams — high-volume cloud audit logs for example — directly into an LLM is architecturally and financially non-viable for most enterprises."),
    ("Matt", "Deterministic streaming detection and response pipelines operate at speeds significantly faster than token-by-token LLM generation. So the optimized SOC infrastructure treats AI as a precise tool within a broader multi-tiered economic model."),
    ("Anton", "Walk us through the tiers."),
    ("Matt", "Tier 1 is Deterministic Automation. This operates at minimal cost — pennies per execution — and maximal speed. It filters noise, auto-resolves high-confidence alerts via rigid flowcharts, no LLM required."),
    ("Matt", "Tier 2 is the Agentic LLM Layer. You invoke this mid-to-late in the chain to process complex variables, synthesize threat intel, or summarize dense event clusters. You're calling the LLM only when the deterministic layer genuinely can't handle it."),
    ("Matt", "Tier 3 is Human Execution. Reserved for high-stakes scenarios requiring ultimate manual validation. The cases where a human really does need to make the call."),
    ("Anton", "And which LLMs are you actually using at each tier? Are you reaching for the flagship models everywhere?"),
    ("Matt", "No, and this is a point that often surprises people. Rigorous back-testing and observability frameworks consistently show that state-of-the-art flagship models are rarely required for everyday security operations."),
    ("Matt", "Smaller, highly optimized flash models from prior release cycles provide exceptional accuracy for event summarization and log analysis at a fraction of the token cost. You establish an explicit alert budget through operational testing and match the model tier to the task complexity."),
    ("Tim", "Before we wrap up — how should SOC teams be measuring success as they evolve toward this architecture? What metrics matter?"),
    ("Anton", "Traditional MTTD and MTTR remain essential. But you have to augment them with agent-specific governance metrics. The number of human touches per case is a critical one. The overall ratio of autonomous versus manual containment executions is another."),
    ("Anton", "Those metrics tell you how far your autonomous capabilities have actually matured — not just in theory, but in production."),
    ("Tim", "Matt, final question: practical advice for a security leader who wants to start this journey today?"),
    ("Matt", "Lower the barrier to entry through immediate internal experimentation. Three concrete steps."),
    ("Matt", "First: construct basic AI agents within ring-fenced testing environments. Don't start in production. Second: connect those agents to existing MCP servers or internal service APIs. Third: evaluate the art of the possible — validate how effectively the model queries your localized security data before you design complex autonomous workflows."),
    ("Matt", "Build trust with the technology incrementally, the same way you'd expand that Overton Window. The technology is ready. The question is whether your organization is ready to build the governance structures that let you safely exploit it."),
    ("Tim", "Fantastic. Matt Gregson from PwC US — thank you so much for joining us today from Google Cloud Next 2026."),
    ("Matt", "Thanks Tim, thanks Anton. Really enjoyed it."),
    ("Anton", "And thank you to everyone listening. We'll have show notes in the links below. Subscribe wherever you get your podcasts."),
    ("Tim", "Until next time."),
]


def words(text: str) -> int:
    return len(text.split())


def generate():
    entries = []
    t = 0.0
    for speaker, text in ENTRIES:
        start = round(t, 2)
        duration = words(text) * SPW
        end = round(t + duration, 2)
        entries.append({"speaker": speaker, "start_time": start, "end_time": end, "text": text})
        t = end + GAP

    transcript = {
        "session_name": "Cloud Security Podcast Ep 278: Agentic SOC — Hype vs. Reality",
        "track_id": "main",
        "entries": entries,
    }
    out = Path(__file__).parent / "data" / "transcript.json"
    out.write_text(json.dumps(transcript, indent=2))
    total_min = t / 60
    print(f"Generated {len(entries)} entries, ~{total_min:.1f} minutes of content → {out}")


if __name__ == "__main__":
    generate()
