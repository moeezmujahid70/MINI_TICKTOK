from pydantic import BaseSettings


class Config(BaseSettings):
    app_version: str = '1.0'
    app_title: str = 'Mini TICTOK API'
    app_url: str
    app_release_stage: str = 'production'

    db_uri: str
    db_default_database: str = 'Mini_TickTok_v1'

    mega_email = str
    mega_password = str

    jwt_secret: str
    jwt_algorithm = 'HS256'
    jwt_access_token_expire_minutes = 30
    jwt_refresh_token_expire_days = 30

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        env_prefix = 'APP_'


config = Config()
