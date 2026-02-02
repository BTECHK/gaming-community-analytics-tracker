# CommunityPulse

**gaming Community Pulse & Sentiment Dashboard**

CommunityPulse aggregates sentiment and trends across multiple platforms to help gaming players and content creators understand what the community is talking about - without manually browsing Reddit, YouTube, and other platforms.

---

## Features

- **Trending Topics** - Real-time community discussion themes with sentiment analysis
- **Sentiment Breakdown** - Positive/neutral/negative distribution with confidence scores
- **Cross-Platform Aggregation** - YouTube, OfficialNews, TierSite, Google Trends data sources
- **Patch Pulse** - Current patch sentiment and highlights
- **Personal Digest** - Follow topics and get AI-generated summaries
- **Feedback System** - Vote and report on topic accuracy
- **Multi-source Quotes** - Representative quotes from community discussions

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | SvelteKit 2 + Svelte 5 (with runes) |
| Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL 15 |
| Cache | Valkey (Redis-compatible) |
| NLP | BERTopic + Sentence Transformers |
| AI Summaries | Google Gemini (optional) |
| Container | Docker + Docker Compose |

---

## Quick Start

### Prerequisites

- Docker Desktop installed and running
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/gaming-community-analytics-tracker.git
   cd gaming-community-analytics-tracker
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (see Environment Variables below)
   ```

3. **Start the application**
   ```bash
   docker compose up
   ```

4. **Seed demo data (optional)**
   ```bash
   docker compose exec backend python scripts/seed_demo_data.py
   ```

5. **Access the dashboard**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `VALKEY_URL` | Valkey/Redis connection string | Yes |
| `YOUTUBE_API_KEY` | YouTube Data API key | No (uses fallback) |
| `GEMINI_API_KEY` | Google Gemini API key for AI summaries | No (uses fallback) |

### Example `.env`:
```env
DATABASE_URL=postgresql://communitypulse:communitypulse@db:5432/communitypulse
VALKEY_URL=redis://cache:6379/0
YOUTUBE_API_KEY=your_youtube_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## Project Structure

```
gaming-community-analytics-tracker/
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── api/routes/         # API endpoints
│   │   ├── ingestion/adapters/ # Data source scrapers
│   │   ├── models/             # SQLAlchemy models
│   │   ├── nlp/                # NLP pipeline (BERTopic, sentiment)
│   │   └── services/           # Business logic
│   ├── scripts/                # Utility scripts
│   └── tests/                  # Pytest tests
├── frontend/                    # SvelteKit frontend
│   ├── src/
│   │   ├── lib/               # Components, stores, API client
│   │   │   ├── components/    # Reusable UI components
│   │   │   ├── stores/        # Svelte 5 rune stores
│   │   │   └── i18n/          # Internationalization
│   │   └── routes/            # SvelteKit pages
│   └── e2e/                   # Playwright E2E tests
├── docs/                        # Documentation
├── docker-compose.yml           # Container orchestration
└── README.md
```

---

## Development

### Running Tests

**Backend tests (requires Docker):**
```bash
docker compose exec backend pytest tests/ -v
```

**Frontend unit tests:**
```bash
cd frontend
npm run test:run
```

**Frontend E2E tests (requires frontend running):**
```bash
cd frontend
npm run test:e2e
```

### Development Commands

**Start in development mode:**
```bash
docker compose up
```

**Rebuild containers after dependency changes:**
```bash
docker compose build --no-cache
```

**View logs:**
```bash
docker compose logs -f backend
docker compose logs -f web
```

**Access backend shell:**
```bash
docker compose exec backend bash
```

---

## API Endpoints

### Dashboard
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/trending` | GET | Trending topics with sentiment |
| `/api/dashboard/topics` | GET | All topics list |
| `/api/dashboard/topics/{slug}` | GET | Single topic details |
| `/api/dashboard/sources` | GET | Source distribution |
| `/api/dashboard/patch-pulse` | GET | Current patch sentiment |
| `/api/dashboard/aggregate` | POST | Trigger aggregation |
| `/api/dashboard/digest/summary` | POST | AI digest summary |

### Feedback
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/feedback/vote` | POST | Submit vote (thumbs up/down) |
| `/api/feedback/report` | POST | Report inaccurate topic |
| `/api/feedback/general` | POST | Submit general feedback |

### Health
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check with DB/cache status |

Full API documentation available at `http://localhost:8000/docs` when running.

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  SvelteKit      │────▶│  FastAPI        │────▶│  PostgreSQL     │
│  Frontend       │     │  Backend        │     │  Database       │
│                 │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │                 │     │                 │
                        │  NLP Worker     │────▶│  Valkey Cache   │
                        │  (BERTopic)     │     │                 │
                        │                 │     │                 │
                        └─────────────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Data Sources   │
                        │  - YouTube      │
                        │  - TierSite        │
                        │  - the game publisher   │
                        │  - Google Trends│
                        └─────────────────┘
```

---

## Key Components

### NLP Pipeline
- **BERTopic** for dynamic topic discovery with seed topics
- **Sentence Transformers** for embedding generation
- **VADER** for sentiment analysis
- **Gemini API** for human-readable topic naming (optional)

### Frontend
- **Svelte 5 runes** ($state, $derived, $effect) for reactivity
- **svelte-persisted-state** for localStorage persistence
- **svelte-i18n** for internationalization (English only for MVP)
- **CSS custom properties** for theming

### Backend
- **Async SQLAlchemy** for database operations
- **Pydantic** for request/response validation
- **Background workers** for NLP processing
- **Dead letter queue** for failed job handling

---

## Security

- All API keys in environment variables (never committed)
- SQLAlchemy ORM (SQL injection prevention)
- Pydantic validation on all inputs
- CORS restricted to frontend origin
- Error responses don't leak stack traces
- Session IDs for anonymous feedback tracking

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License - See LICENSE file for details.

---

*CommunityPulse - Know what the game community is talking about, instantly.*
