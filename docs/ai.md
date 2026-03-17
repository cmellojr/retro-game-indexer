# AI Technologies

This project uses two AI models running locally. No cloud APIs required. Defaults to CPU; GPU is supported via `config.toml`.

## Whisper (Speech-to-Text)

**Library:** [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2 backend)
**Model:** `base` (74M parameters)
**Quantization:** INT8 (runs on CPU with ~1.5 GB RAM)

### What it does

Whisper is an automatic speech recognition (ASR) model developed by OpenAI. It converts audio into text, producing timestamped segments:

```
[1.5s]  "hoje vamos falar sobre o Super Mario World"
[4.2s]  "um dos melhores jogos do Super Nintendo"
```

### Key concepts

- **ASR (Automatic Speech Recognition)**: the task of converting spoken audio into written text. Whisper handles this end-to-end: raw audio in, text out.

- **Encoder-decoder transformer**: Whisper's architecture. The encoder processes a mel spectrogram (visual representation of audio frequencies) and the decoder generates text tokens autoregressively (one token at a time, each conditioned on previous tokens).

- **Multilingual model**: trained on 680,000 hours of audio in 99 languages. The videos in this project are in Brazilian Portuguese; Whisper handles this natively.

- **Initial prompt (hints)**: a text string provided before transcription starts, injected into the decoder context. This biases the model toward specific vocabulary. For example, passing "Super Mario World, Castlevania, Mega Man" increases the chance of correct transcription of these game names instead of phonetically similar but wrong words.

- **INT8 quantization**: the model weights are stored as 8-bit integers instead of 32-bit floats. This reduces memory by ~4x and speeds up inference on CPU with minimal quality loss.

- **CTranslate2**: an inference engine optimized for transformer models. faster-whisper uses it to run Whisper 4x faster than the original OpenAI implementation with less memory.

### How it's used in this project

```
audio.mp3 → Whisper (base, INT8, CPU) → [{"text": "...", "start": 1.5}, ...]
```

The `initial_prompt` parameter receives domain-specific hints (game titles or maintenance terms) to improve transcription accuracy for technical vocabulary.

---

## GLiNER (Named Entity Recognition)

