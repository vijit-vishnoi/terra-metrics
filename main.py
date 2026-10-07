from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import uuid
import os
import shutil

import models
import schemas
import processor
from database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Geospatial File Measurement API")

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/files/", response_model=schemas.FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith((".kml", ".zip")):
        raise HTTPException(status_code=400, detail="Only .kml and .zip files are allowed.")
    
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    db_file = models.GeospatialFile(id=file_id, filename=file.filename, status="PENDING")
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    background_tasks.add_task(processor.process_file_db, file_id, file_path)
    
    return db_file

@app.get("/api/files/{id}/", response_model=schemas.FileResponse)
def get_file_metadata(id: str, db: Session = Depends(get_db)):
    db_file = db.query(models.GeospatialFile).filter(models.GeospatialFile.id == id).first()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return db_file

@app.get("/api/files/{id}/measurements/", response_model=schemas.MeasurementResponse)
def get_file_measurements(id: str, db: Session = Depends(get_db)):
    db_file = db.query(models.GeospatialFile).filter(models.GeospatialFile.id == id).first()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    measurements = db.query(models.FeatureMeasurement).filter(models.FeatureMeasurement.file_id == id).all()
    
    return schemas.MeasurementResponse(id=db_file.id, measurements=measurements)
