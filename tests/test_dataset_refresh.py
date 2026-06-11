import os
import sys
import msal
import requests

AUTHORITY_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}"
SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
BASE_URL = "https://api.powerbi.com/v1.0/myorg"


def get_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=AUTHORITY_TEMPLATE.format(tenant_id=tenant_id)
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" not in result:
        err = result.get("error_description", result.get("error", "unknown error"))
        raise SystemExit(f"\n[FAIL] Token Acquisition Failed:\n{err}\n")
    return result["access_token"]


def main() -> None:
    tenant_id = os.environ.get("PBI_TENANT_ID")
    client_id = os.environ.get("PBI_CLIENT_ID")
    client_secret = os.environ.get("PBI_CLIENT_SECRET")

    missing = [
        name
        for name, val in [
            ("PBI_TENANT_ID", tenant_id),
            ("PBI_CLIENT_ID", client_id),
            ("PBI_CLIENT_SECRET", client_secret)
        ]
        if not val
    ]
    if missing:
        raise SystemExit(
            f"\n[FAIL] Missing env vars: {', '.join(missing)}.\n"
            "Set them and rerun"
        )
    
    token = get_token(tenant_id, client_id, client_secret)
    print("[OK] Token Acquired\n")

    headers = {"Authorization": f"Bearer {token}"}

    # Get workspaces
    print("=== Fetching Workspaces ===")
    resp = requests.get(f"{BASE_URL}/groups", headers=headers, timeout=30)
    resp.raise_for_status()
    workspaces = resp.json().get("value", [])
    
    if not workspaces:
        print("No workspaces found")
        return
    
    for ws in workspaces:
        print(f"Workspace: {ws.get('name')} ({ws.get('id')})\n")
        
        workspace_id = ws.get("id")
        
        # Get datasets with refresh history
        print("  --- Datasets with Refresh History ---")
        datasets_url = f"{BASE_URL}/groups/{workspace_id}/datasets"
        resp = requests.get(datasets_url, headers=headers, timeout=30)
        resp.raise_for_status()
        datasets = resp.json().get("value", [])
        
        if not datasets:
            print("  (no datasets found)")
        else:
            for i, dataset in enumerate(datasets[:5]):  # Show first 5 as demo
                dataset_id = dataset.get("id")
                dataset_name = dataset.get("name")
                print(f"\n    Dataset: {dataset_name}")
                print(f"      ID: {dataset_id}")
                print(f"      All properties: {list(dataset.keys())}")
                
                # Get refresh history for this dataset
                try:
                    refresh_url = f"{BASE_URL}/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
                    refresh_resp = requests.get(refresh_url, headers=headers, timeout=30)
                    if refresh_resp.status_code == 200:
                        refreshes = refresh_resp.json().get("value", [])
                        if refreshes:
                            latest = refreshes[0]
                            print(f"      Last Refresh Status: {latest.get('status', 'N/A')}")
                            print(f"      Last Refresh Time: {latest.get('endTime', 'N/A')}")
                        else:
                            print(f"      No refresh history found")
                    else:
                        print(f"      Refresh history status: {refresh_resp.status_code}")
                except Exception as e:
                    print(f"      Error fetching refresh history: {e}")
            
            if len(datasets) > 5:
                print(f"\n    (... and {len(datasets) - 5} more datasets)")
        
        print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        print(f"\n[FAIL] HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        sys.exit(1)
