# CommunityPulse

**the game Community Intelligence Platform**

CommunityPulse aggregates sentiment and trends across multiple platforms to help gaming players and content creators understand what the community is talking about - without manually browsing Reddit, Twitter, Discord, and YouTube.

---

## The Problem

Players spend **2-4 hours weekly** manually browsing fragmented platforms to understand:
- How does the community feel about the latest patch?
- What's trending right now?
- What are people upset or excited about?

Existing tools (TierSite, , ) focus on **stats**, not **sentiment**. Enterprise social listening tools exist but cost $500+/month.

## The Solution

CommunityPulse provides:

- **State of the Game** - Overall community mood (1-10) with AI-generated summary
- **Top 3 Good / Top 3 Bad** - What's working and what needs improvement, with explanations of *why*
- **Trend Detection** - What's blowing up right now
- **Cross-Platform Aggregation** - Reddit, YouTube, OfficialNews, TierSite, , Google Trends

```
┌─────────────────────────────────────────────────────┐
│  STATE OF THE GAME                                  │
│                                                     │
│  😐 6.2/10 - "Cautiously optimistic"               │
│                                                     │
│  👍 What's Working                                  │
│  • Skarner rework - "Finally feels like a champ"   │
│  • Arena mode - "Best casual mode in years"        │
│                                                     │
│  👎 Needs Improvement                               │
│  • Matchmaking - "Plat players in Bronze lobbies"  │
│  • Vanguard - "Linux players locked out"           │
└─────────────────────────────────────────────────────┘
```

---

## Project Status

**Phase:** MVP1 Planning Complete - Ready for Implementation

| Document | Description |
|----------|-------------|
| [MVP1 Design](docs/claude-brainstorm/MVP1-DESIGN.md) | Full technical specification |
| [Master PRD](docs/claude-brainstorm/MASTER-PRD.md) | Consolidated product requirements |
| [Implementation Plan](docs/claude-brainstorm/IMPLEMENTATION-PLAN.md) | Step-by-step build guide |
| [Session Notes](docs/claude-brainstorm/SESSION-NOTES.md) | Planning decisions and rationale |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React (Vite) |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Sentiment | VADER + TextBlob |
| AI/LLM | Gemini 1.5 Flash |
| Container | Docker + docker-compose |

---

## Quick Start

### Prerequisites

- Docker Desktop installed
- API keys for:
  - Reddit (create app at reddit.com/prefs/apps)
  - YouTube Data API (Google Cloud Console)
  - Gemini (Google AI Studio)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/gaming-community-analytics-tracker.git
   cd gaming-community-analytics-tracker
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start the application**
   ```bash
   docker-compose up
   ```

4. **Access the dashboard**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## Data Sources

### MVP1 Sources

| Source | Data |
|--------|------|
| Reddit | r/gamecommunity posts + comments |
| YouTube | the game creator videos + comments |
| OfficialNews Official | Patch notes, news |
| TierSite | Tier lists, trending builds |
|  | Meta reports, guides |
| Google Trends | Search interest data |

### MVP2+ (Planned)

- Twitter/X
- Twitch
- Discord
- News aggregators

---

## Project Structure

```
gaming-community-analytics-tracker/
├── backend/                    # FastAPI backend
│   ├── api/routes/            # API endpoints
│   ├── services/              # Business logic
│   │   ├── fetchers/          # Data source clients
│   │   ├── sentiment.py       # VADER analysis
│   │   └── llm.py             # Gemini integration
│   └── models/                # SQLAlchemy models
├── frontend/                   # React frontend
│   └── src/components/        # Dashboard components
├── docs/
│   └── claude-brainstorm/     # Planning documents
├── Main Strategy Docs/         # Original research (3 LLM iterations)
├── UI Examples/                # Design references
└── docker-compose.yml
```

---

## Features

### MVP1 (Current)

- [x] Manual data fetch trigger
- [x] Cross-platform aggregation (6 sources)
- [x] VADER sentiment analysis
- [x] Gemini AI summaries with fallback
- [x] State of the Game dashboard
- [x] Top mentions feed
- [x] Topic cloud
- [x] Error handling & graceful degradation

### MVP2 (Planned)

- [ ] Scheduled polling (hourly)
- [ ] Twitter/X integration
- [ ] User accounts
- [ ] Alerts & notifications
- [ ] Mobile responsive

---

## API Endpoints

```
POST /api/fetch/all           # Trigger data collection
GET  /api/dashboard/state     # State of the game
GET  /api/dashboard/sentiment # Sentiment breakdown
GET  /api/posts               # Recent posts
POST /api/posts/{id}/summarize # AI summary for post
GET  /api/keywords            # Trending keywords
```

Full API documentation available at `/docs` when running.

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDDIT_CLIENT_ID` | Reddit API client ID | Yes |
| `REDDIT_CLIENT_SECRET` | Reddit API secret | Yes |
| `REDDIT_USER_AGENT` | Reddit API user agent | Yes |
| `YOUTUBE_API_KEY` | YouTube Data API key | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |

---

## Security

This project follows security best practices. See [Vibe Code Security Guide](security-notes/Vibe%20Code%20Security%20Guide.md) for details.

Key measures:
- All API keys in environment variables (never committed)
- SQLAlchemy ORM (SQL injection prevention)
- Pydantic validation on all inputs
- CORS restricted to frontend origin
- Error responses don't leak stack traces

---

## Contributing

This project is in active development. See [Implementation Plan](docs/claude-brainstorm/IMPLEMENTATION-PLAN.md) for current tasks.

---

## Research Background

This project was planned through three iterations of AI-assisted research:

1. **ChatGPT** - Market research, competitive analysis
2. **Gemini** - Smart polling architecture, cost optimization
3. **Claude Code** - Technical design, implementation planning

See `Main Strategy Docs/` for original research documents.

---

## License

MIT License - See LICENSE file for details.

---

## Acknowledgments

- UI design inspired by [DashboardStyleA](https://dashboard-style-a.com) social listening dashboard
- Sentiment analysis powered by [VADER](https://github.com/cjhutto/vaderSentiment)
- AI summaries by Google Gemini

---

*CommunityPulse - Know what's trending in the game, instantly.*
