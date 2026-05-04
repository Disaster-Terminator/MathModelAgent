import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from app.config.setting import settings
from app.utils.common_utils import ensure_safe_task_id, get_config_template
from app.schemas.enums import CompTemplate
from app.services.redis_manager import redis_manager
from app.utils.log_util import logger
import httpx

router = APIRouter()


def _require_safe_task_id(task_id: str) -> str:
    try:
        return ensure_safe_task_id(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="非法任务ID") from exc


def _load_task_messages_from_file(task_id: str) -> list[dict]:
    safe_task_id = _require_safe_task_id(task_id)
    message_file = Path("logs/messages") / f"{safe_task_id}.json"
    if not message_file.exists():
        return []

    try:
        with open(message_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"读取任务消息文件失败: {str(e)}")
        return []


@router.get("/")
async def root():
    return {"message": "Hello World"}


@router.get("/config")
async def config():
    return {
        "environment": settings.ENV,
        "model": settings.MODEL,
        "litellm_api_url": settings.LITELLM_API_URL,
        "max_chat_turns": settings.MAX_CHAT_TURNS,
        "max_retries": settings.MAX_RETRIES,
        "CORS_ALLOW_ORIGINS": settings.CORS_ALLOW_ORIGINS,
    }


@router.get("/writer_seque")
async def get_writer_seque():
    # 返回论文顺序
    config_template: dict = get_config_template(CompTemplate.CHINA)
    return list(config_template.keys())


@router.get("/messages")
async def get_task_messages(task_id: str):
    return _load_task_messages_from_file(task_id)


@router.get("/track")
async def track(task_id: str):
    # 获取任务的token使用情况

    pass


@router.get("/status")
async def get_service_status():
    """获取各个服务的状态"""
    status = {
        "backend": {"status": "running", "message": "Backend service is running"},
        "redis": {"status": "unknown", "message": "Redis connection status unknown"}
    }

    # 检查Redis连接状态
    try:
        redis_client = await redis_manager.get_client()
        await redis_client.ping()
        status["redis"] = {"status": "running", "message": "Redis connection is healthy"}
    except Exception as e:
        logger.error(f"Redis connection failed: {str(e)}")
        status["redis"] = {"status": "error", "message": f"Redis connection failed: {str(e)}"}

    return status


@router.get("/health/proxy")
async def health_proxy():
    """检测后端到上游 LiteLLM Proxy 的连通性（不暴露 API Key）"""
    base_url = settings.LITELLM_API_URL
    if not base_url:
        return {"reachable": False, "error": "LITELLM_API_URL not configured"}

    try:
        url = base_url.rstrip("/") + "/models"
        async with httpx.AsyncClient(timeout=10) as client:
            headers = {}
            if settings.LITELLM_API_KEY:
                headers["Authorization"] = f"Bearer {settings.LITELLM_API_KEY}"
            response = await client.get(url, headers=headers)

        if response.status_code == 200:
            return {"reachable": True, "status": 200, "note": "proxy reachable and key valid"}
        elif response.status_code == 401:
            return {"reachable": True, "status": 401, "error": "proxy reachable but API Key rejected"}
        else:
            return {"reachable": True, "status": response.status_code, "error": response.text[:200]}
    except Exception as e:
        return {"reachable": False, "error": str(e)}


@router.post("/reset-api-config")
async def reset_api_config():
    """清空前端保存的各 agent 专属配置，强制回退到 .env.dev 全局配置"""
    try:
        settings.COORDINATOR_API_KEY = None
        settings.COORDINATOR_MODEL = None
        settings.COORDINATOR_BASE_URL = None
        settings.MODELER_API_KEY = None
        settings.MODELER_MODEL = None
        settings.MODELER_BASE_URL = None
        settings.CODER_API_KEY = None
        settings.CODER_MODEL = None
        settings.CODER_BASE_URL = None
        settings.WRITER_API_KEY = None
        settings.WRITER_MODEL = None
        settings.WRITER_BASE_URL = None
        return {"success": True, "message": "已清空前端保存的专属配置，回退到 .env.dev 全局配置"}
    except Exception as e:
        logger.error(f"重置配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
