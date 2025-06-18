# Voice Agent PoC

This repository contains a minimal FastAPI application and a `docker-compose.yml` configuration that starts both the API service and a PostgreSQL database. It is intended as a starting point for the PoC described in `PRD.md`.

## Requirements
- [Docker](https://docs.docker.com/get-docker/) with Compose plugin

## Running the app
Run the following command from the project root:

```bash
docker compose up --build
```

For local development without Docker, run:

```bash
uvicorn app.main:app --reload
```

The API will be available at [http://localhost:8000](http://localhost:8000). Swagger UI can be accessed at [http://localhost:8000/docs](http://localhost:8000/docs).

The database data is stored in the `db_data` Docker volume declared in `docker-compose.yml`.

## Environment variables
The web service reads the following environment variables to connect to the database:

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

Additional variables are required when using the telephony features:

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`
- `OPENAI_API_KEY` (for `IntentClassifier` and Whisper STT)
- `DEEPGRAM_API_KEY` (if using Deepgram STT)
- `ELEVEN_API_KEY` (for ElevenLabs TTS)

Default values are provided in `docker-compose.yml`, but you can override them using a `.env` file or by exporting them before running Compose.

## Project structure
```
├── app
│   └── main.py        # FastAPI application
├── Dockerfile         # Image definition for the API service
├── docker-compose.yml # Multi-service configuration
├── requirements.txt   # Python dependencies
└── PRD.md             # Product requirements
```
