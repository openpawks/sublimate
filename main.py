import uvicorn
from src.backend.app import app
from src.config import settings


def main():
    uvicorn.run(app, **settings.get("uvicorn"))


if __name__ == "__main__":
    main()
