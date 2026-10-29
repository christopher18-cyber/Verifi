import os
import socket
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.graph.build import graph

load_dotenv()

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

def find_available_port(host: str, starting_port: int, max_attempts: int = 50) -> int:
    """Check if the given port is available; if not, return the next open port."""
    test_host = "127.0.0.1" if host in ("0.0.0.0", "") else host
    for p in range(starting_port, starting_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((test_host, p))
                return p
            except OSError:
                continue
    return starting_port


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    configured_port = int(os.getenv("PORT", 8000))
    port = find_available_port(host, configured_port)

    if port != configured_port:
        print(f"\n⚠️  Port {configured_port} is busy or restricted. Switched to available port: {port}\n")

    uvicorn.run("app.main:app", host=host, port=port, reload=True)