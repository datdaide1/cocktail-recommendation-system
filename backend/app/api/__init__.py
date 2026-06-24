from fastapi import APIRouter

router = APIRouter()

# Example router, will be populated with actual endpoints
@router.get("/")
async def root():
    return {"message": "API is running"}
