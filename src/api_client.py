import logging 
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


logger = logging.getLogger(__name__)

BASE_URL = "https://api.powerbi.com/v1.0/myorg"

RETRYABLE_STATUS_CODES = [429, 500, 502, 503, 504]

class PowerBIClient:
    """REST client for the Power BI API with retry logic"""

    def __init__(
        self, 
        access_token: str,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        request_timeout: int = 30,
    ):
        self._access_token = access_token
        self._request_timeout = request_timeout
        self._session = self._create_session(max_retries, backoff_factor)

    def _create_session(self, max_retries: int, backoff_factor: float) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=RETRYABLE_STATUS_CODES,
            allowed_methods=["GET"],
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        return session
    
    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }  
    
    def get_refresh_history(
            self,
            workspace_id: str,
            dataset_id: str,
            top: int = 60,
    ) -> list[dict[str, Any]]:
        url = f"{BASE_URL}/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
        params = {"$top": top}
        response = self._session.get(url, headers=self._headers, params=params, timeout=self._request_timeout)
        response.raise_for_status()
        return response.json().get("value", [])
    
    def get_refresh_history_safe(
            self,
            workspace_id: str,
            dataset_id: str,
            dataset_name: str,
            top: int = 60,
    ) -> list[dict[str, Any]]:
        try:
            return self.get_refresh_history(workspace_id, dataset_id, top)
        except requests.RequestException as e:
            status = e.response.status_code if e.response is not None else None
            if status == 404:
                logger.warning(f"Dataset not found: {dataset_name} (ID: {dataset_id}) in workspace {workspace_id}")
                return []
            if status == 403:
                logger.warning(f"Access forbidden for dataset: {dataset_name} (ID: {dataset_id}) in workspace {workspace_id}")
                return []
            raise

    def get_datasets_in_workspace(self, workspace_id: str) -> list[dict[str, Any]]:
        url = f"{BASE_URL}/groups/{workspace_id}/datasets"
        response = self._session.get(url, headers=self._headers, timeout=self._request_timeout)
        response.raise_for_status()
        return response.json().get("value", [])
    
    def get_datasets_in_workspace_safe(self, workspace_id: str) -> list[dict[str, Any]]:
        try:
            return self.get_datasets_in_workspace(workspace_id)
        except requests.RequestException as e:
            status = e.response.status_code if e.response is not None else None
            if status == 404:
                logger.warning(f"Workspace not found: {workspace_id}")
                return []
            if status == 403:
                logger.warning(f"Access forbidden for workspace: {workspace_id}")
                return []
            raise

    def close(self):
        self._session.close()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    