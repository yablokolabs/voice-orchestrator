"""Prompt management router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from voice_orchestrator.api.schemas import (
    ActivatePromptRequest,
    CreatePromptRequest,
    PromptVersionResponse,
)

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("/", response_model=list[str])
async def list_prompts() -> list[str]:
    """List all prompt IDs."""
    return []


@router.get("/{prompt_id}/versions", response_model=list[PromptVersionResponse])
async def list_versions(prompt_id: str) -> list[PromptVersionResponse]:
    """List all versions for a prompt."""
    return []


@router.post("/", response_model=PromptVersionResponse)
async def create_prompt(request: CreatePromptRequest) -> PromptVersionResponse:
    """Create a new prompt version."""
    raise HTTPException(status_code=501, detail="Requires DB connection")


@router.post("/activate", response_model=PromptVersionResponse)
async def activate_prompt(request: ActivatePromptRequest) -> PromptVersionResponse:
    """Activate a specific prompt version."""
    raise HTTPException(status_code=501, detail="Requires DB connection")
