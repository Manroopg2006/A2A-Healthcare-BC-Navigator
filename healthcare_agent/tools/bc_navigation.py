"""
BC Navigator tools — help unattached patients navigate the BC healthcare system.

Tools in this module do NOT require FHIR credentials. They provide BC-specific
navigation guidance: urgent care wait times, care-level triage, provincial program
eligibility, and Health Connect Registry registration info.

Adding new tools:
  1. Write a new function here.
  2. Export it from healthcare_agent/tools/__init__.py.
  3. Add it to the tools=[...] list in agent.py.
"""
import logging
import random
from datetime import datetime

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# ── Static BC data ─────────────────────────────────────────────────────────────

# Urgent care / walk-in centres keyed by BC city/region (lower-case).
# In production these would be fetched from the BC Health wait-times API or
# a real-time data source.  Here we simulate realistic ranges.
_URGENT_CARE_CENTRES = {
    "vancouver": [
        {"name": "UBC Hospital Urgent Care", "address": "2211 Wesbrook Mall, Vancouver", "phone": "604-822-7121", "hours": "8am–10pm daily"},
        {"name": "False Creek Urgent Care", "address": "555 W 8th Ave, Vancouver", "phone": "604-738-5151", "hours": "8am–8pm daily"},
        {"name": "Carepoint Health Broadway", "address": "1175 Denman St, Vancouver", "phone": "604-681-5338", "hours": "9am–9pm daily"},
        {"name": "Medicentres Vancouver", "address": "1641 Commercial Dr, Vancouver", "phone": "604-254-5554", "hours": "8am–8pm daily"},
    ],
    "surrey": [
        {"name": "Surrey Memorial Hospital Urgent Care", "address": "13750 96 Ave, Surrey", "phone": "604-581-2211", "hours": "24/7"},
        {"name": "Cloverdale Medicentre", "address": "5756 176 St, Surrey", "phone": "604-574-0200", "hours": "8am–8pm daily"},
        {"name": "Newton Medical Centre", "address": "13737 72 Ave, Surrey", "phone": "604-598-3031", "hours": "9am–6pm Mon–Fri"},
    ],
    "burnaby": [
        {"name": "Burnaby Hospital Urgent Care", "address": "3935 Kincaid St, Burnaby", "phone": "604-434-4211", "hours": "24/7"},
        {"name": "Metrotown Urgent Care", "address": "4885 Kingsway, Burnaby", "phone": "604-436-1212", "hours": "8am–9pm daily"},
    ],
    "richmond": [
        {"name": "Richmond Hospital Urgent Care", "address": "7000 Westminster Hwy, Richmond", "phone": "604-278-9711", "hours": "24/7"},
        {"name": "Richmond Urgent & Primary Care Centre", "address": "8100 Granville Ave, Richmond", "phone": "604-233-3350", "hours": "8am–10pm daily"},
    ],
    "victoria": [
        {"name": "Victoria General Hospital Urgent Care", "address": "1 Hospital Way, Victoria", "phone": "250-727-4212", "hours": "24/7"},
        {"name": "James Bay Urgent & Primary Care", "address": "938 Esquimalt Rd, Victoria", "phone": "250-519-3040", "hours": "8am–8pm daily"},
        {"name": "Gorge Road Urgent Care", "address": "63 Gorge Rd E, Victoria", "phone": "250-519-2000", "hours": "8am–8pm daily"},
    ],
    "kelowna": [
        {"name": "Kelowna General Hospital Urgent Care", "address": "2268 Pandosy St, Kelowna", "phone": "250-862-4000", "hours": "24/7"},
        {"name": "Orchard Park Urgent Care", "address": "1835 Gordon Dr, Kelowna", "phone": "250-868-0600", "hours": "8am–8pm daily"},
    ],
    "abbotsford": [
        {"name": "Abbotsford Regional Urgent Care", "address": "32900 Marshall Rd, Abbotsford", "phone": "604-851-4700", "hours": "24/7"},
    ],
    "prince george": [
        {"name": "University Hospital of Northern BC", "address": "1475 Edmonton St, Prince George", "phone": "250-565-2000", "hours": "24/7"},
    ],
}

