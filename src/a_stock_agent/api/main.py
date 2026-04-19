from .app import create_app

app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run("a_stock_agent.api.main:app", host="0.0.0.0", port=8000, reload=False)
