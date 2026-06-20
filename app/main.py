from fastapi import FastAPI
from app.db.database import engine
from app.api.v1.endpoints import auth, password, token

app = FastAPI(
    title="Marketonomy Auth API",
    description="Authentication system for Marketonomy",
    version="1.0.0"
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(password.router, prefix="/api/v1")
app.include_router(token.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Marketonomy Auth API is running!"}
@app.get("/test db")
def test_db():
    try:
        connection = engine.connect()
        connection.close()
        return {"status": "success", "message": "Database connected successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}