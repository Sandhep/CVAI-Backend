from fastapi import FastAPI

from repository.firebase.Firebase import Firebase

from controller import HttpController

from fastapi.middleware.cors import CORSMiddleware

from service.LLMScore  import LLMScore

Firebase.initialize()

LLMScore.initialiseModel()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(HttpController.router)

