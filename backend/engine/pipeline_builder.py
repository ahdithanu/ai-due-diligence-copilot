from typing import Optional
from backend.engine.graph import GraphEngine, END
from backend.engine.model_adapter import ModelAdapter
from backend.nodes import (
    DeterministicFinancialEngineNode,
    FinancialAnalystNode,
    FinancialCriticNode,
    MarketAnalystNode,
    CompetitiveAnalystNode,
    CustomerAnalystNode,
    ProductAnalystNode,
    RiskAnalystNode,
    UnitEconomicsAnalystNode,
    CrossExaminerNode,
    GapDetectorNode,
    BullNode,
    BearNode,
    SkepticNode,
    ICSynthesizerNode,
    MemoGeneratorNode,
    HumanReviewGateNode,
    skeptic_routing_condition
)

def build_full_diligence_graph(model_adapter: Optional[ModelAdapter] = None) -> GraphEngine:
    """
    Builds and wires up the full 17-node AI Investment Due Diligence Graph:
    Deterministic Financial Engine -> Specialist Analysts (Financial, Market, Competitive, Customer, Product, Risk, UnitEconomics) ->
    Critic -> Cross Examiner -> Gap Detector -> Investment Committee (Bull, Bear, Skeptic) -> IC Synthesizer -> Memo Generator.
    """
    graph = GraphEngine(name="full_diligence_graph")

    # 1. Instantiate Nodes
    fin_engine = DeterministicFinancialEngineNode()
    fin_analyst = FinancialAnalystNode(model_adapter=model_adapter)
    market_analyst = MarketAnalystNode(model_adapter=model_adapter)
    comp_analyst = CompetitiveAnalystNode(model_adapter=model_adapter)
    cust_analyst = CustomerAnalystNode(model_adapter=model_adapter)
    prod_analyst = ProductAnalystNode(model_adapter=model_adapter)
    risk_analyst = RiskAnalystNode(model_adapter=model_adapter)
    unit_econ_analyst = UnitEconomicsAnalystNode(model_adapter=model_adapter)
    
    fin_critic = FinancialCriticNode(model_adapter=model_adapter)
    cross_examiner = CrossExaminerNode(model_adapter=model_adapter)
    gap_detector = GapDetectorNode(model_adapter=model_adapter)

    bull_node = BullNode(model_adapter=model_adapter)
    bear_node = BearNode(model_adapter=model_adapter)
    skeptic_node = SkepticNode(model_adapter=model_adapter)
    ic_synthesizer = ICSynthesizerNode(model_adapter=model_adapter)
    memo_generator = MemoGeneratorNode()

    # 2. Add Nodes to Graph
    graph.add_node("DeterministicFinancialEngine", fin_engine)
    graph.add_node("FinancialAnalyst", fin_analyst)
    graph.add_node("MarketAnalyst", market_analyst)
    graph.add_node("CompetitiveAnalyst", comp_analyst)
    graph.add_node("CustomerAnalyst", cust_analyst)
    graph.add_node("ProductAnalyst", prod_analyst)
    graph.add_node("RiskAnalyst", risk_analyst)
    graph.add_node("UnitEconomicsAnalyst", unit_econ_analyst)
    graph.add_node("FinancialCritic", fin_critic)
    graph.add_node("CrossExaminer", cross_examiner)
    graph.add_node("GapDetector", gap_detector)
    graph.add_node("Bull", bull_node)
    graph.add_node("Bear", bear_node)
    graph.add_node("Skeptic", skeptic_node)
    graph.add_node("ICSynthesizer", ic_synthesizer)
    graph.add_node("MemoGenerator", memo_generator)

    # 3. Wire Up Sequential & Conditional Edges
    graph.set_entry_point("DeterministicFinancialEngine")
    graph.add_edge("DeterministicFinancialEngine", "FinancialAnalyst")
    graph.add_edge("FinancialAnalyst", "MarketAnalyst")
    graph.add_edge("MarketAnalyst", "CompetitiveAnalyst")
    graph.add_edge("CompetitiveAnalyst", "CustomerAnalyst")
    graph.add_edge("CustomerAnalyst", "ProductAnalyst")
    graph.add_edge("ProductAnalyst", "RiskAnalyst")
    graph.add_edge("RiskAnalyst", "UnitEconomicsAnalyst")
    graph.add_edge("UnitEconomicsAnalyst", "FinancialCritic")
    graph.add_edge("FinancialCritic", "CrossExaminer")
    graph.add_edge("CrossExaminer", "GapDetector")
    graph.add_edge("GapDetector", "Bull")
    graph.add_edge("Bull", "Bear")
    graph.add_edge("Bear", "Skeptic")

    # Skeptic Conditional Routing: routes to GapDetector if critical flaws exist, else to ICSynthesizer
    graph.add_conditional_edges(
        "Skeptic",
        skeptic_routing_condition,
        path_map={
            "GapDetector": "GapDetector",
            "ICSynthesizer": "ICSynthesizer"
        }
    )

    graph.add_edge("ICSynthesizer", "MemoGenerator")
    graph.add_edge("MemoGenerator", END)

    return graph
