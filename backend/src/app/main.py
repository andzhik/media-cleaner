import asyncio
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from .api import routes_tree, routes_list, routes_process, routes_jobs


app = FastAPI(title="Video Cleaner API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_tree.router, prefix="/api")
app.include_router(routes_list.router, prefix="/api")
app.include_router(routes_process.router, prefix="/api")
app.include_router(routes_jobs.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Video Cleaner API is running"}