**Library:** [GLiNER](https://github.com/urchade/GLiNER)
**Model:** `urchade/gliner_base`

### What it does

GLiNER detects named entities in text given a set of labels. Unlike traditional NER models that are trained on fixed entity types (person, organization, location), GLiNER is **zero-shot**: you provide arbitrary labels at inference time.

```python
# Input
text = "hoje vamos falar sobre o Super Mario World"
labels = ["video game"]

# Output
[{"text": "Super Mario World", "label": "video game", "score": 0.95}]
```

### Key concepts

- **NER (Named Entity Recognition)**: the task of identifying and classifying named entities (proper nouns, specific items) in text. Given "I played Zelda on the SNES", NER would extract "Zelda" as a video game and "SNES" as a console.

- **Zero-shot NER**: the ability to recognize entity types never seen during training. Traditional NER requires training data for each entity type; GLiNER generalizes from its pre-training. You just pass the label strings you want and it finds matching spans in the text.

- **Span-based extraction**: GLiNER scores every possible text span (contiguous substring) against each label. The spans with scores above the confidence threshold are returned as entities. This is different from token classification approaches (like BERT-NER) that label individual tokens.

- **Confidence threshold**: a cutoff score (0.0-1.0) below which detections are discarded. Higher threshold = fewer results but higher precision. Lower threshold = more results but more noise. Default: 0.7 for games, 0.6 for maintenance.

- **Bi-encoder architecture**: GLiNER encodes entity labels and text spans separately, then computes similarity. This allows efficient inference with arbitrary label sets without retraining.

### How it's used in this project

Two detection pipelines use the same GLiNER model with different labels:

| Pipeline | Labels | Threshold |
|----------|--------|-----------|
| Games | `"video game"` | 0.7 |
| Maintenance | `"repair tool"`, `"electronic component"`, `"hardware modification"` | 0.6 |

```
transcribed segments → GLiNER (zero-shot) → [{"name": "Resident Evil", "category": "video game", "timestamp": 448.6, "confidence": 0.95}]
```

Post-processing applies:
1. **Stopword filtering** — removes generic terms ("jogo", "game", "super")
2. **Console filtering** — removes console names ("playstation", "snes")
3. **User blocklist** — removes terms from `config.toml`
4. **Alias normalization** — maps transcription variants to canonical names
5. **Deduplication** — keeps only the first occurrence of each entity
6. **Validation** — fuzzy-matches candidates against known datasets (`data/datasets/`), normalizes names to canonical form, and marks unmatched entities with `[?]`

---

## Processing Pipeline

```
YouTube URL
    │
    ▼
[yt-dlp] ──→ audio file (cached)
    │
    ▼
[Whisper] ──→ text segments with timestamps (cached)
    │
    ▼
[GLiNER] ──→ entity mentions with confidence scores
    │
    ▼
[Filters] ──→ cleaned results (stopwords, blocklist, aliases, dedup)
    │
    ▼
[Validator] ──→ fuzzy match against known datasets → confirmed / uncertain [?]
    │
    ▼
  Output + SQLite
```

Both the audio download and transcription steps are cached on disk (`.cache/`). The detection step always runs fresh, allowing rapid iteration on `config.toml` calibration settings.

---

## RAG (Retrieval-Augmented Generation)

RAG is not used in this project, but it's worth understanding what it is and why it doesn't apply here.

### What it is

Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval with text generation. Instead of relying solely on what a large language model (LLM) "memorized" during training, RAG first searches a knowledge base for relevant documents, then feeds those documents to the LLM as context so it can generate a grounded answer.

### How it works

```
User question
    │
    ▼
[Retriever] ──→ search a vector database or document index
    │               for relevant passages
    ▼
[Augmentation] ──→ inject retrieved passages into the LLM prompt
    │
    ▼
[Generator (LLM)] ──→ generate an answer based on the retrieved context
    │
    ▼
  Answer (grounded in real data)
```

Key components:

- **Embedding model**: converts text into numerical vectors so that semantically similar texts end up close together in vector space. Used to encode both the documents in the knowledge base and the user's query.

- **Vector database**: stores document embeddings and supports fast similarity search (e.g., FAISS, ChromaDB, Pinecone). When a query comes in, it finds the most similar documents.

- **LLM (generator)**: receives the retrieved passages as context and generates a natural language answer. Because it has the actual source text, it can cite specifics rather than hallucinating.

### Why it doesn't fit this project

This project is an **extraction pipeline**, not a question-answering system:

| | This project | RAG system |
|---|---|---|
| **Goal** | Extract structured data from audio | Answer questions using documents |
| **Input** | YouTube video URL | Natural language question |
| **Output** | List of detected entities | Natural language answer |
| **AI role** | Transcription + NER | Retrieval + generation |
| **Knowledge base** | Not needed | Core component |

The pipeline converts audio → text → entities. There is no user query, no knowledge base to search, and no text to generate. RAG solves a fundamentally different problem.

### Where RAG could fit (future)

If the project evolves to support **natural language queries over indexed data**, RAG would become relevant. For example:

```
"Which videos mention Castlevania and Mega Man?"
"What maintenance tools does the channel recommend most?"
```

In that scenario:
1. The existing pipeline would populate a knowledge base (video titles, detected entities, timestamps)
2. An embedding model would index those records
3. A user query would trigger retrieval of relevant records
4. An LLM would synthesize a natural language answer from the retrieved data

This would turn the project from a batch extraction tool into an interactive search engine over video content.

---

## Model Details

| | Whisper (base) | GLiNER (base) |
|---|---|---|
| **Parameters** | 74M | ~110M |
| **Disk size** | ~150 MB (INT8) | ~440 MB |
| **RAM usage** | ~1.5 GB | ~1 GB |
| **Device** | CPU (default) or CUDA | CPU (default) or CUDA |
| **Input** | Audio (any format) | Text + label strings |
| **Output** | Timestamped text segments | Scored entity spans |
| **Approach** | Supervised (680k hours) | Zero-shot generalization |

Device and model size are configurable in `config.toml`. See [usage.md](usage.md) for details.
