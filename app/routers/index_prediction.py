import json
import asyncio
import logging

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

from app.services.index_prediction_service import IndexPredictionService
from app.services.websocket_manager import get_websocket_manager
from app.routers.auth_db import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/index-prediction", tags=["index-prediction"])


class PredictionRequest(BaseModel):
    expectation_id: Optional[str] = None
    target_indices: List[str] = Field(default_factory=lambda: [
        "000016.SH", "000300.SH", "000905.SH", "000852.SH", "000688.SH", "399006.SZ"
    ])
    research_depth: str = "标准"
    selected_analysts: List[str] = Field(default_factory=lambda: [
        "tech", "sentiment", "macro", "valuation"
    ])
    quick_analysis_model: Optional[str] = None
    deep_analysis_model: Optional[str] = None
    analysis_date: Optional[str] = None


class PredictionTaskResponse(BaseModel):
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int = 0
    current_step: Optional[str] = None
    current_step_description: Optional[str] = None
    elapsed_seconds: float = 0
    estimated_remaining_seconds: Optional[float] = None


@router.post("/analyze", response_model=PredictionTaskResponse)
async def start_analysis(request: PredictionRequest, user: dict = Depends(get_current_user)):
    svc = IndexPredictionService()
    task_id = await svc.start_prediction(str(user["id"]), request.model_dump())
    return PredictionTaskResponse(task_id=task_id, status="pending")


@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str, user: dict = Depends(get_current_user)):
    svc = IndexPredictionService()
    progress = svc.get_task_progress(task_id)
    if progress:
        stages = progress.get("stages", [])
        running = [s for s in stages if s.get("status") == "running"]
        completed = [s for s in stages if s.get("status") == "completed"]
        current_name = running[0]["name"] if running else (completed[-1]["name"] if completed else "分析中")
        return TaskStatusResponse(
            task_id=task_id,
            status=progress.get("status", "running"),
            progress=progress.get("progress", 0),
            current_step=current_name,
            current_step_description="",
            elapsed_seconds=progress.get("elapsed_seconds", 0),
            estimated_remaining_seconds=progress.get("estimated_remaining_seconds"),
        )
    doc = await svc.get_task_status(task_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(
        task_id=task_id,
        status=doc.get("status", "unknown"),
        progress=100 if doc.get("status") == "completed" else 0,
        elapsed_seconds=doc.get("elapsed_seconds", 0),
    )


@router.get("/tasks/{task_id}/result")
async def get_task_result(task_id: str, user: dict = Depends(get_current_user)):
    svc = IndexPredictionService()
    result = await svc.get_task_result(task_id)
    if result is None:
        doc = await svc.get_task_status(task_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"task_id": task_id, "status": doc.get("status"), "result": None}
    return {"task_id": task_id, "status": "completed", "result": result}


@router.get("/history")
async def get_history(user: dict = Depends(get_current_user), skip: int = 0, limit: int = 20):
    svc = IndexPredictionService()
    return await svc.get_history(str(user["id"]), skip=skip, limit=limit)


@router.get("/tasks")
async def list_tasks(
    user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    svc = IndexPredictionService()
    tasks, total = await svc.list_all_tasks(str(user["id"]), status, skip, limit)
    return {"tasks": tasks, "total": total}


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, user: dict = Depends(get_current_user)):
    svc = IndexPredictionService()
    ok = await svc.cancel_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found or not running")
    return {"ok": True}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, user: dict = Depends(get_current_user)):
    svc = IndexPredictionService()
    ok = await svc.delete_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


@router.post("/tasks/{task_id}/mark-failed")
async def mark_task_failed(task_id: str, user: dict = Depends(get_current_user)):
    svc = IndexPredictionService()
    ok = await svc.mark_task_failed(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


@router.post("/tasks/{task_id}/retry")
async def retry_task(task_id: str, user: dict = Depends(get_current_user)):
    svc = IndexPredictionService()
    new_task = await svc.retry_task(task_id, str(user["id"]))
    if not new_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": new_task["task_id"], "status": new_task["status"]}


@router.get("/indices")
async def get_indices():
    svc = IndexPredictionService()
    return await svc.get_indices_metadata()


@router.get("/sectors")
async def get_sectors():
    svc = IndexPredictionService()
    return await svc.get_sectors()


@router.websocket("/ws/index-prediction/{task_id}")
async def websocket_index_prediction(websocket: WebSocket, task_id: str):
    ws_manager = get_websocket_manager()
    await ws_manager.connect(websocket, task_id)
    try:
        svc = IndexPredictionService()
        await websocket.send_text(json.dumps({
            "type": "connected",
            "task_id": task_id,
        }))
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=3)
            except asyncio.TimeoutError:
                progress = svc.get_task_progress(task_id)
                if progress:
                    stages = progress.get("stages", [])
                    if stages:
                        await websocket.send_text(json.dumps({
                            "type": "pipeline_status",
                            "stages": stages,
                            "progress": progress.get("progress", 0),
                            "elapsed_seconds": progress.get("elapsed_seconds", 0),
                        }))
                continue
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket, task_id)


_STAGE_NAMES = [
    "指数技术面分析师", "资金情绪分析师", "宏观政策分析师", "指数估值分析师",
    "板块主线分析师", "指数影响分析师", "多空辩论",
    "研究裁判", "指数交易员", "风险辩论", "风险裁判",
]


def _build_pipeline_from_step(current_step: str) -> list:
    idx = -1
    for i, name in enumerate(_STAGE_NAMES):
        if name in current_step or current_step in name:
            idx = i
            break
    stages = []
    for i, name in enumerate(_STAGE_NAMES):
        if i < idx:
            stages.append({"id": name, "name": name, "status": "completed", "time": 0})
        elif i == idx:
            stages.append({"id": name, "name": name, "status": "running", "time": 0})
        else:
            stages.append({"id": name, "name": name, "status": "pending", "time": 0})
    return stages
