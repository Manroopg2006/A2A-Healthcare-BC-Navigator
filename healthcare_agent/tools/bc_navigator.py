"""
BC Navigator Tools — helps unattached BC patients navigate the healthcare system.
"""
from google.adk.tools import ToolContext


def recommend_care_level(symptoms: str, tool_context: ToolContext) -> dict:
    """
    Based on the patient's symptoms and their existing conditions,
    recommends the appropriate level of care in BC:
    ER, Urgent Care, Walk-in Clinic, Telehealth, or 811.
    """
    conditions = tool_context.state.get("active_conditions", "unknown")

    emergency_keywords = [
        "chest pain", "difficulty breathing", "stroke", "unconscious",
        "severe bleeding", "overdose", "heart attack", "can't breathe",
        "seizure", "severe allergic reaction", "anaphylaxis"
    ]
    urgent_keywords = [
        "fever", "infection", "sprain", "cut", "fracture", "vomiting",
        "diarrhea", "rash", "earache", "eye pain", "urinary tract"
    ]

    symptoms_lower = symptoms.lower()

    if any(kw in symptoms_lower for kw in emergency_keywords):
        return {
            "recommendation": "EMERGENCY ROOM (911 or nearest ER)",
            "reason": "Your symptoms may be life-threatening. Call 911 or go to the nearest ER immediately.",
            "bc_resource": "Dial 911",
        }
    elif any(kw in symptoms_lower for kw in urgent_keywords):
        return {
            "recommendation": "Urgent Care Centre or Walk-in Clinic",
            "reason": "Your symptoms need same-day attention but are not life-threatening.",
            "bc_resource": "Find wait times at medimap.ca or call 811 for guidance.",
        }
    else:
        return {
            "recommendation": "Telehealth or 811",
            "reason": "Your symptoms can likely be assessed remotely.",
            "bc_resource": "Call 811 (HealthLink BC) anytime — free nurse advice line available 24/7.",
        }


def find_bc_urgent_care(city: str, tool_context: ToolContext) -> dict:
    """
    Returns a list of Urgent and Primary Care Centres (UPCCs) and
    walk-in clinics in the specified BC city.
    """
    clinics = {
        "vancouver": [
            {"name": "Vancouver UPCC – Raven Song", "address": "2450 Ontario St, Vancouver", "phone": "604-709-6400", "hours": "Mon-Fri 8am-8pm"},
            {"name": "Vancouver UPCC – Cedar Cottage", "address": "4110 Kaslo St, Vancouver", "phone": "604-215-9922", "hours": "Daily 8am-8pm"},
            {"name": "Spectrum Health Walk-in", "address": "1669 Davie St, Vancouver", "phone": "604-669-1669", "hours": "Daily 9am-9pm"},
        ],
        "surrey": [
            {"name": "Surrey UPCC – Guildford", "address": "10236 152A St, Surrey", "phone": "604-587-3870", "hours": "Daily 8am-8pm"},
            {"name": "Surrey UPCC – Newton", "address": "13711 72 Ave, Surrey", "phone": "604-543-6700", "hours": "Daily 8am-8pm"},
        ],
        "chilliwack": [
            {"name": "Chilliwack UPCC", "address": "45600 Menholm Rd, Chilliwack", "phone": "604-702-4900", "hours": "Daily 8am-8pm"},
            {"name": "Chilliwack Walk-in Clinic", "address": "8491 Cook Rd, Chilliwack", "phone": "604-793-9696", "hours": "Mon-Sat 9am-5pm"},
        ],
        "kelowna": [
            {"name": "Kelowna UPCC", "address": "1340 Ellis St, Kelowna", "phone": "250-870-4636", "hours": "Daily 8am-8pm"},
        ],
        "victoria": [
            {"name": "Victoria UPCC – Quadra Village", "address": "905 Quadra St, Victoria", "phone": "250-519-3450", "hours": "Daily 8am-8pm"},
            {"name": "James Bay Walk-in", "address": "230 Menzies St, Victoria", "phone": "250-388-9934", "hours": "Daily 9am-5pm"},
        ],
        "abbotsford": [
            {"name": "Abbotsford UPCC", "address": "31764 Marshall Rd, Abbotsford", "phone": "604-870-7800", "hours": "Daily 8am-8pm"},
        ],
        "kamloops": [
            {"name": "Kamloops UPCC", "address": "235 Lansdowne St, Kamloops", "phone": "250-314-2840", "hours": "Daily 8am-8pm"},
        ],
        "prince george": [
            {"name": "Prince George UPCC", "address": "1780 Nicholson St, Prince George", "phone": "250-565-2000", "hours": "Daily 8am-8pm"},
        ],
    }

    city_lower = city.lower().strip()
    results = clinics.get(city_lower)

    if not results:
        return {
            "message": f"No specific listings found for {city}.",
            "suggestion": "Visit medimap.ca to find real-time wait times near you, or call 811 for help finding care.",
        }

    return {
        "city": city,
        "clinics": results,
        "tip": "Check medimap.ca for live wait times before you go.",
        "bc_nurse_line": "Call 811 anytime for free advice from a registered nurse.",
    }


