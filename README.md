# Terra Metrics: Geospatial File Measurement API

A FastAPI-based web service that accepts uploaded spatial data files (.kml and .zip Shapefiles), automatically parses their contents, dynamically reprojects geographic coordinates to local planar coordinate systems (UTM), and calculates metrics like area for Polygons and length for LineStrings.

## Setup Instructions

### Prerequisites
- Python 3.12+

### Installation & Running Locally

1. **Clone or navigate to the repository:**
   ```bash
   cd terra-metrics
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn python-multipart sqlalchemy pytest httpx geopandas fiona shapely
   ```

4. **Run the FastAPI server:**
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://127.0.0.1:8000`. You can also access the interactive OpenAPI documentation at `http://127.0.0.1:8000/docs`.

### Running Tests
To run the automated tests using Pytest:
```bash
pytest -v
```

## API Documentation

### 1. Upload Geospatial File
**Endpoint:** `POST /api/files/`

**Description:** Uploads a `.kml` or `.zip` (containing a Shapefile) to the server. The processing job is pushed to the background while returning an immediate response.

**Request:** `multipart/form-data` containing a `file` field.

**Response (201 Created):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "parcels.zip",
  "status": "PENDING"
}
```

### 2. Get File Metadata
**Endpoint:** `GET /api/files/{id}/`

**Description:** Retrieves the metadata and processing status of a previously uploaded file.

**Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "parcels.zip",
  "status": "COMPLETED"
}
```

### 3. Get Feature Measurements
**Endpoint:** `GET /api/files/{id}/measurements/`

**Description:** Retrieves the parsed features, their geometric measurements (area or length in meters), and arbitrary properties extracted from the file.

**Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "measurements": [
    {
      "feature_id": "0",
      "geometry_type": "Polygon",
      "properties": "{\"Name\": \"Parcel A\", \"Zoning\": \"Residential\"}",
      "area_sqm": 4500.5,
      "length_m": null
    },
    {
      "feature_id": "1",
      "geometry_type": "LineString",
      "properties": "{\"Name\": \"Access Road\"}",
      "area_sqm": null,
      "length_m": 150.2
    }
  ]
}
```

## Architecture

- **`main.py`**: The application entry point containing FastAPI route definitions and dependency injections. Handles asynchronous background task delegation.
- **`processor.py`**: The core geospatial engine. Responsible for reading files via `geopandas`, detecting coordinate reference systems (CRS), performing UTM reprojection, executing `shapely` geometry measurements, and writing results to the database.
- **`models.py`**: SQLAlchemy ORM definitions linking files and individual feature measurements using foreign keys.
- **`schemas.py`**: Pydantic models (V2) handling data validation and serialization for API requests and responses.
- **`database.py`**: Bootstraps a lightweight SQLite database (`terra_metrics.db`) to track processing status and measurements.

## Design Decisions

- **GeoPandas & Fiona**: Used as the backbone for reading and manipulating spatial data. GeoPandas abstracts away the complexity of managing CRS transforms and geometric operations. Fiona acts as the robust I/O engine capable of handling complex formats like `.zip` compressed Shapefiles and nested `.kml` geometries seamlessly.
- **Dynamic CRS Handling (UTM)**: Geographic coordinate systems (like EPSG:4326/WGS84) express coordinates in degrees. Calculating raw area/length directly on a spherical model yields meaningless geometric degrees. To provide precise metric measurements (square meters, linear meters), the application dynamically calculates the optimal local UTM zone for the dataset using `geopandas.estimate_utm_crs()` and reprojects the spatial data into that planar coordinate system before running Shapely area/length computations.
- **Background Tasks**: Geospatial files can be large and parsing them synchronously blocks API threads. Upload endpoints immediately return a `PENDING` status while deferring the heavy geospatial lifting to FastAPI's built-in `BackgroundTasks`.

## Learnings and Future Scope

### Learnings
- Managing mixed-geometry tests locally required circumventing Shapefile format limitations (Shapefiles do not support mixing Polygons and Points in the same file). By utilizing a raw KML payload for tests, the test suite could seamlessly validate geometry filtering (e.g. skipping Points) and complex measurements in a single assertion run.
- Using FastAPI's Starlette test client automatically resolves background tasks synchronously, massively simplifying assertion logic for background-processed resources without needing arbitrary timeouts.

### Future Scope
- **Storage Strategy**: Move from a local `temp_uploads` folder and SQLite database to cloud block storage (e.g., AWS S3) and a robust relational database (PostgreSQL with PostGIS) for horizontal scalability.
- **Robust Queueing**: Upgrade from FastAPI `BackgroundTasks` to Celery or RQ paired with Redis/RabbitMQ to handle job retries, dead-letter queues, and complex asynchronous state tracking across multiple worker nodes.
- **Enhanced Spatial Analytics**: Extend geometry support to complex TopoJSON, generate centroids, measure perimeter for polygons, or validate topology against OGC standards.
