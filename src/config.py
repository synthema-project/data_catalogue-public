import os


def get_env_variable(name: str) -> str:
    """Fetches an environment variable and raises an exception if it's missing."""
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _get_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    # PostgreSQL (shared with the data-ingestor, which writes the same tables)
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "dataset_catalogue")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "appuser")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "apppassword")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    # Public MinIO/object-storage host that is prefixed onto the stored dataset
    # paths (i.e. what appears in GET /usecases). Clients strip this prefix and
    # connect to their own MINIO_ENDPOINT, so this is the *catalogue's* notion of
    # the object-storage location, independent of where bytes were uploaded.
    MINIO_PUBLIC_URL: str = os.getenv(
        "MINIO_PUBLIC_URL", "obstorageapi.k8s.synthema.rid-intrasoft.eu"
    ).rstrip("/")

    # HTTP server port
    APP_PORT: int = int(os.getenv("APP_PORT", "83"))


settings = Settings()

# Keycloak (auth). Defaults preserve the previously hardcoded values.
KEYCLOAK_SERVER_URL: str = os.getenv("KEYCLOAK_SERVER_URL", "https://identity.gatv.es")
KEYCLOAK_CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "synthema")
KEYCLOAK_REALM_NAME: str = os.getenv("KEYCLOAK_REALM_NAME", "Synthema")
# Public key used to decode Keycloak tokens (PEM body, no header/footer).
KEYCLOAK_PUBLIC_KEY: str = os.getenv("KEYCLOAK_PUBLIC_KEY", "")
# When true, bypass authentication (e2e/dev only).
AUTH_DISABLE_TESTS: bool = _get_bool("AUTH_DISABLE_TESTS", False)
