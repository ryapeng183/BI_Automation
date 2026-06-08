import json 
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("powerbi_refresh_pipeline")

REPO_ROOT = "/Workspace/Repos/ryapeng@vancity.com/powerbi-refresh-monitor"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.auth import PowerBIAuthenticator
from src.api_client import PowerBIClient
from src.transform import transform_refresh_records, ilter_records_by_watermark
from src.delta_ops import (
    ensure_table_exists,
    upsert_fresh_data,
    get_watermarks,
    REFRESH_HISTORY_SCHEMA,
)
from src.discovery import resolve_dataset_registry
from src.alerts import AlertDispatcher, check_refres_failures, check_refresh_failures, check_duration_anomalies, check_stale_data

#load pipeline config
with open(f"{REPO_ROOT}/config/pipeline_config.json") as f:
    pipeline_config = json.load(f)
with open(f"{REPO_ROOT}/config/datasets.json") as f:
    datasets_config = json.load(f)

delta_cfg = pipeline_config["delta_table"]
TABLE_NAME = f"{delta_cfg['catalog']}.{delta_cfg['schema']}.{delta_cfg['table_name']}"

api_cfg = pipeline_config["api"]
alert_cfg = pipeline_config["alerting"]
extraction_cfg = pipeline_config.get("extraction", {})
increnemental_enabled = extraction_cfg.get("incremental", True)

logger.info("Pipeline config loaded.")
logger.info("Target Delta table: %s", TABLE_NAME)
logger.info("Incremental extraction: %s", "enabled" if increnemental_enabled else "disabled")

#Read credentials from Databricks secrets
secrets_cfg = pipeline_config["secrets"]
tenant_id = dbutils.secrets.get(secrets_cfg["scope"], secrets_cfg["tenant_id"])
client_id = dbutils.secrets.get(secrets_cfg["scope"], secrets_cfg["client_id"])
client_secret = dbutils.secrets.get(secrets_cfg["scope"], secrets_cfg["client_secret_key"])

#get OAuth2 token
authenticator = PowerBIAuthenticator(tenant_id, client_id, client_secret)
access_token = authenticator.get_access_token()
logger.info("Access token acquired.")


client = PowerBIClient(
    access_token=access_token,
    max_retries=api_cfg["max_retries"],
    backoff_factor=api_cfg["backoff_factor"],
    request_timeout=api_cfg["request_timeout_seconds"],
)

resolved_datasets = resolve_dataset_registry(
    client=client,
    datasets_config=datasets_config,
    inter_request_delay=api_cfg.get("inter_request_delay_seconds", 0.2),
)

logger.info("resolved %d active datasets to process.", len(resolved_datasets))



ensure_table_exists(spark, TABLE_NAME)

if increnemental_enabled:
    watermarks = get_watermarks(spark, TABLE_NAME)
    logger.info("Loaded watermarks for %d datasets.", len(watermarks))
else:
    watermarks = {}
    logger.info("full extraction enabled, ignoring watermarks.")


#Extract refresh histories

max_workers = api_cfg.get("max_concurrent_requests", 4)
top_records = api_cfg["top_records_per_dataset"]

stats = {"datasets_processed": 0, "datasets_skipped": 0, "datasets_failed": 0}

def extract_dataset(dataset_entry: dict) -> list[dict]:
    """extract and transform refresh history for a single dataset"""
    ws_id =dataset_entry["workspace_id"]
    ds_id = dataset_entry["dataset_id"]
    ds_name = dataset_entry["dataset_name"]
    ws_name = dataset_entry["workspace_name"]
    is_critical = dataset_entry.get("is_critical", False)
    wm = watermarks.get(ds_id)

    raw_records = client.get_refresh_history(
        workspace_id=ws_id,
        dataset_id=ds_id,
        dataset_name=ds_name,
        top=top_records,
    )

    if not raw_records:
        return []
    
    filtered = filter_records_by_watermark(raw_records, wm)

    if  not filtered:
        logger.info("'%s': all %d records already known, skipping.", ds_name, len(raw_records), wm)
        return []
    
    transformed = transform_refresh_records(
        raw_records=filtered,
        dataset_id=ds_id,
        dataset_name=ds_name,
        workspace_id=ws_id,
        workspace_name=ws_name,
        is_critical=is_critical,
    )

    logger.info("'%s': extracted %d new records (watermark=%s).", ds_name, len(transformed), wm or "none")
    return transformed

all_records = []

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    future_to_entry = {executor.submit(extract_dataset, entry): entry for entry in resolved_datasets}
    for future in as_completed(future_to_entry):
        dataset_entry = future_to_entry[future]
        try:
            records = future.result()
            if records:
                all_records.extend(records)
                stats["datasets_processed"] += 1
            else:
                stats["datasets_skipped"] += 1
        except Exception as e:  
            logger.error("Error processing dataset '%s': %s", entry.get("dataset_name", "?"), entry.get("dataset_id", "?"), exc,)
            stats["datasets_failed"] += 1


# load delta table
# if alert_cfg.get("enabled", False) and all_records:
#     dispatcher = AlertDispatcher(teams_webhook_url=alert_cfg.get("teams_webhook_url"))

client.close()

print("="*50)
print("PIPELINE RUN SUMMARY")
print("="*50)
print(f"Total datasets resolved: {len(resolved_datasets)}")
print(f"Datasets processed: {stats['datasets_processed']}")
print(f"Datasets skipped (no new records): {stats['datasets_skipped']}")
print(f"Datasets failed: {stats['datasets_failed']}")
print(f"Records ingested: {len(all_records)}")
print(f"Target Delta table: {TABLE_NAME}")
print(f"Incremental: {'yes' if increnemental_enabled else 'no'}")
