from fastapi import FastAPI, File, UploadFile, HTTPException
from firebase_admin import credentials, initialize_app, storage
import os
from repository.firebase.serviceAccountKey import service_account_key_file

app = FastAPI()

cred = credentials.Certificate(service_account_key_file())
firebase_app = initialize_app(cred, {
    'storageBucket': 'cvai-92a44.appspot.com',
})

@app.post("/upload-cv")
async def upload_file(file: UploadFile = File(...)):
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, detail="Invalid file type. Supported types: PDF, DOC, DOCX, TXT"
        )

    # Upload file to Firebase Storage
    folder_name = "CVs"
    blob = storage.bucket().blob(f"{folder_name}/{file.filename}")
    try:
        blob.upload_from_file(file.file, content_type=file.content_type)
        blob.make_public()  # Make the file publicly accessible

        return {
            "filename": file.filename,
            "url": blob.public_url,  # Return the public URL of the file
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@app.post("/upload-jd")
async def upload_file(file: UploadFile = File(...)):
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, detail="Invalid file type. Supported types: PDF, DOC, DOCX, TXT"
        )

    # Upload file to Firebase Storage
    folder_name = "JobDescription"
    blob = storage.bucket().blob(f"{folder_name}/{file.filename}")
    try:
        blob.upload_from_file(file.file, content_type=file.content_type)
        blob.make_public()  # Make the file publicly accessible

        return {
            "filename": file.filename,
            "url": blob.public_url,  # Return the public URL of the file
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