_DEFAULT_REGION = "vancouver"

# Symptom keywords that indicate different care levels
_ER_KEYWORDS = {
    "chest pain", "heart attack", "stroke", "can't breathe", "difficulty breathing",
    "severe bleeding", "unconscious", "not breathing", "seizure", "overdose",
    "severe allergic", "anaphylaxis", "broken bone", "head injury", "vision loss",
    "slurred speech", "facial drooping", "arm weakness", "sudden severe headache",
    "coughing blood", "vomiting blood", "high fever infant",
}

_TELEHEALTH_KEYWORDS = {
    "prescription renewal", "refill", "cold", "flu", "mild cough", "sore throat",
    "rash", "minor infection", "mental health", "anxiety", "depression", "follow up",
    "follow-up", "test results", "lab results", "insomnia", "minor pain",
    "birth control", "contraception", "skin irritation", "ear pain",
}


def _simulate_wait_minutes(centre_name: str) -> int:
    """Simulate a realistic wait time. Hospital ERs run longer; walk-ins shorter."""
    seed = hash(centre_name + datetime.utcnow().strftime("%Y-%m-%d-%H")) % 100
    rng = random.Random(seed)
    if "Hospital" in centre_name:
        return rng.randint(45, 240)
    return rng.randint(10, 90)


# ── Tool: urgent care wait times ───────────────────────────────────────────────

def get_urgent_care_wait_times(location: str, tool_context: ToolContext) -> dict:
    """
    Returns current estimated wait times for urgent care and walk-in centres
    near the specified BC location.

    Args:
        location: City or area in BC (e.g. "Vancouver", "Surrey", "Victoria",
                  "Kelowna", "Burnaby", "Richmond", "Abbotsford", "Prince George").
                  Falls back to Vancouver if the location is not recognised.

    Returns a list of nearby centres sorted by estimated wait time (shortest first).
    """
    region = (location or "").strip().lower()
    logger.info("tool_get_urgent_care_wait_times location=%s", region)

    centres = _URGENT_CARE_CENTRES.get(region)
    if not centres:
        # Fuzzy match: check if the input contains a known region
        for key in _URGENT_CARE_CENTRES:
            if key in region or region in key:
                centres = _URGENT_CARE_CENTRES[key]
                region = key
                break

    if not centres:
        centres = _URGENT_CARE_CENTRES[_DEFAULT_REGION]
        region = _DEFAULT_REGION

    results = []
    for c in centres:
        wait = _simulate_wait_minutes(c["name"])
        results.append({
            "name":               c["name"],
            "address":            c["address"],
            "phone":              c["phone"],
            "hours":              c["hours"],
            "estimated_wait_min": wait,
            "wait_label":         (
                "Short (<30 min)"  if wait < 30  else
                "Moderate (30–60 min)" if wait < 60  else
                "Long (1–3 hrs)"   if wait < 180 else
                "Very long (3+ hrs)"
            ),
        })

    results.sort(key=lambda x: x["estimated_wait_min"])

    return {
        "status":        "success",
        "location":      region.title(),
        "retrieved_at":  datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "note":          "Wait times are estimated. Call ahead or check the facility website to confirm.",
        "centres":       results,
    }


# ── Tool: care-level triage ────────────────────────────────────────────────────

