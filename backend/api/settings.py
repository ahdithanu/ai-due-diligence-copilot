import os
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.config import settings
from backend.engine.model_adapter import get_model_adapter

router = APIRouter(prefix="/settings", tags=["Settings"])


class LLMSettingsResponse(BaseModel):
    current_provider: str
    available_providers: List[str]
    has_gemini_key: bool
    has_openai_key: bool
    active_model_name: str
    is_live_ready: bool


class UpdateLLMSettingsRequest(BaseModel):
    provider: str
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None


@router.get("/llm", response_model=LLMSettingsResponse)
async def get_llm_settings():
    has_gemini = bool(settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "").strip())
    has_openai = bool(settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "").strip())
    
    current_p = (settings.LLM_PROVIDER or "mock").lower()
    adapter = get_model_adapter(provider=current_p)

    is_live_ready = (current_p == "gemini" and has_gemini) or \
                    (current_p == "openai" and has_openai) or \
                    (current_p in ("routed", "router") and (has_gemini or has_openai))

    return LLMSettingsResponse(
        current_provider=current_p,
        available_providers=["routed", "gemini", "openai", "mock"],
        has_gemini_key=has_gemini,
        has_openai_key=has_openai,
        active_model_name=adapter.model_name,
        is_live_ready=is_live_ready
    )


@router.post("/llm", response_model=LLMSettingsResponse)
async def update_llm_settings(req: UpdateLLMSettingsRequest):
    allowed = ["routed", "gemini", "openai", "mock"]
    p_norm = req.provider.lower().strip()
    if p_norm not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider '{req.provider}'. Allowed: {allowed}"
        )

    settings.LLM_PROVIDER = p_norm
    os.environ["LLM_PROVIDER"] = p_norm

    if req.gemini_api_key:
        clean_key = req.gemini_api_key.strip()
        settings.GEMINI_API_KEY = clean_key
        os.environ["GEMINI_API_KEY"] = clean_key

    if req.openai_api_key:
        clean_key = req.openai_api_key.strip()
        settings.OPENAI_API_KEY = clean_key
        os.environ["OPENAI_API_KEY"] = clean_key

    return await get_llm_settings()
