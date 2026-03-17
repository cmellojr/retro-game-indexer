# Roadmap

Evolution plan for retro-game-indexer, from current audio-based detection toward a multi-modal game indexing platform.

---

## Completed

### v0.1 — Core Pipeline
- [x] Download audio from YouTube via yt-dlp
- [x] Transcribe with faster-whisper (cached)
- [x] Detect game names with GLiNER zero-shot NER
- [x] CLI with `analyze` command
- [x] Whisper hints for domain vocabulary

### v0.2 — Channel Support & Calibration
- [x] `list` command — browse channel videos/lives
- [x] `channel` command — batch analyze multiple videos
- [x] Maintenance pipeline (tools, components, mods)
- [x] `config.toml` calibration — threshold, blocklist, aliases
- [x] Timestamped YouTube links (`-l` flag)
- [x] Caching system (audio + transcripts)
- [x] Progress bar for transcription

### v0.3 — Persistence & Validation
- [x] SQLite database for video metadata and detections
- [x] `search` command — query across all analyzed videos
- [x] `history` command — list analyzed videos
- [x] Validation layer — fuzzy match against known datasets
- [x] JSON datasets (known_titles, stopwords, consoles, hints, aliases)
- [x] Configurable model parameters (GPU support via config.toml)
- [x] HuggingFace token support (.env)

---

## Planned

### v0.4 — Dataset Expansion & Calibration Refinement
- [ ] Expand `known_titles.json` with comprehensive retro game lists (SNES, Mega Drive, NES, Game Boy, N64, PS1, Saturn, etc.)
- [ ] IGDB API integration — auto-populate known titles from the Internet Game Database
- [ ] Improve alias matching — handle multi-word fragments from GLiNER (e.g., long Japanese titles split into pieces)
- [ ] Blocklist suggestions — detect recurring false positives across runs and suggest additions
- [ ] Export results — CSV/JSON export for analysis in external tools

### v0.5 — Visual Game Detection
- [ ] Frame extraction from video using PySceneDetect (keyframe sampling at scene changes)
- [ ] OpenCLIP ViT-B-32 integration — compute frame embeddings locally (CPU/GPU)
- [ ] Reference screenshot database — scrape from IGDB/ScreenScraper.fr, embed with CLIP
- [ ] FAISS vector index — cosine similarity search against reference database
- [ ] `pipelines/visual/detector.py` — VisualDetector following the existing Detector pattern
- [ ] Merge audio + visual detections — corroborate game mentions across modalities
- [ ] Visual pipeline calibration in `config.toml`
- [ ] Optional perceptual hashing (pHash) as fast pre-filter

### v0.6 — Data Layers & Knowledge Base
- [ ] Reorganize data storage: `data/raw/` (audio), `data/processed/` (transcripts, embeddings), `data/knowledge/` (validated entities)
- [ ] Structured knowledge graph — games → videos → timestamps with confidence scores
- [ ] Cross-video analytics — most mentioned games, detection trends over time
- [ ] Dashboard or web UI for browsing indexed content

### v0.7 — RAG & Natural Language Queries
- [ ] Embed transcript segments with a text embedding model
- [ ] Vector index for transcript chunks (ChromaDB or FAISS)
- [ ] Natural language query interface: "Which videos mention Castlevania?"
- [ ] LLM-powered answer generation grounded in indexed data
- [ ] Semantic search across video content (not just entity names)

---

## Ideas (not prioritized)

- **OCR on gameplay** — read text from title screens, menus, and in-game text using Tesseract or EasyOCR
- **Audio fingerprinting** — identify games by soundtrack/sound effects (Dejavu, Chromaprint)
- **Multi-language support** — extend beyond Brazilian Portuguese
- **Plugin system** — custom pipelines for other content types (music, movies, hardware)
- **Real-time analysis** — process live streams as they happen
- **Community datasets** — shared known_titles.json curated by the community
- **IGDB enrichment** — auto-fetch game metadata (year, platform, genre) for detected titles
- **Confidence fusion** — combine audio + visual + OCR scores for higher accuracy
