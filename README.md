# LedgerForge - FastAPI Project

## Run this project in 10 steps

1. Install Python 3.11 or newer.
2. Install Git and Visual Studio Code.
3. Clone or download the project.
4. Open the project folder in VS Code.
5. Create a virtual environment using `python -m venv .venv`.
6. Activate it using `.venv\Scripts\activate` on Windows.
7. Install dependencies using `pip install -r requirements.txt`.
8. Copy `.env.example` to `.env` and configure the settings if required.
9. Run `python -m scripts.seed_example`.
10. Start the API using `uvicorn app.main:app --reload`.

## Test the API

Open http://127.0.0.1:8000/docs

Try the `GET /departments` endpoint.

## Run tests

```bash
python -m pytest