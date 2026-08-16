from typing import List, Dict, Any
from backend.domain.schemas import DiligenceState, ICAudioScript

def generate_ic_audio_script(state: DiligenceState) -> ICAudioScript:
    """
    Generates a structured Investment Committee (IC) debate podcast script
    featuring dialogue between Bull, Bear, and Skeptic partners.
    """
    company_name = state.company_name or "Target Company"
    industry = state.industry or "Technology"
    stage = state.target_round or "Series A"
    check_size = f"${state.check_size_usd:,.0f}" if state.check_size_usd else "$5,000,000"

    speakers = [
        {
            "name": "Partner Alex (Bull)",
            "role": "Bull Partner",
            "voice_id": "en-US-Standard-B"
        },
        {
            "name": "Partner Sarah (Bear)",
            "role": "Bear Partner",
            "voice_id": "en-US-Standard-C"
        },
        {
            "name": "Partner David (Skeptic)",
            "role": "Skeptic Partner / IC Chair",
            "voice_id": "en-US-Standard-D"
        }
    ]

    bull_points = state.bull_case or f"Exceptional product velocity in {industry} with strong top-line ARR expansion and high net retention."
    bear_points = state.bear_case or "Valuation multiple compression risk, elevated customer acquisition cost, and competitive moat sustainability."
    skeptic_points = state.skeptic_critique or "Downside protection concerns under liquidity waterfall and high CAC payback period under macro stress scenarios."

    transcript_lines = [
        {
            "speaker": "Partner David (Skeptic)",
            "role": "IC Chair",
            "timestamp_seconds": 0,
            "text": f"Welcome back, team. Today we're reviewing our potential {check_size} investment in {company_name} for their {stage} round in {industry}. Alex, you're sponsoring this deal. Pitch us the thesis."
        },
        {
            "speaker": "Partner Alex (Bull)",
            "role": "Bull Partner",
            "timestamp_seconds": 20,
            "text": f"Thanks, David. I'm strong conviction on {company_name}. {bull_points} Market size is massive, customer feedback is off the charts, and unit economics support hyper-growth trajectory."
        },
        {
            "speaker": "Partner Sarah (Bear)",
            "role": "Bear Partner",
            "timestamp_seconds": 55,
            "text": f"Hold on, Alex. Looking closely at the risk register, I have serious reservations. {bear_points} We're entering a sensitive valuation environment, and burn rate gives us less than 18 months runway."
        },
        {
            "speaker": "Partner David (Skeptic)",
            "role": "IC Chair",
            "timestamp_seconds": 95,
            "text": f"Sarah makes a valid point. Let's look at the financial stress testing. {skeptic_points} If churn spikes by 5% in a macro downturn, what happens to our liquidation preference and MOIC?"
        },
        {
            "speaker": "Partner Alex (Bull)",
            "role": "Bull Partner",
            "timestamp_seconds": 130,
            "text": "Our waterfall scenario models show that with Series A 1x non-participating preferred, our downside is well-covered up to a 50% haircut on exit valuation. Plus, gross margins of 75%+ give operating leverage as scale increases."
        },
        {
            "speaker": "Partner Sarah (Bear)",
            "role": "Bear Partner",
            "timestamp_seconds": 160,
            "text": "If we do proceed, I want strict milestone tranche releases, board observer seats, and mandatory monthly cohort retention reporting."
        },
        {
            "speaker": "Partner David (Skeptic)",
            "role": "IC Chair",
            "timestamp_seconds": 180,
            "text": f"Agreed. Let's issue a CONDITIONAL PASS for {company_name}, subject to satisfactory completion of the formal Data Room requests and final IC term sheet alignment."
        }
    ]

    return ICAudioScript(
        title=f"IC Debate Podcast: {company_name} ({stage})",
        duration_seconds=210,
        speakers=speakers,
        transcript_lines=transcript_lines
    )
