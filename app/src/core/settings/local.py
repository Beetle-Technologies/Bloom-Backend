from .base import Settings as BaseSettings


class Settings(BaseSettings):
    ALLOW_TESTING_ENVIRONMENT: bool = True
