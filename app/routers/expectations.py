from fastapi import APIRouter, HTTPException, Depends
from typing import List, Any

from app.models.expectation import ExpectationCreate, ExpectationUpdate, ExpectationResponse
from app.services.expectation_service import ExpectationService
from app.routers.auth_db import get_current_user

router = APIRouter(prefix="/api/expectations", tags=["expectations"])


@router.post("", response_model=ExpectationResponse)
async def create_expectation(data: ExpectationCreate, user: dict = Depends(get_current_user)):
    svc = ExpectationService()
    doc = await svc.create(str(user["id"]), data.model_dump())
    return _format_response(doc)


@router.get("")
async def list_expectations(user: dict = Depends(get_current_user), skip: int = 0, limit: int = 50):
    svc = ExpectationService()
    docs = await svc.list_by_user(str(user["id"]), skip=skip, limit=limit)
    return [_format_response(d) for d in docs]


@router.get("/active")
async def get_active_expectation(user: dict = Depends(get_current_user)):
    svc = ExpectationService()
    doc = await svc.get_active(str(user["id"]))
    if not doc:
        raise HTTPException(status_code=404, detail="No active expectation found")
    return _format_response(doc)


@router.get("/{expectation_id}")
async def get_expectation(expectation_id: str, user: dict = Depends(get_current_user)):
    svc = ExpectationService()
    doc = await svc.get_by_id(expectation_id, str(user["id"]))
    if not doc:
        raise HTTPException(status_code=404, detail="Expectation not found")
    return _format_response(doc)


@router.put("/{expectation_id}")
async def update_expectation(expectation_id: str, data: ExpectationUpdate, user: dict = Depends(get_current_user)):
    svc = ExpectationService()
    doc = await svc.update(expectation_id, str(user["id"]), data.model_dump(exclude_none=True))
    if not doc:
        raise HTTPException(status_code=404, detail="Expectation not found")
    return _format_response(doc)


@router.delete("/{expectation_id}")
async def delete_expectation(expectation_id: str, user: dict = Depends(get_current_user)):
    svc = ExpectationService()
    ok = await svc.delete(expectation_id, str(user["id"]))
    if not ok:
        raise HTTPException(status_code=404, detail="Expectation not found")
    return {"ok": True}


@router.post("/{expectation_id}/activate")
async def activate_expectation(expectation_id: str, user: dict = Depends(get_current_user)):
    svc = ExpectationService()
    ok = await svc.set_active(expectation_id, str(user["id"]))
    if not ok:
        raise HTTPException(status_code=404, detail="Expectation not found or already active")
    return {"ok": True}


@router.post("/{expectation_id}/copy")
async def copy_expectation(expectation_id: str, user: dict = Depends(get_current_user)):
    svc = ExpectationService()
    doc = await svc.copy(expectation_id, str(user["id"]))
    if not doc:
        raise HTTPException(status_code=404, detail="Expectation not found")
    return _format_response(doc)


def _format_response(doc: dict) -> dict:
    if "_id" in doc:
        doc["id"] = doc["_id"]
    elif "id" not in doc:
        doc["id"] = doc.get("_id", "")
    if isinstance(doc.get("content"), str):
        doc["content"] = {"policy_long_term": doc["content"]}
    return doc
