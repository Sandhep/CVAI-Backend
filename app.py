from fastapi import FastAPI  # type: ignore

app = FastAPI()

@app.get('/')
async def read_root():
    return {"message":"Testing FastAPI"}

@app.get('/home')
async def home_root():
    return {"message":"Home route"}