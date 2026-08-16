import asyncio
import io
import json
from httpx import AsyncClient, ASGITransport
from backend.main import app

DEMO_COMPANIES = [
    {
        "name": "Acme AI Systems",
        "industry": "Enterprise AI Automation",
        "target_round": "Series A",
        "check_size_usd": 5000000.0,
        "doc_filename": "acme_ai_pitch_deck.txt",
        "doc_content": (
            "Acme AI Systems Pitch Deck & Financial Materials\n"
            "Executive Summary: Acme AI delivers autonomous enterprise workflow orchestration.\n"
            "Market: TAM is $45B growing at 28% CAGR driven by global AI adoption.\n"
            "Financials: FY2024 ARR reached $10M with 80% Gross Margin and 125% Net Revenue Retention (NRR).\n"
            "Unit Economics: LTV/CAC ratio is 4.2x with 9 months CAC Payback period.\n"
            "Technology & Moat: 3 filed patents on workflow orchestration and fine-tuned model weights.\n"
            "Risks: Key person dependency on founding CTO. High customer concentration with top client representing 35% of ARR."
        )
    },
    {
        "name": "Nexus Quantum Inc",
        "industry": "Quantum Computing & Security",
        "target_round": "Seed",
        "check_size_usd": 2500000.0,
        "doc_filename": "nexus_quantum_deck.txt",
        "doc_content": (
            "Nexus Quantum Inc Executive Brief & Financial Model\n"
            "Company Overview: Next-generation fault-tolerant quantum encryption hardware.\n"
            "Market Opportunity: Post-quantum cryptography market expected to reach $15B by 2030.\n"
            "Financial Performance: Q4 2024 MRR reached $200K ($2.4M ARR) with 75% Gross Margin.\n"
            "Burn & Runway: Cash balance is $4M with a monthly burn rate of $250K (16 months runway).\n"
            "Competitive Landscape: Outperforming legacy HSM providers on key throughput metrics.\n"
            "Key Risks: Long enterprise sales cycles and hardware supply chain lead times."
        )
    },
    {
        "name": "Starlight Robotics",
        "industry": "Autonomous Logistics & Robotics",
        "target_round": "Series B",
        "check_size_usd": 12000000.0,
        "doc_filename": "starlight_robotics_materials.txt",
        "doc_content": (
            "Starlight Robotics Due Diligence Vault\n"
            "Product: Autonomous mobile robots (AMRs) for warehouse fulfillment.\n"
            "Market Size: Warehouse automation market is $35B expanding at 18% CAGR.\n"
            "Financial Highlights: FY2024 Revenue was $18M with 65% Gross Margin and Rule of 40 score of 48%.\n"
            "Unit Economics: CAC is $45K with ACV of $120K yielding 120% NRR across 85 active enterprise deployments.\n"
            "Moat: Proprietary SLAM navigation algorithms and hardware-software integration patents.\n"
            "Risk Factors: Supply chain component availability and regulatory safety standards."
        )
    }
]

async def seed_demo_data():
    print("🚀 Seeding AI Investment Due Diligence Copilot demo data...")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost:8000") as client:
        for company in DEMO_COMPANIES:
            print(f"\n🏢 Creating investment workspace: {company['name']} ({company['target_round']})...")
            
            # 1. Create Investment
            create_resp = await client.post(
                "/api/v1/investments",
                json={
                    "company_name": company["name"],
                    "industry": company["industry"],
                    "target_round": company["target_round"],
                    "check_size_usd": company["check_size_usd"]
                }
            )
            if create_resp.status_code != 201:
                print(f"❌ Failed to create investment for {company['name']}: {create_resp.text}")
                continue

            inv_data = create_resp.json()
            inv_id = inv_data["investment_id"]
            print(f"   ✓ Workspace ID: {inv_id}")

            # 2. Upload Document
            print(f"   📄 Uploading diligence material: {company['doc_filename']}...")
            doc_bytes = company["doc_content"].encode("utf-8")
            files = {"file": (company["doc_filename"], io.BytesIO(doc_bytes), "text/plain")}
            upload_data = {"doc_type": "PITCH_DECK"}
            
            upload_resp = await client.post(
                f"/api/v1/investments/{inv_id}/documents",
                files=files,
                data=upload_data
            )
            if upload_resp.status_code != 200:
                print(f"❌ Failed to upload document for {company['name']}: {upload_resp.text}")
                continue

            up_res = upload_resp.json()
            print(f"   ✓ Extracted {up_res['chunks_extracted']} chunks & {up_res['evidence_extracted']} evidence records.")

            # 3. Start 17-Node Diligence Graph Execution
            print(f"   ⚙️ Executing 17-node diligence graph state machine...")
            start_resp = await client.post(f"/api/v1/investments/{inv_id}/diligence/start")
            if start_resp.status_code != 200:
                print(f"❌ Failed graph execution for {company['name']}: {start_resp.text}")
                continue

            final_state = start_resp.json()
            rec = final_state.get("recommendation", "N/A")
            conf = final_state.get("confidence_score", 0.0)
            print(f"   ✓ Execution completed! Recommendation: {rec} (Confidence: {conf})")
            
            # 4. Fetch Memo Status
            memo_resp = await client.get(f"/api/v1/investments/{inv_id}/memo")
            if memo_resp.status_code == 200:
                print(f"   ✓ Institutional Investment Memo generated & persisted.")

    print("\n🎉 Demo data seeding complete! Start backend and frontend to explore populated workspaces.")

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
