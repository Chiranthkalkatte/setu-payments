from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.session import engine, Base
from app.api.routes import events, transactions, reconciliation


@asynccontextmanager
async def lifespan(app:FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title= 'setu payment backend', vesion = '1.0', lifespan = lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/health', tags=["health"])
async def health_check():
    return {"status": "Success", "version": "1.0.0"}


app.include_router(events.router, tags=["Events"])
app.include_router(transactions.router, tags=["Transactions"])
app.include_router(reconciliation.router, tags=["Reconciliation"])