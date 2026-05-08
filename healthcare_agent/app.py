"""
healthcare_agent — A2A application entry point.

Start the server with:
    uvicorn healthcare_agent.app:a2a_app --host 0.0.0.0 --port 8001

The agent card is served publicly at:
    GET http://localhost:8001/.well-known/agent-card.json

All other endpoints require an X-API-Key header (see shared/middleware.py).
"""
import os

from a2a.types import AgentSkill
from shared.app_factory import create_a2a_app

from .agent import root_agent

print(os.getenv('PO_PLATFORM_BASE_URL'))

a2a_app = create_a2a_app(
    agent=root_agent,
    name="bc_navigator_agent",
    description=(
        "A BC healthcare navigator that helps unattached patients (those without a "
        "family doctor) find care, understand their options, and access provincial "
        "programs. Covers urgent care wait times, symptom triage, MSP/PharmaCare "
        "eligibility, and Health Connect Registry registration."
    ),
    url=os.getenv("HEALTHCARE_AGENT_URL", os.getenv("BASE_URL", "http://localhost:8001")),
    port=8001,
    # FHIR context is optional for this agent — the BC navigation tools work without it.
    # When FHIR credentials are supplied, the agent personalises guidance using the
    # patient's real health record.
    fhir_extension_uri=f"{os.getenv('PO_PLATFORM_BASE_URL', 'http://localhost:5139')}/schemas/a2a/v1/fhir-context",
    fhir_scopes=[
        {"name": "patient/Patient.rs",           "required": False},  # get_patient_demographics
        {"name": "patient/MedicationRequest.rs", "required": False},  # get_active_medications
        {"name": "patient/Condition.rs",         "required": False},  # get_active_conditions
        {"name": "patient/Observation.rs",       "required": False},  # get_recent_observations
    ],
    skills=[
        # BC Navigator skills
        AgentSkill(
            id="urgent-care-wait-times",
            name="urgent-care-wait-times",
            description="Find urgent care and walk-in centres near a BC location with estimated wait times.",
            tags=["bc", "urgent-care", "wait-times", "navigator"],
        ),
        AgentSkill(
            id="symptom-triage",
            name="symptom-triage",
            description="Analyse symptoms and recommend the right level of care: ER, walk-in, or telehealth.",
            tags=["bc", "triage", "symptoms", "navigator"],
        ),
        AgentSkill(
            id="bc-program-eligibility",
            name="bc-program-eligibility",
            description="Explain BC government health programs the patient may qualify for (MSP, PharmaCare, etc.).",
            tags=["bc", "msp", "pharmacare", "programs", "navigator"],
        ),
        AgentSkill(
            id="health-connect-registry",
            name="health-connect-registry",
            description="Guide the patient through registering on the BC Health Connect Registry to get a family doctor.",
            tags=["bc", "family-doctor", "health-connect", "navigator"],
        ),
        # FHIR skills (used when FHIR context is supplied by the caller)
        AgentSkill(
            id="patient-demographics",
            name="patient-demographics",
            description="Retrieve patient demographics like name, DOB, and contacts from the FHIR record.",
            tags=["demographics", "fhir"],
        ),
        AgentSkill(
            id="active-medications",
            name="active-medications",
            description="Get a list of the patient's active medications and dosages from the FHIR record.",
            tags=["medications", "fhir"],
        ),
        AgentSkill(
            id="active-conditions",
            name="active-conditions",
            description="Get the patient's active conditions and diagnoses from the FHIR record.",
            tags=["conditions", "fhir"],
        ),
        AgentSkill(
            id="recent-observations",
            name="recent-observations",
            description="Retrieve recent vitals, lab results, and social history from the FHIR record.",
            tags=["observations", "fhir"],
        ),
    ],
)
