from fastapi import FastAPI, status
from pydantic import BaseModel

app = FastAPI(
    title="Inventory & Allocation Engine",
    version="0.1.0",
    description="High-concurrency reservation engine with transactional row locking"
)

class HealthCheck(BaseModel):
    status: str
    version: str

@app.get("/health", response_model=HealthCheck, status_code=status.HTTP_200_OK)
async def health_check():
    return HealthCheck(status="healthy", version="0.1.0")