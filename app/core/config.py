from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 数据库配置
    #database_url: str
    db_user: str
    db_password: str
    db_name: str
    db_host: str
    db_port: int

    redis_url: str

    # OpenAI配置
    openai_api_key: str

    # JWT配置
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # 应用配置
    app_name: str = "智能内容聚合平台"
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()
