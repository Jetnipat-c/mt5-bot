from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from app.routers import trading
from app.bot_engine import start_bot, stop_bot, get_bot_status

@asynccontextmanager
async def lifespan(app: FastAPI):
    # App Startup
    yield
    # App Shutdown
    stop_bot()

app = FastAPI(title="MT5 Trading API", lifespan=lifespan)
app.include_router(trading.router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/bot/start")
def api_start_bot():
    return start_bot()

@app.post("/bot/stop")
def api_stop_bot():
    return stop_bot()

@app.get("/bot/status")
def api_bot_status():
    return get_bot_status()
