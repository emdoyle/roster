import uvicorn
from fastapi import FastAPI


def main():
    app = FastAPI(title="Roster Agent", version="0.1.0")
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
