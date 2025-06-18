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

In addition to the database settings, the app relies on several provider specific variables:

- `OPENAI_API_KEY` – API key used for Whisper STT and chat completions.
- `OPENAI_WHISPER_MODEL` – (optional) Whisper model name, defaults to `whisper-1`.
- `DEEPGRAM_API_KEY` – API key for Deepgram STT (if `STT_PROVIDER=deepgram`).
- `DEEPGRAM_MODEL` – (optional) Deepgram transcription model.
- `ELEVEN_API_KEY` – ElevenLabs TTS key.
- `ELEVEN_VOICE_ID` – (optional) voice ID to synthesize, defaults to `default`.
- `ELEVEN_MODEL_ID` – (optional) TTS model name.
- `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` – credentials for Twilio/Vapi integrations.
- `TWILIO_TTS_VOICE` – (optional) voice name when using Twilio TTS.
- `TTS_PROVIDER` – choose between `elevenlabs` or `twilio`.
- `STT_PROVIDER` – choose between `openai` or `deepgram`.
- `DATABASE_URL` – alternative SQLAlchemy connection string.

An example configuration is provided in [`.env.example`](./.env.example). Copy it to `.env` and fill in your secrets before launching the stack.

## Project structure
```
├── app
│   └── main.py        # FastAPI application
├── Dockerfile         # Image definition for the API service
├── docker-compose.yml # Multi-service configuration
├── requirements.txt   # Python dependencies
└── PRD.md             # Product requirements
```

## API endpoints

The service exposes a small set of REST endpoints. When running locally via Docker Compose they are available at `http://localhost:8000`.

- `POST /call/outbound` – initiate an outbound call. Body parameters:
  - `phone_number` – destination phone number.
  - `prompt` – text prompt to speak when the call starts.
  - `metadata` – optional JSON object stored with the conversation.

- `POST /call/inbound` – webhook receiver for Twilio/Vapi events. Send the incoming event payload as `{ "event": { ... } }`.

You can experiment with these endpoints using the interactive Swagger UI at `/docs`.
