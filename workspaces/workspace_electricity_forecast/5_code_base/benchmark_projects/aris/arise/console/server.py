import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .registry import AgentRegistry
from .routes import agents, skills, trajectories, evolutions, settings
from . import ws


def create_console_app(data_dir: str = "~/.arise/console", static_dir: str | None = None) -> FastAPI:
    app = FastAPI(title="ARISE Console", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    registry = AgentRegistry(data_dir=data_dir)

    agents.init(registry)
    skills.init(registry)
    trajectories.init(registry)
    evolutions.init(registry)
    settings.init(data_dir)
    ws.init(registry)

    app.include_router(agents.router)
    app.include_router(skills.router)
    app.include_router(trajectories.router)
    app.include_router(evolutions.router)
    app.include_router(settings.router)
    app.include_router(ws.router)

    # Serve frontend static files if available
    if static_dir and os.path.isdir(static_dir):
        index_html = os.path.join(static_dir, "index.html")

        # Serve static assets (js, css, fonts)
        assets_dir = os.path.join(static_dir, "assets")
        if os.path.isdir(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        # SPA fallback: serve index.html for all non-API routes
        @app.get("/{path:path}")
        async def spa_fallback(path: str):
            # Check if it's a static file
            file_path = os.path.join(static_dir, path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)
            return FileResponse(index_html)

    return app


def run_console(data_dir: str = "~/.arise/console", port: int = 8080, host: str = "0.0.0.0"):
    """Run the ARISE Console server."""
    import uvicorn
    import webbrowser

    # Look for built frontend
    static_dir = None
    # Check relative to this file (for pip-installed package)
    pkg_static = os.path.join(os.path.dirname(__file__), "static")
    # Check in the console/ directory (for development)
    dev_static = os.path.join(os.path.dirname(__file__), "..", "..", "console", "dist")
    dev_static = os.path.normpath(dev_static)

    if os.path.isdir(pkg_static):
        static_dir = pkg_static
    elif os.path.isdir(dev_static):
        static_dir = dev_static

    app = create_console_app(data_dir=data_dir, static_dir=static_dir)

    url = f"http://localhost:{port}"
    print(f"""
  ╭──────────────────────────────────╮
  │                                  │
  │   ARISE Console                  │
  │   {url:<32s} │
  │                                  │
  ╰──────────────────────────────────╯
""")

    if static_dir:
        print(f"  Serving frontend from {static_dir}")
    else:
        print("  No frontend build found. Run 'npm run build' in console/")
        print(f"  API only at {url}/api/agents")

    # Open browser
    webbrowser.open(url)

    uvicorn.run(app, host=host, port=port)
