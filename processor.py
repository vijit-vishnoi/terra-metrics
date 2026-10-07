import geopandas as gpd
import fiona
import json
from models import GeospatialFile, FeatureMeasurement
from database import SessionLocal

# Enable fiona KML driver (disabled by default) to allow geopandas to parse KMLs natively
fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['libkml'] = 'rw'

def process_file_db(file_id: str, file_path: str):
    db = SessionLocal()
    try:
        db_file = db.query(GeospatialFile).filter(GeospatialFile.id == file_id).first()
        if not db_file:
            return
            
        if file_path.endswith('.zip'):
            gdf = gpd.read_file(file_path)
        elif file_path.endswith('.kml'):
            gdf = gpd.read_file(file_path, driver='KML')
        else:
            db_file.status = 'ERROR'
            db.commit()
            return

        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
            
        db_file.crs = gdf.crs.to_string()
        db_file.feature_count = len(gdf)
            
        # Reproject to local UTM to calculate accurate metric area/length instead of spherical degrees
        if gdf.crs.is_geographic:
            gdf = gdf.to_crs(gdf.estimate_utm_crs())

        for idx, row in gdf.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            
            geom_type = geom.geom_type
            if geom_type in ('Point', 'MultiPoint'):
                continue
                
            area = None
            length = None
            
            if geom_type in ('Polygon', 'MultiPolygon'):
                area = geom.area
            elif geom_type in ('LineString', 'MultiLineString'):
                length = geom.length
            else:
                continue
                
            props = {k: v for k, v in row.items() if k != 'geometry'}
            props_json = json.dumps(props, default=str)
            
            feature_id = str(idx)
            
            meas = FeatureMeasurement(
                file_id=file_id,
                feature_id=feature_id,
                geometry_type=geom_type,
                properties=props_json,
                area_sqm=area,
                length_m=length
            )
            db.add(meas)
            
        db_file.status = 'COMPLETED'
        db.commit()
    except Exception as e:
        print(f"Error processing {file_id}: {e}")
        db_file = db.query(GeospatialFile).filter(GeospatialFile.id == file_id).first()
        if db_file:
            db_file.status = 'ERROR'
            db.commit()
    finally:
        db.close()
