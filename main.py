import os
import uuid
import zipfile
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from schemas import GenerateRequest, GenerateResponse, PatchRequest, PatchResponse
from pipeline.runner import run_pipeline, refine_pipeline
from pipeline import agent_coder, agent_analyst
from utils import state, cancel as cancel_utils

os.makedirs("output", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Generator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/output", StaticFiles(directory="output", html=True), name="output")


def _pipeline_task(bt: str, bp: str, features: str, run_id: str) -> None:
    try:
        run_pipeline(bt=bt, bp=bp, features=features, run_id=run_id)
    except Exception as e:
        print(f"[main] pipeline task ended with error for run_id={run_id}: {e}")


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, background_tasks: BackgroundTasks):
    run_id = str(uuid.uuid4())
    state.write(run_id, "starting", step="queued")
    cancel_utils.register(run_id)
    background_tasks.add_task(
        _pipeline_task,
        bt=request.bt,
        bp=request.bp,
        features=request.features or "",
        run_id=run_id,
    )
    return GenerateResponse(run_id=run_id, status="started", artifacts=[])


@app.post("/cancel/{run_id}")
async def cancel_run(run_id: str):
    run_dir = os.path.join("output", run_id)
    if not os.path.isdir(run_dir):
        raise HTTPException(status_code=404, detail="run_id not found")

    info = state.read(run_id)
    if info.get("status") != "running":
        raise HTTPException(status_code=409, detail="Pipeline is not running")

    if cancel_utils.request(run_id):
        return {"cancelled": True, "run_id": run_id}
    raise HTTPException(status_code=404, detail="Cancel event not found")


@app.post("/refine/{run_id}", response_model=GenerateResponse)
async def refine(run_id: str, background_tasks: BackgroundTasks):
    run_dir = os.path.join("output", run_id)
    if not os.path.isdir(run_dir):
        raise HTTPException(status_code=404, detail="run_id not found")

    info = state.read(run_id)
    if info.get("status") == "running":
        raise HTTPException(status_code=409, detail="Pipeline already running for this run_id")

    def _refine_task():
        try:
            refine_pipeline(run_id)
        except Exception as e:
            print(f"[main] refine task ended with error for run_id={run_id}: {e}")

    state.write(run_id, "running", step="refine: queued")
    background_tasks.add_task(_refine_task)
    return GenerateResponse(run_id=run_id, status="refining", artifacts=[])


@app.post("/patch/{run_id}", response_model=PatchResponse)
async def patch(run_id: str, request: PatchRequest):
    run_dir = os.path.join("output", run_id)
    if not os.path.isdir(run_dir):
        raise HTTPException(status_code=404, detail="run_id not found")

    info = state.read(run_id)
    if info.get("status") == "running":
        raise HTTPException(status_code=409, detail="Pipeline already running for this run_id")

    if not request.instruction.strip():
        raise HTTPException(status_code=422, detail="instruction cannot be empty")

    state.write(run_id, "running", step="patch")
    try:
        patched_files = agent_coder.patch(instruction=request.instruction, run_id=run_id)
        state.write(run_id, "running", step="patch-docs")
        patched_docs = agent_analyst.patch(instruction=request.instruction, run_id=run_id)
        state.write(run_id, "done", step="")
    except Exception as e:
        state.write(run_id, "failed", step="patch", error=f"{type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return PatchResponse(run_id=run_id, status="done", patched_files=patched_files + patched_docs)


@app.get("/runs")
async def list_runs():
    runs = []
    if not os.path.isdir("output"):
        return {"runs": []}
    for name in sorted(os.listdir("output"), reverse=True):
        run_dir = os.path.join("output", name)
        if not os.path.isdir(run_dir):
            continue
        info = state.read(name)
        if info.get("status") == "running":
            continue
        created_at = os.path.getmtime(run_dir)
        steps = info.get("steps", [])
        file_count = sum(
            1 for dirpath, _, fnames in os.walk(run_dir)
            for f in fnames if not f.startswith(".")
        )
        runs.append({
            "run_id": name,
            "status": info.get("status", "unknown"),
            "created_at": created_at,
            "file_count": file_count,
            "step_count": len(steps),
        })
    return {"runs": runs}


@app.get("/status/{run_id}")
async def status(run_id: str):
    run_dir = os.path.join("output", run_id)
    if not os.path.isdir(run_dir):
        return {"run_id": run_id, "status": "not_found", "files": [], "step": "", "error": ""}

    info = state.read(run_id)

    files = []
    for dirpath, _, filenames in os.walk(run_dir):
        for fname in filenames:
            if fname.startswith("."):
                continue
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, run_dir)
            files.append(rel)

    return {
        "run_id": run_id,
        "status": info["status"],
        "step": info.get("step", ""),
        "error": info.get("error", ""),
        "steps": info.get("steps", []),
        "files": sorted(files),
    }


@app.get("/file/{run_id}/{path:path}")
async def get_file(run_id: str, path: str):
    run_dir = os.path.realpath(os.path.join("output", run_id))
    if not os.path.isdir(run_dir):
        raise HTTPException(status_code=404, detail="run_id not found")

    full_path = os.path.realpath(os.path.join(run_dir, path))
    if not full_path.startswith(run_dir + os.sep) and full_path != run_dir:
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        with open(full_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"content": content, "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
                if fname.startswith("."):
                    continue
                full = os.path.join(dirpath, fname)
                arcname = os.path.relpath(full, run_dir)
                zf.write(full, arcname)

    return FileResponse(
        tmp.name,
        media_type="application/zip",
        filename=f"{run_id}.zip",
    )
