from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import chat, tools

app = FastAPI(title="Cocktail Recommendation System API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["Tools"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