def check_bc_program_eligibility(tool_context: ToolContext) -> dict:
    """
    Checks which BC health programs the patient may be eligible for
    based on their demographics, conditions, and medications.
    """
    demographics = tool_context.state.get("patient_demographics", {})
    conditions = tool_context.state.get("active_conditions", [])
    medications = tool_context.state.get("active_medications", [])

    programs = []

    # Everyone in BC qualifies for these
    programs.append({
        "program": "BC Health Connect Registry",
        "description": "Register to be matched with a family doctor or nurse practitioner.",
        "how_to_apply": "Visit patientattachmentregistry.gov.bc.ca or call 1-877-967-2433",
        "eligible": True,
    })

    programs.append({
        "program": "HealthLink BC (811)",
        "description": "Free 24/7 health advice from registered nurses, dietitians, and pharmacists.",
        "how_to_apply": "Call 811 anytime. Translation available in 130+ languages.",
        "eligible": True,
    })

    programs.append({
        "program": "BC PharmaCare (Fair PharmaCare)",
        "description": "BC's income-based drug coverage program that helps pay for eligible prescription drugs.",
        "how_to_apply": "Register at gov.bc.ca/pharmacare or call 1-800-663-7100",
        "eligible": True,
    })

    # Check for diabetes-specific programs
    conditions_str = str(conditions).lower()
    if "diabetes" in conditions_str:
        programs.append({
            "program": "BC Diabetes Prevention Program",
            "description": "Free lifestyle coaching program for people at risk of or living with Type 2 diabetes.",
            "how_to_apply": "Ask your care provider for a referral or visit bcdiabetes.ca",
            "eligible": True,
        })

    # Check for mental health
    if any(kw in conditions_str for kw in ["depression", "anxiety", "mental health", "bipolar", "ptsd"]):
        programs.append({
            "program": "BC Mental Health Support Line",
            "description": "Free confidential mental health support available 24/7.",
            "how_to_apply": "Call 310-6789 (no area code needed) anytime.",
            "eligible": True,
        })

    return {
        "eligible_programs": programs,
        "note": "This is a general overview. Eligibility may vary. Call 811 for personalized guidance.",
    }


def get_bc_family_doctor_registration(tool_context: ToolContext) -> dict:
    """
    Provides step-by-step instructions for registering to get a family doctor in BC.
    """
    return {
        "program": "BC Health Connect Registry",
        "steps": [
            "1. Visit patientattachmentregistry.gov.bc.ca",
            "2. Click 'Register as a Patient'",
            "3. Enter your BC Services Card number and personal details",
            "4. Select your preferred location and language",
            "5. You will be matched with available family doctors or nurse practitioners in your area",
            "6. You will receive a notification when a provider accepts you",
        ],
        "average_wait": "Wait times vary by region. Urban areas like Vancouver may take longer than rural areas.",
        "while_you_wait": [
            "Call 811 for free nurse advice anytime",
            "Use BC's Urgent and Primary Care Centres (UPCCs) for non-emergency care",
            "Check medimap.ca for walk-in clinic wait times near you",
            "Virtual care options: Telus Health MyCare, Maple, or BC's virtual services",
        ],
        "tip": "Register even if you currently have a doctor — your registration is deactivated once you're attached.",
    }