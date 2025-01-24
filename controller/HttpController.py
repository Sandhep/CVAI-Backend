
from fastapi import APIRouter, HTTPException, UploadFile, File

from service.FileProcess import FileProcess

from typing import List

from pydantic import BaseModel


router = APIRouter()

class FileResponse(BaseModel):
    name: str
    summary: str
    url: str

class MatchCVRequest(BaseModel):
    selected_jd: str
    top_n: int
    model: str

@router.post('/upload-cvs')
async def handleCVs(files: List[UploadFile] = File(...)):

    allowed_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]

    uploadedFiles = []

    for file in files:

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type for {file.filename}. Supported types: PDF, DOC, DOCX, TXT"
            )
        

        res = await FileProcess.cvProcess(file)
        
        uploadedFiles.append(res)

    return {"uploaded_CVs":uploadedFiles}    


@router.post('/upload-jds')
async def handleJDs(files: List[UploadFile] = File(...)):

    allowed_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]

    uploadedFiles = []

    for file in files:

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type for {file.filename}. Supported types: PDF, DOC, DOCX, TXT"
            )
        

        res = await FileProcess.jdProcess(file)
        
        uploadedFiles.append(res)

    return {"uploaded_JDs":uploadedFiles}    

@router.get("/user-cvs", response_model=List[FileResponse])
async def get_user_cvs():
    try:

        response = await FileProcess.fetchCV()

        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-jds", response_model=List[FileResponse])
async def get_user_cvs():
    try:

        response = await FileProcess.fetchJD()

        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/find-match")
async def find_match(request: MatchCVRequest):
    try:
        selected_jd = request.selected_jd
        top_n = request.top_n
        model = request.model

        response = await FileProcess.findMatchingCV(selected_jd,top_n,model)

        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))