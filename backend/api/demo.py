from typing import Optional
from fastapi import APIRouter
from backend.domain.schemas import DemoControlRequest, DemoStatusResponse
from backend.services.automated_demo_service import automated_demo_service

router = APIRouter(prefix="/demo", tags=["Demo"])


@router.post("/start", response_model=DemoStatusResponse)
async def start_demo(control: Optional[DemoControlRequest] = None):
    """
    Starts automated demo player with optional speed and loop settings.
    """
    speed = control.speed if control else 1.0
    loop = control.loop if control else True
    return automated_demo_service.start(speed=speed, loop=loop)


@router.post("/pause", response_model=DemoStatusResponse)
async def pause_demo():
    """
    Pauses demo playback.
    """
    return automated_demo_service.pause()


@router.post("/resume", response_model=DemoStatusResponse)
async def resume_demo():
    """
    Resumes demo playback.
    """
    return automated_demo_service.resume()


@router.post("/step", response_model=DemoStatusResponse)
async def step_demo():
    """
    Manually steps to the next demo milestone.
    """
    return automated_demo_service.step()


@router.post("/reset", response_model=DemoStatusResponse)
async def reset_demo():
    """
    Resets demo state back to initial state.
    """
    return automated_demo_service.reset()


@router.get("/status", response_model=DemoStatusResponse)
async def get_demo_status():
    """
    Returns current demo playback status and log messages.
    """
    return automated_demo_service.get_status()
