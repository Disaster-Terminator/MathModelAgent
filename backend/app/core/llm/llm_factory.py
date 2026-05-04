from app.config.setting import settings
from app.core.llm.llm import LLM


def _resolve_agent_config(agent_value: str | None, global_value: str | None) -> str:
    """优先使用 agent 专属配置，为空时回退到全局配置，再为空则返回空字符串。"""
    return (agent_value if agent_value else global_value) or ""


class LLMFactory:
    task_id: str

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id

    def get_all_llms(self) -> tuple[LLM, LLM, LLM, LLM]:
        coordinator_llm = LLM(
            api_key=_resolve_agent_config(settings.COORDINATOR_API_KEY, settings.LITELLM_API_KEY),
            model=_resolve_agent_config(settings.COORDINATOR_MODEL, settings.MODEL),
            base_url=_resolve_agent_config(settings.COORDINATOR_BASE_URL, settings.LITELLM_API_URL),
            task_id=self.task_id,
            max_tokens=settings.COORDINATOR_MAX_TOKENS,
        )

        modeler_llm = LLM(
            api_key=_resolve_agent_config(settings.MODELER_API_KEY, settings.LITELLM_API_KEY),
            model=_resolve_agent_config(settings.MODELER_MODEL, settings.MODEL),
            base_url=_resolve_agent_config(settings.MODELER_BASE_URL, settings.LITELLM_API_URL),
            task_id=self.task_id,
            max_tokens=settings.MODELER_MAX_TOKENS,
        )

        coder_llm = LLM(
            api_key=_resolve_agent_config(settings.CODER_API_KEY, settings.LITELLM_API_KEY),
            model=_resolve_agent_config(settings.CODER_MODEL, settings.MODEL),
            base_url=_resolve_agent_config(settings.CODER_BASE_URL, settings.LITELLM_API_URL),
            task_id=self.task_id,
            max_tokens=settings.CODER_MAX_TOKENS,
        )

        writer_llm = LLM(
            api_key=_resolve_agent_config(settings.WRITER_API_KEY, settings.LITELLM_API_KEY),
            model=_resolve_agent_config(settings.WRITER_MODEL, settings.MODEL),
            base_url=_resolve_agent_config(settings.WRITER_BASE_URL, settings.LITELLM_API_URL),
            task_id=self.task_id,
            max_tokens=settings.WRITER_MAX_TOKENS,
        )

        return coordinator_llm, modeler_llm, coder_llm, writer_llm
