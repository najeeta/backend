from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from llm_runner import generate_stream, ChatRequest
from thesys_genui_sdk.fast_api import with_c1_response
from config.supabase_config import supabase
from routers import instructors, lms_connections


app = FastAPI(
    title="Anita Backend API",
    description="AI Teaching Assistant Backend with Canvas Integration",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(instructors.router, prefix="/instructors", tags=["instructors"])
app.include_router(lms_connections.router, prefix="/lms-connections", tags=["lms-connections"])


@app.get("/")
def read_root():
    return {
        "status": "ok",
        "service": "anita-backend",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Health check endpoint that verifies database connectivity."""
    try:
        # Test database connection by querying a simple table
        response = supabase.table("instructors").select("id").limit(1).execute()

        return {
            "status": "healthy",
            "database": "connected",
            "service": "anita-backend"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "service": "anita-backend"
        }


@app.post("/chat")
@with_c1_response()
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint for streaming AI responses.
    """
    await generate_stream(request)
