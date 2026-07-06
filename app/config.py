from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    hf_token: str
    model_id: str = "Qwen/Qwen2.5-Coder-7B-Instruct"
    github_token: str = ""
    database_url: str = "sqlite:///./smartdoc.db"
    app_env: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()