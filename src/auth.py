import logging
import msal

logger = logging.getLogger(__name__)

POWER_BI_SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]

class PowerBIAuthenticator:
    def __init__(self, tenant_id: str, client_id:str, client_secret:str):
        self._authority = f"https://login.microsoftonline.com/{tenant_id}"
        self._app = msal.ConfidentialClientApplication(
            client_id=client_id,
            authority=self._authority,
            client_credential=client_secret,
        )

    def get_access_token(self) -> str:

        result = self._app.acquire_token_silent(scopes=POWER_BI_SCOPE, account=None)
        if not result:
            logger.info("No suitable token exists in cache. Getting a new one via client credentials")
            result = self._app.acquire_token_for_client(scopes=POWER_BI_SCOPE)
        if "access_token" in result:
            return result["access_token"]
        
        error = result.get("error_description", result.get("error", "Unknown authentcation error"))
        raise RunTimeError(f"Failed to acquire access token: {error}")
    
    def create_authenticator_from_secrets(dbutils) -> PowerBIAuthenticator:
        scope = "powerbi-montor"
        tenant_id = dbutils.secrets.get(scope=scope, key="tenant-id")
        client_id = dbutils.secrets.get(scope=scope, key="client-id")
        client_secret = dbutils.secrets.get(scope=scope, key="client-secret")
        return PowerBIAuthenticator(tenant_id, client_id, client_secret)