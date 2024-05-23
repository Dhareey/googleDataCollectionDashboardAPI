from sqlalchemy.orm import Session
from api.models.models import CameraCoverage
from datetime import date

def update_camera_coverage_background(collection_date: date, camera_number: int, road_length: float, db: Session):
    try:
        # Get or create the CameraCoverage record for the given date
        coverage = db.query(CameraCoverage).filter(CameraCoverage.date == collection_date).first()

        if coverage is None:
            coverage = CameraCoverage(
                date=collection_date, 
                camera_1_total=0.0, 
                camera_2_total=0.0,
                camera_3_total=0.0,
                camera_4_total=0.0,
                camera_5_total=0.0,
                camera_6_total=0.0
            )
            db.add(coverage)
            db.flush()  # Ensure the new row gets an ID

        # Update the appropriate camera column
        if camera_number == 1:
            coverage.camera_1_total = (coverage.camera_1_total or 0) + road_length
        elif camera_number == 2:
            coverage.camera_2_total = (coverage.camera_2_total or 0) + road_length
        elif camera_number == 3:
            coverage.camera_3_total = (coverage.camera_3_total or 0) + road_length
        elif camera_number == 4:
            coverage.camera_4_total = (coverage.camera_4_total or 0) + road_length
        elif camera_number == 5:
            coverage.camera_5_total = (coverage.camera_5_total or 0) + road_length
        elif camera_number == 6:
            coverage.camera_6_total = (coverage.camera_6_total or 0) + road_length

        db.commit()
    except Exception as e:
        db.rollback()  # Rollback the transaction in case of error
        raise e
    finally:
        db.close()  # Ensure the session is closed
