import pytest
from fastapi.testclient import TestClient
import os
import tempfile
import time

from main import app
from database import Base, engine

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_polygon_reprojection_and_point_skip():
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>test_point</name>
      <Point>
        <coordinates>-122.4194,37.7749,0</coordinates>
      </Point>
    </Placemark>
    <Placemark>
      <name>test_poly</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              -122.4,37.7,0
              -122.3,37.7,0
              -122.3,37.8,0
              -122.4,37.8,0
              -122.4,37.7,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>"""

    with tempfile.TemporaryDirectory() as tmpdir:
        kml_path = os.path.join(tmpdir, "test.kml")
        with open(kml_path, "w") as f:
            f.write(kml_content)
            
        with open(kml_path, 'rb') as f:
            response = client.post(
                "/api/files/",
                files={"file": ("test.kml", f, "application/vnd.google-earth.kml+xml")}
            )
            
    assert response.status_code == 201
    file_id = response.json()["id"]
    
    time.sleep(0.5)
    
    response_metadata = client.get(f"/api/files/{file_id}/")
    assert response_metadata.status_code == 200
    meta = response_metadata.json()
    assert meta["feature_count"] == 2
    assert meta["crs"] is not None
    assert "4326" in meta["crs"]
    
    response_meas = client.get(f"/api/files/{file_id}/measurements/")
    assert response_meas.status_code == 200
    
    data = response_meas.json()
    assert data["id"] == file_id
    measurements = data["measurements"]
    
    # Points are intentionally skipped per requirements
    assert len(measurements) == 1
    
    m = measurements[0]
    assert m["geometry_type"] == "Polygon"
    assert m["area_sqm"] is not None
    # Area must be correctly projected in square meters, not geographic degrees
    assert m["area_sqm"] > 1000.0
