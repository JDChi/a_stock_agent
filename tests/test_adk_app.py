def test_adk_app_exposes_root_agent():
    from a_stock_agent.adk_app.agent import root_agent

    assert root_agent.name == "a_stock_research_agent"
