from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./ledgerforge.db"
    data_dir: str = "../03_Data/csv"
    secret_key: str
    demo_admin_password: str
    demo_hr_password: str
    demo_employee_password: str

    model_config = SettingsConfigDict(env_file=".env")
settings = Settings()