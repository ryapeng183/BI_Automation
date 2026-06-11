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
        
        # Get reports in this workspace
        print("  --- Reports ---")
        reports_url = f"{BASE_URL}/groups/{workspace_id}/reports"
        resp = requests.get(reports_url, headers=headers, timeout=30)
        resp.raise_for_status()
        reports = resp.json().get("value", [])
        
        if not reports:
            print("  (no reports found)")
        else:
            for report in reports:
                print(f"    - {report.get('name')}")
                print(f"      ID: {report.get('id')}")
                print(f"      WebURL: {report.get('webUrl')}")
        
        # Get datasets in this workspace
        print("\n  --- Datasets ---")
        datasets_url = f"{BASE_URL}/groups/{workspace_id}/datasets"
        resp = requests.get(datasets_url, headers=headers, timeout=30)
        resp.raise_for_status()
        datasets = resp.json().get("value", [])
        
        if not datasets:
            print("  (no datasets found)")
        else:
            for dataset in datasets:
                print(f"    - {dataset.get('name')}")
                print(f"      ID: {dataset.get('id')}")
                print(f"      RefreshState: {dataset.get('refreshState', 'N/A')}")
        
        print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        print(f"\n[FAIL] HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        sys.exit(1)
