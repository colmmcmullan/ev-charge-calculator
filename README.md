# EV Charge Calculator

This is a simple Flask application for calculating electric vehicle charging needs.

## Running with Docker

The easiest way to run the application is using Docker Compose:

```bash
docker compose up --build
```

The app will be available at `http://localhost:5001/`

## Running Locally (without Docker)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
python app.py
```

The app will be available at `http://127.0.0.1:5001/`
