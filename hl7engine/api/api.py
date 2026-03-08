# api.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from hl7engine.persistence.db import (
    init_db,
    get_messages,
    get_message_by_id,
    get_messages_by_type,
    get_messages_by_patient_id
)

app = FastAPI(title="HL7 Interface Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/messages")
def list_messages(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    message_type: Optional[str] = None
):
    if message_type:
        return get_messages_by_type(message_type, limit=limit, offset=offset)
    return get_messages(limit=limit, offset=offset)


@app.get("/messages/{msg_id}")
def get_message(msg_id: int):
    msg = get_message_by_id(msg_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return msg


@app.get("/patients/{patient_id}/messages")
def list_messages_by_patient(
    patient_id: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    return get_messages_by_patient_id(patient_id, limit=limit, offset=offset)


@app.get("/health")
def health():
    return {"status": "ok"}