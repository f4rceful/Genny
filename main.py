import os
import uuid
import zipfile
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from schemas import GenerateRequest, GenerateResponse
from pipeline.runner import run_pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("output", exist_ok=True)
    yield


app = FastAPI(title="Generator", lifespan=lifespan)


def _pipeline_task(bt: str, bp: str, features: str, run_id: str) -> None:
    try:
        run_pipeline(bt=bt, bp=bp, features=features, run_id=run_id)
    except Exception as e:
        print(f"[main] Pipeline failed for run_id={run_id}: {e}")


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, background_tasks: BackgroundTasks):
    run_id = str(uuid.uuid4())
    background_tasks.add_task(
        _pipeline_task,
        bt=request.bt,
        bp=request.bp,
        features=request.features or "",
        run_id=run_id,
    )
    return GenerateResponse(run_id=run_id, status="started", artifacts=[])


@app.get("/status/{run_id}")
async def status(run_id: str):
    run_dir = os.path.join("output", run_id)
    if not os.path.isdir(run_dir):
        return {"run_id": run_id, "status": "not_found", "files": []}

    files = []
    for dirpath, _, filenames in os.walk(run_dir):
        for fname in filenames:
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, run_dir)
            files.append(rel)

    return {"run_id": run_id, "status": "done" if files else "running", "files": sorted(files)}


@app.get("/download/{run_id}")
async def download(run_id: str):
    run_dir = os.path.join("output", run_id)
    if not os.path.isdir(run_dir):
        raise HTTPException(status_code=404, detail="run_id not found")

    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    tmp.close()
    with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, _, filenames in os.walk(run_dir):
            for fname in filenames:
                full = os.path.join(dirpath, fname)
                arcname = os.path.relpath(full, run_dir)
                zf.write(full, arcname)

    return FileResponse(
        tmp.name,
        media_type="application/zip",
        filename=f"{run_id}.zip",
    )
