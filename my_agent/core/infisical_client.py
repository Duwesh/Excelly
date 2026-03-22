import asyncio
import os
from my_agent.core.execution_var import Environment, Secrets
from my_agent.core.logging_config import setup_logging

logger = setup_logging()

try:
    from infisical_sdk import InfisicalSDKClient
    HAS_INFISICAL = True
except ImportError:
    HAS_INFISICAL = False

def get_infisical_client():
    if not HAS_INFISICAL:
        return None
    try:
        client = InfisicalSDKClient(host="https://app.infisical.com")
        client.auth.universal_auth.login(
            Secrets.INFISICAL_CLIENT_ID,
            Secrets.INFISICAL_CLIENT_TOKEN,
        )
        return client
    except Exception as e:
        logger.error("Error in Connecting to Infisical!", error=e)
        return None

def get_secret(secret_name):
    env_val = os.environ.get(secret_name)
    if env_val:
        return env_val

    if HAS_INFISICAL:
        try:
            client = get_infisical_client()
            if client:
                secret = client.secrets.get_secret_by_name(
                    secret_name=secret_name,
                    project_id=Secrets.INFISICAL_PROJECT_ID,
                    environment_slug=Environment.ENVIRONMENT,
                    secret_path="/",
                ).secretValue
                return secret
        except Exception as e:
            logger.error("Retrieving Secret failed from Infisical", secret_name=secret_name, error=str(e))
    
    return None

async def aget_secret(secret_name):
    return await asyncio.to_thread(get_secret, secret_name)
