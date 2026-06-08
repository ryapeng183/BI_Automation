import json
import logging
from datetime import datetime, timezone
from typing import Any

from dateutil import parser as dt_parser

logger = logging.getLogger(__name__)

def compute_duration_seconds(start_time: str | None, end_time: str | None) -> float | None:
    """Compute the duration in seconds between two ISO 8601 timestamps."""
    if not start_time or not end_time:         
        return None
    try:
        st = dt_parser.isoparse(start_time)
        et = dt_parser.isoparse(end_time)
        duration = (et - st).total_seconds()
        return int(duration)
    except Exception as e:
        logger.error(f"Error computing duration: {e}")
        return None
    
def extract_error_code(service_exception_json: str | None) -> str | None:
    """Extract the error code from a JSON string."""
    if not service_exception_json:
        return None
    try:
        data = json.loads(service_exception_json)
        return data.get("errorCode")
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Error extracting error code: {e}")
        return "PARSE_ERROR"
    
def filter_records_by_watermark(raw_records: list[dict[str, Any]], watermark: str | None) -> list[dict[str, Any]]:
    """Filter raw API records to only include those newer than the watermark timestamp."""
    if not watermark:
        return raw_records
    
    wm_dt = dt_parser.isoparse(watermark)
    filtered = []
    for record in raw_records:
        start_time = record.get("startTime")
        if not start_time:
            filtered.append(record) 
            continue
        try:
            if dt_parser.isoparse(start_time) > wm_dt:
                filtered.append(record)
        except (ValueError, TypeError):
            filtered.append(record)
    return filtered

def transform_refresh_records(
        raw_records: list[dict[str, Any]],
        dataset_id: str,
        dataset_name: str,
        workspace_id: str,
        workspace_name: str,
        is_critical: bool,
) -> list[dict[str, Any]]:
    """Transform raw API records into a structured format for storage."""
    ingestion_ts = datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []

    for record in raw_records:
        request_id = record.get("requestId")
        if not request_id:
            logger.warning("Skipping record with missing requestId: %s", record)
            continue

        start_time = record.get("startTime")
        end_time = record.get("endTime")
        svc_exception = record.get("serviceExceptionJson")
        attempts = record.get("refreshAttempts", [])

        rows.append(
            {
                "request_id": request_id,
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "workspace_id": workspace_id,
                "workspace_name": workspace_name,
                "refresh_type": record.get("refreshType"),
                "status": record.get("status"),
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": compute_duration_seconds(start_time, end_time),
                "service_exception_json": svc_exception,
                "error_code": extract_error_code(svc_exception),
                "refresh_attempts_json": json.dumps(attempts) if attempts else None,
                "attempt_count": len(attempts),
                "is_critical": is_critical,
                "ingestion_timestamp": ingestion_ts.isoformat(),
                "ingestion_date": ingestion_ts.strftime("%Y-%m-%d"),
            }
    )