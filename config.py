import os


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


HOST = get_env("HOST", "0.0.0.0")
PORT = int(get_env("PORT", "8000"))

ADMIN_API_KEY = get_env("ADMIN_API_KEY")

DEFAULT_PROVIDER = get_env("DEFAULT_PROVIDER", "openrouter")
DEFAULT_MODEL = get_env("DEFAULT_MODEL")

PROVIDER_KEYS = {
    "openai": get_env("OPENAI_API_KEY"),
    "groq": get_env("GROQ_API_KEY"),
    "openrouter": get_env("OPENROUTER_API_KEY"),
    "gemini": get_env("GEMINI_API_KEY"),
    "huggingface": get_env("HUGGINGFACE_API_KEY"),
    "bazaarlink": get_env("BAZAARLINK_API_KEY"),
}

BAZAARLINK_BASE_URL = get_env("BAZAARLINK_BASE_URL", "https://api.bazaarlink.ai/v1").rstrip("/")

VEKTORFLOW_API_KEY = get_env("VEKTORFLOW_API_KEY")
