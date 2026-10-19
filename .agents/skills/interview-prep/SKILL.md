---
name: interview-prep
description: Guidance for executive-level AI engineering and Forward-Deployed Engineer (FDE) interviews, focusing on strategic discovery, business outcomes, and technical follow-ups.
---

# Interview Prep Skill

Use this skill when preparing for high-stakes technical interviews, customer discovery discussions, or architecture defense sessions.

## Core Mindset

Shift the discussion from **"how the code works"** to **"what business risk this mitigates"**.

* Junior Engineer: Talks about chunking algorithms, LangChain abstractions, and prompt phrasing.
* Staff / FDE / Lead: Diagnoses unvetted data rooms, asymmetric financial risk (false positives vs false negatives), broken-deal expense optimization, and deterministic evaluation gates.

## 4 Discovery Pillars to Drive

1. **Data Room Asymmetry**:
   * *Probe*: "How do your clients reconcile pitch deck claims ($12M ARR) against audited financial statements ($8M ARR)?"
   * *Outcome*: Demonstrates contradiction detection and human-in-the-loop review nodes.
2. **Asymmetric Risk**:
   * *Probe*: "Which error is worse for the investment committee: missing a good deal (false negative) or writing a $20M check into fraud/dilution traps (false positive)?"
   * *Outcome*: Justifies confidence scoring and acceptance gates.
3. **Information Barriers & Multi-Entity Governance**:
   * *Probe*: "How do you enforce Chinese walls across funds, SPVs, and co-investors?"
   * *Outcome*: Highlights Row-Level Security (RLS), RBAC, and KMS encryption.
4. **Unit Economics & TCO**:
   * *Probe*: "What is the token burn for ingesting 5,000-page data rooms?"
   * *Outcome*: Explains task-based model routing (Gemini Flash for OCR/extraction vs GPT-4o for debate synthesis).

## Detailed Playbook Reference

For full scripts and interview scenarios, consult the project playbook:
`interview_executive_playbook.md`
