# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ideas Generator is an automated business opportunity generator that monitors Reddit communities, analyzes discussions using Google Gemini AI to detect pain points and emerging trends, and produces daily email reports and podcast episodes.

## Architecture

This project follows a **3-layer architecture**:

1. **Directive Layer (`directives/`)**: SOP documents in Markdown defining *what* to do
2. **Orchestration Layer**: The AI agent (you) reads directives and calls execution tools in the correct order
3. **Execution Layer (`execution/`)**: Deterministic Python scripts that do the actual work

**Key principle**: Don't do the work yourself - read the directive, then execute the corresponding script. This reduces error accumulation (90% accuracy per step = 59% success over 5 steps).

## Common Commands

All commands run from `execution/reddit_analyzer/`:

```bash
cd execution/reddit_analyzer

# Data collection
uv run collector.py

# Analysis (requires GOOGLE_API_KEY)
uv run analyze_ideas.py --category "B2B_MARKET"

# Email report (requires Google Service Account)
uv run send_email.py --category "B2B_MARKET"

# Podcast generation pipeline
uv run generate_podcast_script.py --category "B2B_MARKET"
uv run semantic_segmentation.py --script "scripts/podcast_script_B2B_MARKET_YYYYMMDD.json"
uv run synthesize_podcast_audio.py --segments "segments_B2B_MARKET_YYYYMMDD.json"
uv run audio_postproduction.py --raw-audio "audio/raw/" --output "episodes/"
```

## Environment Setup

Copy `.env.example` to `.env` and configure the required variables.

### Required Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Google AI Studio API key for Gemini ([get here](https://makersuite.google.com/app/apikey)) |
| `GOOGLE_MODEL` | Gemini model to use (default: `gemini-3-flash-preview`) |
| `OPENAI_API_KEY` | OpenAI API key for TTS podcast generation ([get here](https://platform.openai.com/api-keys)) |
| `OPENAI_TEXT_MODEL` | OpenAI model for text generation (default: `gpt-4`) |
| `RECIPIENT_EMAIL` | Email destination for reports |

### Google Workspace APIs (Gmail, Drive, Sheets)

| Variable | Description |
|----------|-------------|
| `GOOGLE_SERVICE_ACCOUNT_PATH` | Path to service account JSON (default: `execution/reddit_analyzer/secrets/service_account.json`) |
| `GOOGLE_SCOPES` | Required OAuth scopes (Drive, Gmail, Sheets) |

### Optional Variables

See `.env.example` for the full list, including:
- **Cost Management**: `MAX_MONTHLY_COST_USD`, `MAX_EPISODES_PER_DAY`
- **Audio Settings**: `AUDIO_FORMAT`, `AUDIO_BITRATE`, `TTS_MODEL`, voice configurations
- **Feature Flags**: `ENABLE_PODCAST_GENERATION`, `ENABLE_MULTI_SPEAKER`, etc.
- **Alternative TTS**: ElevenLabs, Azure Cognitive Services, AWS Polly
- **Rate Limiting**: `REDDIT_RATE_LIMIT_DELAY`, `GEMINI_RATE_LIMIT_DELAY`

## Configuration

- `execution/reddit_analyzer/config.json` - Subreddit sources and categories
- `execution/reddit_analyzer/podcast_config_advanced.json` - TTS voices, audio settings, multi-speaker configuration

Categories are extracted from `config.json` and processed in parallel by GitHub Actions.

## CI/CD

GitHub Actions workflow (`.github/workflows/daily_ideas.yml`) runs daily at 08:00 UTC:
1. Collects Reddit data (single job)
2. Analyzes and reports per category (matrix strategy, parallel)
3. Generates podcast episodes per category
4. Commits updated database

## Self-Repair Protocol

When errors occur:
1. Read the error message and stack trace
2. Fix the script (check with user before retrying if it uses paid API credits)
3. Update the directive with lessons learned (API limits, edge cases)
4. Never create or overwrite directives without asking first

## Key Files

- `execution/reddit_analyzer/reddit_ideas.db` - SQLite database of collected posts
- `latest_analysis_*.md` - Generated analysis reports per category
- `scripts/` - Generated podcast JSON scripts
- `episodes/` - Final MP3 podcast files
- `.tmp/` - Intermediate files (can be deleted, never commit)
