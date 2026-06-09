import os
import sys
import msal
import requests

AUTHORITY_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}"
SCOPE = ["https:analysis.windows.net/powerbi/api/.default"]
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
    print(" [OK] Token Acquired")

    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(f"{BASE_URL}/groups", headers=headers, timeout=30)
    if resp.status_code == 401:
        raise SystemExit(
            "[FAIL] 401 unauthorized"
        )
    if resp.status_code == 403:
        raise SystemExit(
            "[FAIL] 403 Forbidden - not allowed"
        )
    resp.raise_for_status()

    workspaces = resp.json().get("value", [])
    print("[OK] API call succeeded")
    for ws in workspaces:
        print(" - {es.get('name')}  ({ws.get('id')})")
    if not workspaces:
        print(
            " (none yet- epected if the SP hasn't been added as a member of any workspace) "
        )

    if __name__ == "__main__":
        try:
            main()
        except requests.HTTPError as e:
            print(f"\n [FAIL] http error")
            sys.exit(1)