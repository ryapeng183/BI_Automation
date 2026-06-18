import logging
import time 
from typing import Any
from src.api_client import PowerBIClient

logger = logging.getLogger(__name__)


def resolve_dataset_registry(
    client: PowerBIClient,
    datasets_config: dict[str, Any],
    inter_request_delay: float = 0.2
) -> list[dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}

    for entry in datasets_config.get("datasets", []):
        if not entry.get("is_active", True):
            continue
        ds_id = entry["dataset_id"]
        result[ds_id] = {
            "workspace_id": entry["workspace_id"],
            "workspace_name": entry["workspace_name"],
            "dataset_id": ds_id,
            "dataset_name": entry["dataset_name"],
            "is_critical": entry.get("is_critical", False),
            "is_active": True,
        }

    for ws_entry in datasets_config.get("workspaces", []):
        if not ws_entry.get("is_active", True):
            continue
        ws_id = ws_entry["workspace_id"]
        ws_name = ws_entry["workspace_name"]
        exclude = set(ws_entry.get("exclude_datasets", []))
        is_critical_default = ws_entry.get("is_critical_default", False)

        logger.info("Discovering datasets in workspace '%s' ", ws_name, ws_id)

        api_datasets = client.get_datasets_in_workspace_safe(ws_id, ws_name)

        discovered = 0
        for ds in api_datasets:
            ds_id = ds.get("id")
            if not ds_id or ds_id in exclude:
                continue
            if ds_id not in result:
                result[ds_id] = {
                    "workspace_id": ws_id,
                    "workspace_name": ws_name,
                    "dataset_id": ds_id,
                    "dataset_name": ds.get("name", "Unknown"),
                    "is_critical": is_critical_default,
                    "is_active": True
                }
                discovered += 1

        logger.info(
            " Discovered %d new datasets (total API: %d, excluded: %d)",
            discovered,
            len(api_datasets),
            len(exclude)
        )

        time.sleep(inter_request_delay)
    
    return list(result.values())