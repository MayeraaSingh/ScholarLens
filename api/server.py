"""
FastAPI Backend for ScholarLens Web Interface

Provides REST API endpoints for:
- PDF upload and analysis
- Session management
- Report retrieval
- Real-time progress tracking
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import asyncio
from datetime import datetime
import json

from src.orchestrator import OrchestratorAgent
from src.memory import get_session_manager
from src.utils import get_logger, Config

# Initialize
app = FastAPI(title="ScholarLens API", version="1.0.0")
logger = get_logger("api")
session_manager = get_session_manager()
orchestrator = OrchestratorAgent()

# CORS - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for analysis progress
analysis_progress = {}


class AnalysisRequest(BaseModel):
    """Request model for analysis."""
    session_id: Optional[str] = None


class AnalysisStatus(BaseModel):
    """Status of an analysis job."""
    session_id: str
    status: str  # "queued", "processing", "completed", "failed"
    progress: int  # 0-100
    current_stage: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "ScholarLens API",
        "version": "1.0.0",
        "status": "online",
        "agents": 7
    }


@app.post("/api/analyze", response_model=AnalysisStatus)
async def upload_and_analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session_id: Optional[str] = None
):
    """
    Upload a PDF and start analysis.
    Returns immediately with session_id for tracking progress.
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Generate or use provided session ID
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Save uploaded file
    upload_dir = Config.DATA_ROOT / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / f"{session_id}_{file.filename}"
    
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"File uploaded: {file_path}")
        
        # Initialize progress tracking
        analysis_progress[session_id] = {
            "status": "queued",
            "progress": 0,
            "current_stage": "Initializing",
            "started_at": datetime.now().isoformat(),
            "filename": file.filename
        }
        
        # Start analysis in background
        background_tasks.add_task(run_analysis, session_id, str(file_path))
        
        return AnalysisStatus(
            session_id=session_id,
            status="queued",
            progress=0,
            current_stage="Queued for processing",
            started_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_analysis(session_id: str, pdf_path: str):
    """Background task to run paper analysis."""
    try:
        # Update progress
        analysis_progress[session_id]["status"] = "processing"
        analysis_progress[session_id]["progress"] = 10
        analysis_progress[session_id]["current_stage"] = "Document Extraction"
        
        logger.info(f"Starting analysis for session: {session_id}")
        
        # Run orchestrator (this calls all agents)
        result = await asyncio.to_thread(
            orchestrator.analyze_paper,
            pdf_path,
            session_id
        )
        
        # Update progress
        analysis_progress[session_id]["status"] = "completed"
        analysis_progress[session_id]["progress"] = 100
        analysis_progress[session_id]["current_stage"] = "Complete"
        analysis_progress[session_id]["completed_at"] = datetime.now().isoformat()
        analysis_progress[session_id]["result"] = result
        
        logger.info(f"Analysis completed for session: {session_id}")
        
    except Exception as e:
        logger.error(f"Analysis failed for {session_id}: {e}")
        analysis_progress[session_id]["status"] = "failed"
        analysis_progress[session_id]["error"] = str(e)
        analysis_progress[session_id]["completed_at"] = datetime.now().isoformat()


@app.get("/api/status/{session_id}", response_model=AnalysisStatus)
async def get_analysis_status(session_id: str):
    """Get the status of an analysis job."""
    if session_id not in analysis_progress:
        raise HTTPException(status_code=404, detail="Session not found")
    
    progress_data = analysis_progress[session_id]
    
    return AnalysisStatus(
        session_id=session_id,
        status=progress_data["status"],
        progress=progress_data["progress"],
        current_stage=progress_data.get("current_stage"),
        error=progress_data.get("error"),
        started_at=progress_data.get("started_at"),
        completed_at=progress_data.get("completed_at")
    )


@app.get("/api/report/{session_id}")
async def get_report(session_id: str):
    """Get the complete analysis report for a session."""
    try:
        # Get from session manager
        context = session_manager.get_full_context(session_id)
        
        if not context:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return JSONResponse(content=context)
        
    except Exception as e:
        logger.error(f"Failed to retrieve report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions")
async def list_sessions():
    """List all active analysis sessions."""
    try:
        sessions = session_manager.list_sessions()
        
        # Enhance with progress info
        enhanced_sessions = []
        for session in sessions:
            session_info = {
                **session,
                "progress_status": analysis_progress.get(session["session_id"], {})
            }
            enhanced_sessions.append(session_info)
        
        return {"sessions": enhanced_sessions}
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its data."""
    try:
        session_manager.clear_session(session_id)
        
        # Remove from progress tracking
        if session_id in analysis_progress:
            del analysis_progress[session_id]
        
        return {"message": "Session deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/clear")
async def clear_all_sessions():
    """Clear all sessions."""
    try:
        session_manager.clear_all()
        analysis_progress.clear()
        
        return {"message": "All sessions cleared"}
        
    except Exception as e:
        logger.error(f"Failed to clear sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{session_id}/{format}")
async def download_report(session_id: str, format: str):
    """Download report in specified format (json or markdown)."""
    try:
        # Find the output file
        output_dir = Config.OUTPUTS_DIR
        
        if format == "json":
            pattern = f"*{session_id[:8]}*_report.json"
        elif format == "markdown" or format == "md":
            pattern = f"*{session_id[:8]}*_report.md"
        else:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'markdown'")
        
        files = list(output_dir.glob(pattern))
        
        if not files:
            raise HTTPException(status_code=404, detail="Report file not found")
        
        file_path = files[0]
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/octet-stream"
        )
        
    except Exception as e:
        logger.error(f"Failed to download report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting ScholarLens API Server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
