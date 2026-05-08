"""
healthcare_agent — BC Navigator Agent definition.

This agent helps unattached BC patients (those without a family doctor) navigate
the BC healthcare system.  It can:
  • Check urgent care wait times near the patient's location
  • Triage symptoms to recommend ER / urgent care / telehealth
  • Explain BC government programs they may qualify for (MSP, PharmaCare, etc.)
  • Walk them through registering on the Health Connect Registry

It also has optional read-only access to a patient's FHIR R4 record when FHIR
credentials are supplied by the caller via A2A message metadata.

To customise:
  • Change model, description, and instruction below.
  • Add or remove tools from the tools=[...] list.
  • Add new BC navigation tools in healthcare_agent/tools/bc_navigation.py.
  • Add new FHIR tools in shared/tools/fhir.py and export from shared/tools/__init__.py.
"""
import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from shared.fhir_hook import extract_fhir_context
from shared.tools import (
    get_active_conditions,
    get_active_medications,
    get_patient_demographics,
    get_recent_observations,
)
from healthcare_agent.tools import (
    get_bc_program_eligibility,
    get_health_connect_registry_info,
    get_urgent_care_wait_times,
    recommend_care_level,
)

# ── Model selection ────────────────────────────────────────────────────────────
# Set HEALTHCARE_AGENT_MODEL in your .env to switch models.
#
# All models are handled via LiteLLM. Use the appropriate prefix:
#   HEALTHCARE_AGENT_MODEL=gemini/gemini-2.5-flash   (Google AI Studio, default)
#   HEALTHCARE_AGENT_MODEL=openai/gpt-4o
#   HEALTHCARE_AGENT_MODEL=anthropic/claude-sonnet-4-6
#   HEALTHCARE_AGENT_MODEL=vertex_ai/gemini-2.5-flash
# ──────────────────────────────────────────────────────────────────────────────
_model_name = os.getenv("HEALTHCARE_AGENT_MODEL", "gemini/gemini-2.5-flash")
_model = LiteLlm(model=_model_name)

root_agent = Agent(
    name="bc_navigator_agent",
    model=_model,
    description=(
        "A BC healthcare navigator that helps unattached patients (those without a "
        "family doctor) find care, understand their options, and access provincial "
        "programs. Covers urgent care wait times, symptom triage, MSP/PharmaCare "
        "eligibility, and Health Connect Registry registration."
    ),
    instruction=(
        "You are a compassionate BC healthcare navigator helping patients who do not have a family doctor. "
        "Your job is to help them get the right care, in the right place, at the right time.\n\n"

        "ALWAYS use your tools to provide accurate, up-to-date information — never guess.\n\n"

        "## Your capabilities\n"
        "1. **Urgent care wait times** — use get_urgent_care_wait_times(location) to find the "
        "   shortest wait near the patient. Always ask for or confirm their city/area first.\n"
        "2. **Symptom triage** — use recommend_care_level(symptoms) to advise whether the patient "
        "   should go to the ER, an urgent care / walk-in clinic, or use telehealth. "
        "   For anything that sounds like an emergency, always lead with 'Call 9-1-1'.\n"
        "3. **BC program eligibility** — use get_bc_program_eligibility() to explain MSP, "
        "   PharmaCare, and other provincial programs the patient may qualify for.\n"
        "4. **Health Connect Registry** — use get_health_connect_registry_info() to walk the "
        "   patient through registering to get matched with a family doctor or nurse practitioner.\n"
        "5. **FHIR health record** — if FHIR credentials are present in the session, use "
        "   get_patient_demographics, get_active_conditions, get_active_medications, and "
        "   get_recent_observations to personalise your guidance with the patient's actual record.\n\n"

        "## Tone\n"
        "Be warm, plain-spoken, and reassuring. Avoid medical jargon. "
        "Many patients are anxious — acknowledge that navigating the system without a doctor is stressful. "
        "Always end with a clear next step the patient can take right now.\n\n"

        "## Safety\n"
        "If a patient describes symptoms that could be life-threatening, immediately tell them to "
        "call 9-1-1 or go to the nearest ER — before providing any other information. "
        "Remind them that HealthLink BC (8-1-1) is free, 24/7, and staffed by registered nurses."
    ),
    tools=[
        # BC navigation tools
        get_urgent_care_wait_times,
        recommend_care_level,
        get_bc_program_eligibility,
        get_health_connect_registry_info,
        # FHIR tools (used when FHIR context is injected by the caller)
        get_patient_demographics,
        get_active_medications,
        get_active_conditions,
        get_recent_observations,
    ],
    # Runs before every LLM call.
    # Reads fhir_url, fhir_token, and patient_id from A2A message metadata
    # and writes them into session state so FHIR tools can call the FHIR server.
    # If FHIR context is absent, the BC navigation tools still work fine.
    before_model_callback=extract_fhir_context,
)
