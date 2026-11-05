from uuid import UUID

from fastapi import APIRouter, Request, Response

from app.api.dependencies import IdempotencyDep, SessionDep, UserDep
from app.core.common import BusinessError, envelope
from app.db.models import Task
from app.jobs.repository import submit
from app.schemas import AudioGenerate, ConfirmScript, Envelope, ScriptGenerate, ScriptView, TaskAccepted
from app.services.scripts import confirm_script
from app.services.views import owned_project, owned_script, script_view, task_view

router = APIRouter(prefix="/api/v1")


@router.post("/projects/{project_id}/script/generate", status_code=202, response_model=Envelope[TaskAccepted], tags=["脚本模块"], summary="提交模拟脚本任务（10秒）")
def generate_script(project_id: UUID, body: ScriptGenerate, request: Request, response: Response,
                    session: SessionDep, user: UserDep, key: IdempotencyDep):
    data, response.status_code = submit(session, user, str(project_id), "script", body, key, request.app.state.settings)
    response.headers["Location"] = data["status_url"]
    response.headers["Retry-After"] = "1"
    return envelope(request, data, "模拟脚本任务")


@router.get("/scripts/{script_id}", response_model=Envelope[ScriptView], tags=["脚本模块"], summary="脚本详情")
def get_script(script_id: UUID, request: Request, session: SessionDep, user: UserDep):
    return envelope(request, script_view(session, owned_script(session, str(script_id), user)))


@router.post("/scripts/{script_id}/confirm", response_model=Envelope[dict], tags=["脚本模块"], summary="确认脚本")
def confirm(script_id: UUID, body: ConfirmScript, request: Request, session: SessionDep, user: UserDep):
    return envelope(request, confirm_script(session, user, str(script_id), body))


@router.post("/projects/{project_id}/audio/generate", status_code=202, response_model=Envelope[TaskAccepted], tags=["语音模块"], summary="提交模拟音频任务（10秒）")
def generate_audio(project_id: UUID, body: AudioGenerate, request: Request, response: Response,
                   session: SessionDep, user: UserDep, key: IdempotencyDep):
    data, response.status_code = submit(session, user, str(project_id), "audio", body, key, request.app.state.settings)
    response.headers["Location"] = data["status_url"]
    response.headers["Retry-After"] = "1"
    return envelope(request, data, "模拟音频任务：返回固定测试音，非正文朗读")


@router.get("/tasks/{task_id}", response_model=Envelope[dict], tags=["任务模块"], summary="查询任务状态")
def get_task(task_id: UUID, request: Request, session: SessionDep, user: UserDep):
    task = session.get(Task, str(task_id))
    if task is None or task.user_id != user:
        raise BusinessError("RESOURCE_NOT_FOUND", "任务不存在", 404)
    owned_project(session, task.project_id, user)
    return envelope(request, task_view(task))
