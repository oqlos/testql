#!/usr/bin/env python3
"""Minimal mock server for api-testing examples."""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

scenarios = {}

@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/v3/data/devices")
def devices():
    return {"data": [{"id": "dev-001", "name": "Test Device"}]}

@app.get("/api/v3/scenarios")
def list_scenarios():
    return {"data": list(scenarios.values())}

@app.post("/api/v3/scenarios", status_code=201)
def create_scenario(body: dict):
    sid = f"sc-{len(scenarios)+1}"
    scenarios[sid] = {"id": sid, **body}
    return {"data": scenarios[sid]}

@app.get("/api/v3/scenarios/{sid}")
def get_scenario(sid: str):
    return {"data": scenarios.get(sid, {"id": sid})}

@app.put("/api/v3/scenarios/{sid}")
def update_scenario(sid: str, body: dict):
    if sid in scenarios:
        scenarios[sid].update(body)
    return {"data": scenarios.get(sid, {"id": sid})}

@app.delete("/api/v3/scenarios/{sid}", status_code=204)
def delete_scenario(sid: str):
    scenarios.pop(sid, None)
    return JSONResponse(status_code=204)

@app.get("/api/users")
def users():
    return {"data": [{"id": "u1", "name": "Alice"}]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8101)
