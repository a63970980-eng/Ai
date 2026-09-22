from api import app


def test_vercel_entrypoint_exposes_fastapi_app():
    assert app.title == "AI Forex Trading Platform"
    assert callable(getattr(app, "openapi"))
