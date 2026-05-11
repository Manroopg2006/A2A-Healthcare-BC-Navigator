"""
RAG tool — searches BC health documents to ground agent responses in real data.
"""
import os
import json
import chromadb
from chromadb.utils import embedding_functions
from google.adk.tools import ToolContext

# Initialize ChromaDB (runs locally, no external API needed)
_client = chromadb.PersistentClient(path="./bc_health_db")
_ef = embedding_functions.DefaultEmbeddingFunction()
_collection = _client.get_or_create_collection(
    name="bc_health_docs",
    embedding_function=_ef
)

def index_bc_documents():
    """
    Seeds the vector database with BC health knowledge.
    Run once on startup.
    """
    documents = [
        {
            "id": "upcc_chilliwack",
            "text": "Chilliwack UPCC is located at 45600 Menholm Rd, Chilliwack BC. Phone: 604-702-4900. Hours: Daily 8am-8pm. Accepts walk-ins for non-emergency urgent care. Fraser Health Virtual Care: 1-800-314-0999 available 10am-10pm daily.",
            "metadata": {"type": "clinic", "city": "chilliwack", "region": "fraser_health"}
        },
        {
            "id": "upcc_vancouver_ravensong",
            "text": "Raven Song UPCC is located at 2450 Ontario St, Vancouver BC. Phone: 604-709-6400. Hours: Mon-Fri 8am-8pm. Vancouver Coastal Health. Accepts walk-ins for urgent non-emergency care.",
            "metadata": {"type": "clinic", "city": "vancouver", "region": "vch"}
        },
        {
            "id": "pharmacare_overview",
            "text": "BC Fair PharmaCare helps BC residents pay for eligible prescription drugs, biologics and pharmacy services. Coverage is based on family net income. Deductible and family maximum are calculated annually. Common covered drugs include metformin for diabetes, lisinopril for hypertension, salbutamol inhalers for asthma. Special Authority required for some high-cost drugs. Register at gov.bc.ca/pharmacare or call 1-800-663-7100.",
            "metadata": {"type": "program", "program": "pharmacare"}
        },
        {
            "id": "health_connect_registry",
            "text": "BC Health Connect Registry helps unattached patients find a family doctor or nurse practitioner. Register at patientattachmentregistry.gov.bc.ca or call 1-877-967-2433. You need your BC Services Card. Wait times vary by region. Urban areas like Vancouver typically have longer waits than rural areas. You can still use UPCCs and walk-in clinics while waiting.",
            "metadata": {"type": "program", "program": "health_connect"}
        },
        {
            "id": "fraser_health_er_chilliwack",
            "text": "Chilliwack General Hospital Emergency Department is located at 45600 Menholm Rd, Chilliwack BC. Full service hospital, open 24/7. Part of Fraser Health. For non-emergency urgent care, use the Chilliwack UPCC first to avoid long ER waits. ER is for life-threatening emergencies only.",
            "metadata": {"type": "hospital", "city": "chilliwack", "region": "fraser_health"}
        },
        {
            "id": "811_healthlink",
            "text": "HealthLink BC 811 is a free, confidential health information and advice line available 24 hours a day, 7 days a week. Call 811 to speak with a registered nurse, pharmacist, or dietitian. Translation available in over 130 languages. Deaf or hard of hearing: call 7-1-1. Available across all of BC.",
            "metadata": {"type": "service", "service": "811"}
        },
        {
            "id": "virtual_care_bc",
            "text": "BC virtual care options for unattached patients: Fraser Health Virtual Care 1-800-314-0999 available 10am-10pm daily. Telus Health MyCare app for same-day video appointments. Maple virtual care platform. Some walk-in clinics offer same-day video appointments. Virtual care is appropriate for non-emergency conditions like cold, flu, rash, minor infections.",
            "metadata": {"type": "service", "service": "virtual_care"}
        },
        {
            "id": "diabetes_bc",
            "text": "BC Diabetes resources: BC Diabetes Prevention Program offers free lifestyle coaching. Covered medications under PharmaCare include metformin, insulin, and some newer diabetes drugs with Special Authority. Patients with diabetes and fever should seek same-day care as infection risk is higher. A1C testing covered under MSP.",
            "metadata": {"type": "condition", "condition": "diabetes"}
        },
        {
            "id": "msp_bc",
            "text": "BC Medical Services Plan (MSP) provides basic medical insurance for BC residents. Covers medically required services by physicians, supplementary health care practitioners, and laboratory services. To enrol or update: call 1-800-663-7100 or visit gov.bc.ca/msp. New BC residents must wait 3 months before coverage begins — consider interim insurance.",
            "metadata": {"type": "program", "program": "msp"}
        },
    ]
    
    # Add to vector DB if not already there
    existing = _collection.get()["ids"]
    for doc in documents:
        if doc["id"] not in existing:
            _collection.add(
                ids=[doc["id"]],
                documents=[doc["text"]],
                metadatas=[doc["metadata"]]
            )

# Index on import
index_bc_documents()


def search_bc_health_knowledge(query: str, tool_context: ToolContext) -> dict:
    """
    Searches BC health knowledge base to find relevant information
    about clinics, programs, and services for the patient's question.
    """
    results = _collection.query(
        query_texts=[query],
        n_results=3
    )
    
    if not results["documents"][0]:
        return {"results": [], "message": "No specific BC health information found for this query."}
    
    return {
        "query": query,
        "results": [
            {
                "content": doc,
                "metadata": meta
            }
            for doc, meta in zip(
                results["documents"][0],
                results["metadatas"][0]
            )
        ],
        "note": "Results retrieved from BC health knowledge base."
    }