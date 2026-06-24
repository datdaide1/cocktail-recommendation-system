from fastapi import FastAPI
<<<<<<< HEAD
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import chat, tools

app = FastAPI(title="Cocktail Recommendation System API", version="1.0.0")
=======
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.chat import router as chat_router

app = FastAPI(title="Cocktail Recommendation System")
>>>>>>> test

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["Tools"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
=======
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])

# Serve frontend
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
>>>>>>> test
