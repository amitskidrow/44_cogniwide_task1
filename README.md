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

## Locale configuration
The application uses a configurable default locale for speech services. The
current value is stored in `app/config.json` and can be retrieved or updated via
the `/config/locale` API endpoints.

## Inbound call processing
Recorded inbound calls can be submitted to `/call/inbound` with a JSON payload
containing the caller phone number and a URL to the audio recording. The service
will transcribe the audio, classify the intent and create a ticket when
appropriate.

## Environment variables
The web service reads the following environment variables to connect to the database:

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

For telephony integration the following Twilio credentials are required:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_CALLER_ID`
- `TWILIO_STREAM_URL` (optional)

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

## Deleting records
You can remove stored conversations or tickets using the management script. It
uses the same `DATABASE_URL` environment variable as the web service.

```bash
python scripts/manage.py delete-conversation <conversation_id>
python scripts/manage.py delete-ticket <ticket_id>
```

Replace the placeholders with the numeric IDs to delete.

## TLS for webhook endpoints

Webhook requests can be served over HTTPS by running Uvicorn with a certificate.
Generate a self‑signed certificate using the helper script:

```bash
scripts/generate_self_signed_cert.sh
```

Start the app with SSL enabled:

```bash
uvicorn app.main:app \
    --host 0.0.0.0 --port 8443 \
    --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
```

## Monitoring dashboard

`docker-compose.yml` includes Prometheus and Grafana services. Once the stack is
running, Prometheus scrapes metrics from the API and Grafana is available at
[http://localhost:3000](http://localhost:3000) (default credentials admin/admin)
to visualize them.
