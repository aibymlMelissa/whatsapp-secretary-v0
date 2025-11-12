# app/routers/files.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import uuid
from pathlib import Path
from datetime import datetime

from database.database import get_db
from database.models import FileRecord

router = APIRouter()

# Configure upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    'document': ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx'],
    'video': ['.mp4', '.avi', '.mov', '.mkv'],
    'audio': ['.mp3', '.wav', '.ogg', '.m4a']
}

def get_file_type(filename: str) -> str:
    """Determine file type based on extension"""
    ext = Path(filename).suffix.lower()
    for file_type, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    return 'other'

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a file and save to database"""
    try:
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename

        # Save file to disk
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        # Create database record
        file_record = FileRecord(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=len(contents),
            mime_type=file.content_type or get_file_type(file.filename)
        )

        db.add(file_record)
        db.commit()
        db.refresh(file_record)

        return {
            "id": file_record.id,
            "filename": file_record.original_filename,
            "size": file_record.file_size,
            "mime_type": file_record.mime_type,
            "created_at": file_record.created_at.isoformat(),
            "status": "uploaded"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to upload file: {str(e)}")

@router.get("/list")
async def list_files(db: Session = Depends(get_db)):
    """List all uploaded files"""
    try:
        files = db.query(FileRecord).order_by(FileRecord.created_at.desc()).all()

        return {
            "files": [
                {
                    "id": f.id,
                    "filename": f.original_filename,
                    "size": f.file_size,
                    "mime_type": f.mime_type,
                    "created_at": f.created_at.isoformat(),
                    "chat_id": f.chat_id,
                    "message_id": f.message_id
                }
                for f in files
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@router.get("/download/{file_id}")
async def download_file(file_id: int, db: Session = Depends(get_db)):
    """Download a file by ID"""
    try:
        file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()

        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")

        file_path = Path(file_record.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")

        return FileResponse(
            path=file_path,
            filename=file_record.original_filename,
            media_type=file_record.mime_type
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

@router.delete("/delete/{file_id}")
async def delete_file(file_id: int, db: Session = Depends(get_db)):
    """Delete a file"""
    try:
        file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()

        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")

        # Delete file from disk
        file_path = Path(file_record.file_path)
        if file_path.exists():
            file_path.unlink()

        # Delete from database
        db.delete(file_record)
        db.commit()

        return {
            "message": f"File {file_record.original_filename} deleted successfully",
            "id": file_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")