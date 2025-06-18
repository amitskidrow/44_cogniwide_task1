# Voice Agent PoC

This repository contains a minimal FastAPI application and a `docker-compose.yml` configuration that starts both the API service and a PostgreSQL database. It is intended as a starting point for the PoC described in `PRD.md`.

## Requirements
- [Docker](https://docs.docker.com/get-docker/) with Compose plugin

## Running the app
Run the following command from the project root:

```bash
docker compose up --build
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

Default values are provided in `docker-compose.yml`, but you can override them using a `.env` file or by exporting them before running Compose.
If `DATABASE_URL` is not explicitly set, it will be assembled from the variables above at runtime.

## Project structure
```
├── app
│   └── main.py        # FastAPI application
├── Dockerfile         # Image definition for the API service
├── docker-compose.yml # Multi-service configuration
├── requirements.txt   # Python dependencies
└── PRD.md             # Product requirements
```
