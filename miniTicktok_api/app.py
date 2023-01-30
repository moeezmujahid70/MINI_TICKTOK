from fastapi import FastAPI
from miniTicktok_api.config import config
from miniTicktok_api.docs.docs import load_api_readme, load_api_tags


from miniTicktok_api.routes import auth
from miniTicktok_api.routes import users
from miniTicktok_api.routes import post
from miniTicktok_api.routes import videos


app = FastAPI(
    version=config.app_version,
    title=config.app_title,
    description=load_api_readme(),
    openapi_tags=load_api_tags()
)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(post.router)
app.include_router(videos.router)
