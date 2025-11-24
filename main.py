import asyncio
from typing import List, Optional

import requests
from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from config import settings
from utils import execute_tobeta

app = FastAPI(
    title="Infinitools API",
    description="API para ejecutar comandos de la herramienta Infinitools",
    version="1.0.0",
)


def send_discord_notification(
    environment: str, success_cpn: Optional[List[str]], failed_cpn: Optional[List[str]]
):
    """Send simple notification to Discord webhook"""
    message_parts = []

    if success_cpn:
        success_str = ", ".join(map(str, success_cpn))
        message_parts.append(f"CPNs pasados a {environment.upper()}: {success_str}")

    if failed_cpn:
        failed_str = ", ".join(map(str, failed_cpn))
        message_parts.append(f"CPNs fallidos: {failed_str}")

    if not message_parts:
        return

    message = "\n".join(message_parts)

    try:
        requests.post(
            "https://discord.com/api/webhooks/1412928175624814612/3s2gX0--GGk-XswQ-7bI1aCrowB7hTrHBpde_J2GCI7v4YZLq7kF88LP7Qh6-c8AUY-R",
            json={
                "username": "InfiniBOT",
                "avatar_url": "https://static.wikia.nocookie.net/the-scrappy/images/b/bc/Screenshot_Snarf.jpg",
                "content": message,
            },
            timeout=5,
        )
    except Exception:
        pass


class ToBetaRequest(BaseModel):
    """Request model for tobeta endpoints"""

    ids: str = Field(
        ...,
        description="Comma-separated list of company IDs (CPNs)",
        examples=["123,456,789"],
    )
    git_user: Optional[str] = Field(
        None, description="GitHub username (defaults to 'github-actions')"
    )
    motive: Optional[str] = Field(
        None,
        description="Reason for the change (defaults to 'Automated deployment')",
        max_length=100,
    )

    @field_validator("ids")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        """Validate that ids string contains valid integers"""
        ids = [id.strip() for id in v.split(",") if id.strip()]

        if not ids:
            raise ValueError("At least one ID must be provided")

        for id_str in ids:
            try:
                cpn = int(id_str)
                if cpn < 1 or cpn > 999999:
                    raise ValueError(f"ID {cpn} is out of range (1-999999)")
            except ValueError as e:
                if "out of range" in str(e):
                    raise e
                raise ValueError(
                    f"Invalid ID format: '{id_str}' is not a valid integer"
                )

        return v


class ToBetaResponse(BaseModel):
    """Response model for tobeta endpoints"""

    message: str
    total: int
    successful: int
    failed: int
    results: List[dict]


async def verify_api_key(
    x_api_key: str = Header(..., description="API Key for authentication"),
):
    """Verify API Key from header"""
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
        )


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "Infinitools API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "environment": settings.environment}


@app.post("/to_beta", response_model=ToBetaResponse, dependencies=[])
async def to_beta(
    request: ToBetaRequest,
    x_api_key: str = Header(..., description="API Key for authentication"),
):
    """
    Move companies to beta environment

    - **ids**: Comma-separated list of company IDs (CPNs)
    - **git_user**: GitHub username (optional, defaults to 'github-actions')
    - **motive**: Reason for the change (optional, defaults to 'Automated deployment')
    """
    await verify_api_key(x_api_key)

    # Parse IDs
    cpn_list = [int(id.strip()) for id in request.ids.split(",") if id.strip()]

    # Set defaults
    git_user = request.git_user or settings.default_git_user
    motive = request.motive or settings.default_motive

    # Execute command for each CPN
    tasks = [
        execute_tobeta(cpn=cpn, dest="beta", git_user=git_user, motive=motive)
        for cpn in cpn_list
    ]

    results = await asyncio.gather(*tasks)

    success_cpn = [r["cpn"] for r in results if r["success"]]
    failed_cpn = [r["cpn"] for r in results if not r["success"]]

    # Count successes and failures
    successful = len(success_cpn)
    failed = len(results) - successful

    # Send Discord notification
    send_discord_notification("beta", success_cpn, failed_cpn)

    return ToBetaResponse(
        message=f"Processed {len(cpn_list)} company(ies) to beta environment",
        total=len(cpn_list),
        successful=successful,
        failed=failed,
        results=results,
    )


@app.post("/to_master", response_model=ToBetaResponse, dependencies=[])
async def to_master(
    request: ToBetaRequest,
    x_api_key: str = Header(..., description="API Key for authentication"),
):
    """
    Move companies to master environment

    - **ids**: Comma-separated list of company IDs (CPNs)
    - **git_user**: GitHub username (optional, defaults to 'github-actions')
    - **motive**: Reason for the change (optional, defaults to 'Automated deployment')
    """
    await verify_api_key(x_api_key)

    # Parse IDs
    cpn_list = [int(id.strip()) for id in request.ids.split(",") if id.strip()]

    # Set defaults
    git_user = request.git_user or settings.default_git_user
    motive = request.motive or settings.default_motive

    # Execute command for each CPN
    tasks = [
        execute_tobeta(cpn=cpn, dest="master", git_user=git_user, motive=motive)
        for cpn in cpn_list
    ]

    results = await asyncio.gather(*tasks)

    success_cpn = [r["cpn"] for r in results if r["success"]]
    failed_cpn = [r["cpn"] for r in results if not r["success"]]

    # Count successes and failures
    successful = len(success_cpn)
    failed = len(results) - successful

    # Send Discord notification
    send_discord_notification("master", success_cpn, failed_cpn)

    return ToBetaResponse(
        message=f"Processed {len(cpn_list)} company(ies) to master environment",
        total=len(cpn_list),
        successful=successful,
        failed=failed,
        results=results,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
