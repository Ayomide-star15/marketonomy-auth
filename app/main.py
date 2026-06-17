from fastapi import FastAPI

app = FastAPI(
    title="Marketonomy Auth API",
    description="Authentication system for Marketonomy",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "Marketonomy Auth API is running!"}