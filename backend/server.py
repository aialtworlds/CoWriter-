from fastapi import FastAPI, APIRouter, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from database import init_pool, close_pool
from auth import current_user
from routers import projects, chapters, wallet, analysis, rules, export

app = FastAPI(title='CoWriter API')
api_router = APIRouter(prefix='/api')


@api_router.get('/')
async def root():
    return {'message': 'CoWriter API online'}


@api_router.get('/me')
async def me(user=Depends(current_user)):
    return {'user_id': user['sub'], 'email': user.get('email')}


api_router.include_router(projects.router)
api_router.include_router(chapters.router)
api_router.include_router(wallet.router)
api_router.include_router(analysis.router)
api_router.include_router(rules.router)
api_router.include_router(export.router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=['*'],
    allow_headers=['*'],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.on_event('startup')
async def startup():
    await init_pool()


@app.on_event('shutdown')
async def shutdown():
    await close_pool()
