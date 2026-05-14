from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import schools, districts, communities

init_db()

app = FastAPI(
    title="大连金普新区学区地图 API",
    description="学区管理和地图展示 API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schools.router, prefix="/api")
app.include_router(districts.router, prefix="/api")
app.include_router(communities.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "大连金普新区学区地图 API", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}
