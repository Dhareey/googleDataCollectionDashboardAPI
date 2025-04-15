import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import csv
from io import StringIO


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# List of mandatory columns that must exist in the CSV
REQUIRED_COLUMNS_1 = {
    'road_name (new)': "Road name in new format",
    'cam_no': "Camera number",
    'status': "Status of collection",
    'File Name': "Collection date",
    'Upload_status': "Upload status",
    'VID': "VID number",
    'Container ID': "Container ID",
    "Usability": "Ingestion Tracker",
    "lenn (Timi)": "Covered length in meters"
}

REQUIRED_COLUMNS_2 = {
    'driving_hub_name': "Hubname", 
    'target_distance_collected': "DIstance collected according to Google", 
    'target_distance_available': "Google total distance availale"}

def verify_csv_headers(headers: List[str], task: str) -> None:
    if task == "roads":
        REQUIRED_COLUMNS = REQUIRED_COLUMNS_1
    else:
        REQUIRED_COLUMNS = REQUIRED_COLUMNS_2
    """Verify all required columns are present in the CSV"""
    missing_columns = [col for col in REQUIRED_COLUMNS.keys() if col not in headers]
    if missing_columns:
        error_msg = f"Missing required columns: {', '.join(missing_columns)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=400,
            detail={
                "message": "CSV validation failed",
                "missing_columns": missing_columns,
                "required_columns": list(REQUIRED_COLUMNS.keys())
            }
        )
        
async def parse_uploaded_file(file: UploadFile, task: str ) -> List[dict]:
    """Parse the uploaded CSV file and return rows as dictionaries"""
    try:
        contents = await file.read()
        data = StringIO(contents.decode('utf-8-sig'))
        csv_reader = csv.DictReader(data)
        
        # Verify headers before processing
        verify_csv_headers(csv_reader.fieldnames, task)
        
        return list(csv_reader)
    except Exception as e:
        logger.error(f"Error parsing file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")