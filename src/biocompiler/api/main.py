"""Run with uv run uvicorn biocompiler.api.main:app --reload."""

import asyncio
import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from biocompiler.bio.safety import SafetyRefusal
from biocompiler.config import get_settings
from biocompiler.contracts.results import CompileResult
from biocompiler.pipeline import PipelineError, run_pipeline
from biocompiler.providers.factory import get_provider
from biocompiler.sandbox.runner import get_simulator


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    )
    app.state.settings = settings
    app.state.provider = get_provider(settings)
    app.state.simulator = get_simulator(settings)
    app.state.capacity = asyncio.Semaphore(2)
    yield
    client = getattr(app.state.provider, "client", None)
    if client:
        await client.close()


app = FastAPI(
    title="BioCompiler Engine",
    version="0.1.0",
    lifespan=lifespan,
    description="Simulation-only PET assay planning. Never controls laboratory hardware.",
)


class CompileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    goal: str = Field(min_length=5, max_length=2000)
    demo_failure: bool = Field(default=False, description="Mock-only injected error for the demo.")


@app.get("/health")
async def health(request: Request):
    settings = request.app.state.settings
    return {
        "status": "ok",
        "provider": settings.biocompiler_provider,
        "simulator": settings.biocompiler_simulator,
        "simulation_only": True,
    }


@app.post("/compile", response_model=CompileResult)
async def compile_goal(payload: CompileRequest, request: Request):
    state = request.app.state
    if payload.demo_failure and state.settings.biocompiler_provider != "mock":
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "invalid_demo_option",
                    "message": "Error injection is available only in mock mode.",
                }
            },
        )
    async with state.capacity:
        result = await run_pipeline(
            payload.goal,
            state.provider,
            state.simulator,
            state.settings,
            demo_failure=payload.demo_failure,
        )
    return JSONResponse(
        status_code=200 if result.status == "success" else 422,
        content=result.model_dump(mode="json"),
    )


@app.exception_handler(SafetyRefusal)
async def safety_error(request: Request, exc: SafetyRefusal):
    return JSONResponse(
        status_code=403,
        content={
            "status": "refused",
            "simulation_only": True,
            "error": {"code": "safety_refusal", "stage": "safety", "message": exc.reason},
        },
    )


@app.exception_handler(PipelineError)
async def pipeline_error(request: Request, exc: PipelineError):
    # Schema diagnostics are safe; remote exception strings may contain credentials.
    message = (
        str(exc.cause)
        if isinstance(exc.cause, ValidationError)
        else f"The {exc.stage} stage failed. Check the server log and configuration."
    )
    return JSONResponse(
        status_code=502,
        content={
            "error": {
                "code": "stage_failed",
                "stage": exc.stage,
                "message": message,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def request_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "invalid_request",
                "stage": "request",
                "message": str(exc),
            }
        },
    )


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    structlog.get_logger().error("unexpected_error", kind=type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected error stopped the run.",
            }
        },
    )
