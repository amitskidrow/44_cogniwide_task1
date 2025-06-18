# PRD — AI Voice Agent System (PoC-1)

## 1 ▪ Purpose & Background
Build a proof-of-concept voice assistant that can handle both **outbound** and **inbound** customer calls, automate common support actions, and log structured data for downstream systems. The PoC will validate technical feasibility, UX quality, and operating costs before a full production rollout. :contentReference[oaicite:0]{index=0}

## 2 ▪ Goals & Success Metrics
| Goal | KPI / Acceptance Criteria |
|------|---------------------------|
| Demonstrate bidirectional calling | • Outbound call placed & heard on real phone number<br>• Inbound call answered by AI |
| Accurate speech processing | ≥ 90 % phrase-level STT accuracy in English (stretch: Hindi, Tamil) |
| Intent extraction | Correct top-3 intent classification ≥ 85 % on test set |
| Rapid prototyping | End-to-end call flow < 3 s latency round-trip |
| DevEx | One-command local setup with Docker |

## 3 ▪ Scope
### In-Scope
* Outbound call initiation, TTS prompt, STT transcription, intent extraction, logging. :contentReference[oaicite:1]{index=1}  
* Inbound call reception, STT, ticket creation or live-agent hand-off simulation. :contentReference[oaicite:2]{index=2}  
* FastAPI backend, SQLite/PostgreSQL persistence, webhook handling, basic OpenAI prompt logic.  
* Single-language baseline: English (extendable to Hindi & Tamil).  
* Minimal Swagger UI for manual QA.

### Out-of-Scope
* Full production contact-center routing
* Third-party CRM integration (stub only)
* Mobile/desktop frontend UI (beyond Swagger)
* PoC-2 multi-agent chat system

## 4 ▪ User Personas
| Persona | Needs | Pain Points Addressed |
|---------|-------|-----------------------|
| Support Lead | Reduce live-agent load | Long wait times, staffing costs |
| End Customer | Quick issue resolution | Hold music, repeating info |
| DevOps / QA | Simple deploy & logs | Complex telephony stack |

## 5 ▪ Functional Requirements
1. **Outbound Calls**  
   a. Triggered via `/call/outbound` API with phone, prompt template, metadata.  
   b. TTS (ElevenLabs or equivalent) asks follow-up questions.  
   c. STT (Deepgram/Whisper) transcribes responses in real time.  
   d. Conversation logged; intent tags: `SCHEDULE_CALLBACK`, `RESOLVE_ISSUE`, `OTHER`. :contentReference[oaicite:3]{index=3}  

2. **Inbound Calls**  
   a. Twilio/Vapi webhook hits `/call/inbound` on ring.  
   b. STT parses complaint/inquiry.  
   c. If intent ≠ `LIVE_AGENT`, create ticket row; else route to `LiveAgentSimulator`.  
   d. Store transcript, caller ID, time stamps, intent. :contentReference[oaicite:4]{index=4}  

3. **Conversation Storage**  
   * Table: `conversations` (id, caller_number, direction, start_ts, end_ts, raw_transcript, intents JSON, status).  
   * Table: `tickets` (id, conversation_id, status, category, created_ts, resolved_ts).  

4. **Language Extension (Optional)**  
   * Modular locale layer; TTS/STT provider must accept locale code.  

## 6 ▪ Non-Functional Requirements
* **Performance** — ≤ 200 ms internal processing per STT chunk.  
* **Scalability** — Design for 5 concurrent calls (PoC target); path to 50+.  
* **Reliability** — Auto-retry outbound call once on failure; idempotent webhooks.  
* **Security & Compliance** — Env-based secret management, GDPR-style data deletion script, TLS for webhooks.  
* **Observability** — Structured logs, Prometheus metrics, span tracing via OpenTelemetry.

## 7 ▪ Technical Architecture
```

Twilio/Vapi ─┐          Outbound scheduler
│                │
▼                ▼
FastAPI app  ←──── REST/CLI trigger
│
┌────────────┴────────────┐
│  CallController (async) │
│  ├─ TTSClient           │
│  ├─ STTStreamListener   │
│  ├─ IntentExtractor     │
│  └─ TicketService       │
└────────────┬────────────┘
▼
PostgreSQL / SQLite

````

| Component | Key Tech |
|-----------|----------|
| Telephony | Twilio Programmable Voice **or** Vapi |
| STT       | OpenAI Whisper v3 or Deepgram API |
| TTS       | ElevenLabs v2 or Twilio TTS |
| LLM       | OpenAI Chat-Completion (gpt-4o-mini) |
| Backend   | Python 3.11, FastAPI, Uvicorn, AsyncIO |
| Storage   | SQLite (local) → PostgreSQL (cloud) |
| Infra     | Docker Compose; optional Render deploy |

## 8 ▪ API Endpoints (draft)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/call/outbound` | Kick off outbound call |
| POST | `/webhook/twilio` | Handle inbound Twilio events |
| POST | `/webhook/vapi` | Handle inbound Vapi events |
| GET  | `/conversation/{id}` | Fetch transcript & intents |
| GET  | `/health` | Liveness/readiness probe |

## 9 ▪ Data Schema (simplified)
```sql
CREATE TABLE conversations (
  id SERIAL PRIMARY KEY,
  phone VARCHAR(20),
  direction ENUM('INBOUND','OUTBOUND'),
  start_ts TIMESTAMP,
  end_ts TIMESTAMP,
  transcript TEXT,
  intents JSONB,
  status ENUM('OPEN','CLOSED') DEFAULT 'OPEN'
);

CREATE TABLE tickets (
  id SERIAL PRIMARY KEY,
  conversation_id INT REFERENCES conversations(id),
  category VARCHAR(100),
  status ENUM('OPEN','RESOLVED','ESCALATED') DEFAULT 'OPEN',
  created_ts TIMESTAMP,
  resolved_ts TIMESTAMP
);
````

## 10 ▪ Milestones & Timeline (aggressive 3-week PoC)

| Week | Deliverable                                           |
| ---- | ----------------------------------------------------- |
| 1    | Telephony hookup, outbound MVP, DB scaffold           |
| 2    | Inbound flow, intent extraction, logging dashboard    |
| 3    | Multi-language toggle, Dockerfile, README, demo video |

## 11 ▪ Risks & Mitigations

| Risk                       | Impact               | Mitigation                                    |
| -------------------------- | -------------------- | --------------------------------------------- |
| STT accuracy in noisy call | Mis-routed intents   | Add post-processing, confidence threshold     |
| API rate limits / cost     | Service interruption | Cache TTS, compress audio payloads            |
| GDPR/PDP compliance        | Legal                | Flag/delete PII on request; encrypted at rest |

## 12 ▪ Open Questions

1. Target daily call volume & concurrency?
2. Preferred telephony provider (Twilio vs Vapi) and account availability?
3. Any compliance constraints beyond GDPR (e.g., PCI, HIPAA)?
4. Required languages for PoC phase or can we defer to pilot?
5. Should we integrate with an existing ticketing system (e.g., Zendesk) or keep local DB?

---

*Prepared by: \[Your Name]*
*Date: 18 June 2025 (IST)*