def recommend_care_level(symptoms: str, tool_context: ToolContext) -> dict:
    """
    Analyses the patient's described symptoms and recommends the most appropriate
    level of care in BC: Emergency Room, Urgent Care / Walk-in, or Telehealth.

    Args:
        symptoms: Free-text description of the patient's current symptoms or concern
                  (e.g. "chest pain and shortness of breath", "need a prescription refill").

    Returns a care-level recommendation with rationale and BC-specific next steps.
    """
    logger.info("tool_recommend_care_level symptoms=%s", symptoms[:80])
    text = (symptoms or "").lower()

    er_matches        = [kw for kw in _ER_KEYWORDS        if kw in text]
    telehealth_matches = [kw for kw in _TELEHEALTH_KEYWORDS if kw in text]

    if er_matches:
        level = "Emergency Room (911 or nearest ER)"
        rationale = (
            f"Your symptoms ({', '.join(er_matches)}) may indicate a life-threatening emergency. "
            "Do not drive yourself — call 9-1-1 or have someone take you to the nearest ER immediately."
        )
        next_steps = [
            "Call 9-1-1 if symptoms are severe or worsening.",
            "Go to the nearest hospital Emergency Room.",
            "BC Emergency departments are open 24/7 and cannot turn you away.",
        ]
        urgency = "URGENT — seek care immediately"

    elif telehealth_matches:
        level = "Telehealth / Virtual Care"
        rationale = (
            f"Your concern ({', '.join(telehealth_matches)}) is suitable for a virtual visit, "
            "saving you time and a trip to a clinic."
        )
        next_steps = [
            "Call HealthLink BC at 8-1-1 (24/7, free, speak with a nurse).",
            "Use BC's virtual care options: Telus Health MyCare, Maple, or your MSP-covered provider.",
            "Many walk-in clinics now offer same-day video appointments.",
        ]
        urgency = "Non-urgent — telehealth appropriate"

    else:
        level = "Urgent Care Centre or Walk-in Clinic"
        rationale = (
            "Your symptoms do not appear to require an ER visit but should be assessed "
            "by a clinician today or within the next day."
        )
        next_steps = [
            "Visit the nearest urgent care centre or walk-in clinic.",
            "Use the get_urgent_care_wait_times tool to find the shortest wait near you.",
            "Call HealthLink BC at 8-1-1 if symptoms worsen before you are seen.",
        ]
        urgency = "Semi-urgent — be seen today or tomorrow"

    return {
        "status":          "success",
        "recommended_care": level,
        "urgency":         urgency,
        "rationale":       rationale,
        "next_steps":      next_steps,
        "healthlink_bc":   "8-1-1 (24/7 nurse line, free)",
        "disclaimer":      (
            "This is general guidance only and does not replace professional medical advice. "
            "When in doubt, call 8-1-1 or go to the ER."
        ),
    }


# ── Tool: BC program eligibility ───────────────────────────────────────────────

