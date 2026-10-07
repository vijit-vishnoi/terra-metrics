import pytest
from fastapi.testclient import TestClient
from main import app, get_db, models
from database import Base, engine, SessionLocal

Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_upload_invalid_extension():
    response = client.post(
        "/api/files/",
        files={"file": ("test.txt", b"test content", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Only .kml and .zip files are allowed."

def test_upload_and_get_kml():
    response = client.post(
        "/api/files/",
        files={"file": ("test.kml", b"<kml></kml>", "application/vnd.google-earth.kml+xml")}
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "test.kml"
    assert data["status"] == "PENDING"
    
    file_id = data["id"]
    
    response_get = client.get(f"/api/files/{file_id}/")
    assert response_get.status_code == 200
    data_get = response_get.json()
    assert data_get["id"] == file_id
    assert data_get["filename"] == "test.kml"
    assert data_get["status"] == "ERROR"
    
    response_meas = client.get(f"/api/files/{file_id}/measurements/")
    assert response_meas.status_code == 200
    data_meas = response_meas.json()
    assert data_meas["id"] == file_id
    assert data_meas["measurements"] == []
