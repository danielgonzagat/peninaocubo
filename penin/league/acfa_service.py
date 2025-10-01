from fastapi import FastAPI

app = FastAPI(title="ACFA League", version="0.1.0")


@app.get("/league/canary/ping")
async def ping():
    return {"ok": True, "xG": 0.01, "EPV": 0.02}
