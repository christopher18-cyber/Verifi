import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.graph.build import graph

app = FastAPI(
    title="Scam & Fraud Message Defense Assistant API",
    description="Backend API powered by hybrid deterministic rules and LLM evaluation."
)

# Pydantic schema for input requests
class MessageRequest(BaseModel):
    message: str
    language: str = "en"

# API Endpoint for checking messages
@app.post("/api/check")
async def check_message(payload: MessageRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    try:
        # Run through LangGraph pipeline
        result = await graph.ainvoke({
            "message": payload.message,
            "language": payload.language
        })
        return result["final"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Ensure static folder exists
os.makedirs("static", exist_ok=True)

# Mount static assets (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve main frontend entrypoint
@app.get("/")
async def read_index():
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "API is running. Place your index.html inside the 'static' folder."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)