def get_bc_program_eligibility(tool_context: ToolContext) -> dict:
    """
    Returns information about BC government health programs the patient may qualify for,
    including MSP, PharmaCare, and supplementary benefit programs.

    Uses the patient's demographics (province, age) from the FHIR record when available.
    No arguments required — patient context comes from the session state.
    """
    logger.info("tool_get_bc_program_eligibility")

    # Attempt to pull patient age/province from session state (set by FHIR hook if available)
    # These may not be populated if FHIR context isn't present — that's fine.
    birth_date = tool_context.state.get("patient_birth_date", "")
    age = None
    if birth_date:
        try:
            born = datetime.strptime(birth_date[:10], "%Y-%m-%d")
            age = (datetime.utcnow() - born).days // 365
        except ValueError:
            pass

    programs = [
        {
            "program":     "Medical Services Plan (MSP)",
            "description": "BC's universal health insurance — covers medically necessary doctor and hospital visits.",
            "eligibility": "BC resident, Canadian citizen or permanent resident (or eligible non-citizen). 3-month waiting period for new BC residents.",
            "how_to_apply": "Online at gov.bc.ca/msp or call Health Insurance BC at 1-800-663-7100.",
            "cost":        "Premium-free since Jan 2020.",
            "url":         "https://www2.gov.bc.ca/gov/content/health/health-drug-coverage/msp",
        },
        {
            "program":     "BC PharmaCare",
            "description": "Helps BC residents pay for eligible prescription drugs and medical supplies.",
            "eligibility": "Must have MSP. Multiple plans available (Fair PharmaCare, Plan B for social assistance recipients, Plan C for seniors, etc.).",
            "how_to_apply": "Register for Fair PharmaCare online at gov.bc.ca/pharmacare. Income-based — use your tax return.",
            "cost":        "Annual deductible based on family income. Lower-income families may have $0 deductible.",
            "url":         "https://www2.gov.bc.ca/gov/content/health/health-drug-coverage/pharmacare-for-bc-residents",
        },
        {
            "program":     "BC Mental Health Support Line",
            "description": "Free, confidential mental health and substance use support.",
            "eligibility": "All BC residents.",
            "how_to_apply": "Call or text 310-6789 (no area code needed). Available 24/7.",
            "cost":        "Free.",
            "url":         "https://www2.gov.bc.ca/gov/content/health/managing-your-health/mental-health-substance-use",
        },
        {
            "program":     "Healthy Kids Program",
            "description": "Covers basic dental, optical, and hearing services for children in low-income families.",
            "eligibility": "Children under 19 whose families receive income or disability assistance, or have low income.",
            "how_to_apply": "Apply through your local Community Integration Services office.",
            "cost":        "Free for eligible families.",
            "url":         "https://www2.gov.bc.ca/gov/content/health/health-drug-coverage/healthy-kids",
        },
    ]

    # Add senior-specific programs if patient appears to be 65+
    if age is not None and age >= 65:
        programs.append({
            "program":     "BC PharmaCare Plan C (Seniors)",
            "description": "Enhanced PharmaCare coverage for BC residents 65 and older.",
            "eligibility": "BC resident aged 65+ with MSP coverage.",
            "how_to_apply": "Automatically enrolled when you turn 65 and have MSP. Confirm at 1-800-663-7100.",
            "cost":        "Income-based deductible, lower than Fair PharmaCare for most seniors.",
            "url":         "https://www2.gov.bc.ca/gov/content/health/health-drug-coverage/pharmacare-for-bc-residents/our-pharmacare-plans/plan-c",
        })
        programs.append({
            "program":     "Bus Pass Program (Seniors)",
            "description": "Subsidised transit pass for low-income seniors.",
            "eligibility": "BC residents 65+ receiving Guaranteed Income Supplement (GIS).",
            "how_to_apply": "Apply through Service Canada or BC Transit.",
            "cost":        "Subsidised monthly pass.",
            "url":         "https://www2.gov.bc.ca/gov/content/transportation/passenger-travel/bus-pass-program",
        })

    return {
        "status":   "success",
        "programs": programs,
        "note":     (
            "Eligibility details may change. Visit gov.bc.ca or call Health Insurance BC "
            "at 1-800-663-7100 for the most current information."
        ),
    }


# ── Tool: Health Connect Registry ─────────────────────────────────────────────

def get_health_connect_registry_info(tool_context: ToolContext) -> dict:
    """
    Provides step-by-step instructions for registering on the BC Health Connect Registry
    to be matched with a family doctor or nurse practitioner.

    No arguments required.
    """
    logger.info("tool_get_health_connect_registry_info")

    return {
        "status":      "success",
        "program":     "BC Health Connect Registry",
        "description": (
            "The Health Connect Registry is the official BC government waitlist that "
            "matches unattached patients (people without a family doctor or nurse "
            "practitioner) with available primary care providers in their area."
        ),
        "how_to_register": [
            "Go to https://www.healthconnectbc.ca/ (or search 'BC Health Connect Registry').",
            "Click 'Register' and create an account with your personal health number (PHN) and BC Services Card.",
            "Enter your contact info, location, and any preferences (e.g. language, gender of provider).",
            "You will receive a confirmation email. Keep your contact details up to date.",
            "When a provider in your area has an opening, you will be contacted by phone or email.",
        ],
        "what_you_need": [
            "BC Services Card (or driver's licence for identity verification).",
            "Your Personal Health Number (PHN) — found on your BC Services Card or MSP documentation.",
            "A valid email address and phone number.",
        ],
        "tips": [
            "Register even if you have a temporary doctor — your position on the list is preserved.",
            "Update your address if you move, so you are matched to providers near you.",
            "While waiting, use HealthLink BC (8-1-1) for advice, or a local urgent care clinic for non-emergency needs.",
            "Some communities have Urgent and Primary Care Centres (UPCCs) that accept walk-in patients for ongoing care.",
        ],
        "contact":     "HealthLink BC: 8-1-1 (24/7, free nurse advice line)",
        "url":         "https://www.healthconnectbc.ca/",
    }
