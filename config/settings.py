from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    simulation_time_step: float = 0.1
    max_agents: int = 100
    api_host: str = '0.0.0.0'
    api_port: int = 8000

    class Config:
        env_file = '.env'

settings = Settings()
