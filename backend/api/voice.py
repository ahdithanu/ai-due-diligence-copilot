import json
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status

from backend.domain.schemas import (
    VoiceLatencyBreakdown,
    VoiceSimulateTurnRequest,
    VoiceSimulateTurnResponse,
    VoiceTurnState
)
from backend.services.voice_stream_service import voice_stream_service

router = APIRouter(prefix="/voice", tags=["Real-Time Voice Streaming"])


@router.get("/latency-profile", response_model=VoiceLatencyBreakdown)
async def get_voice_latency_profile() -> VoiceLatencyBreakdown:
    """
    Returns the real-time engineering latency profile for conversational voice.
    Demonstrates the sub-700ms budget breakdown: VAD (90ms) -> STT (175ms) ->
    LLM TTFT (160ms) -> Streaming TTS (135ms) -> Network buffer (60ms).
    """
    return voice_stream_service.get_latency_profile()


@router.post("/simulate-turn", response_model=VoiceSimulateTurnResponse)
async def simulate_voice_turn(
    request: VoiceSimulateTurnRequest
) -> VoiceSimulateTurnResponse:
    """
    Executes a simulated real-time voice turn demonstrating low-latency speech pipelining
    and full-duplex user barge-in / interruption handling.
    """
    return voice_stream_service.simulate_turn(request)


@router.post("/barge-in/{session_id}")
async def trigger_barge_in(session_id: str) -> Dict[str, Any]:
    """
    Simulates a client-side barge-in interruption signal.
    Cancels downstream TTS generation and purges playback buffers.
    """
    return voice_stream_service.handle_barge_in(session_id)


@router.websocket("/stream")
async def voice_websocket_stream(websocket: WebSocket):
    """
    Bidirectional WebSocket connection for streaming speech frames and handling barge-ins.
    Client sends audio events (e.g. {"type": "SPEECH_START"}, {"type": "AUDIO_CHUNK"}, {"type": "BARGE_IN"}).
    Server responds with streamed sentences and timing telemetry.
    """
    await websocket.accept()
    session = voice_stream_service.get_or_create_session()
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "event": "SESSION_INITIALIZED",
            "session_id": session.session_id,
            "target_latency_budget_ms": 700.0,
            "state": VoiceTurnState.LISTENING.value
        })

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type", "UNKNOWN")

            if msg_type == "BARGE_IN":
                result = voice_stream_service.handle_barge_in(session.session_id)
                await websocket.send_json({
                    "event": "INTERRUPTION_ACKNOWLEDGED",
                    "session_id": session.session_id,
                    "state": VoiceTurnState.USER_SPEAKING.value,
                    "details": result
                })
            elif msg_type == "USER_INPUT":
                transcript = message.get("text", "")
                sim = voice_stream_service.simulate_turn(
                    VoiceSimulateTurnRequest(
                        user_transcript=transcript,
                        simulate_interruption=message.get("simulate_interruption", False)
                    )
                )
                await websocket.send_json({
                    "event": "TURN_COMPLETED",
                    "response": sim.model_dump()
                })
            elif msg_type == "PING":
                await websocket.send_json({"event": "PONG", "session_id": session.session_id})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"event": "ERROR", "detail": str(e)})
        except Exception:
            pass
