<!--
- Primary keyword: multimodal rag   (390/mo · KD 33); secondary: video rag (90/mo · KD 37)
- SEO title (<=60 chars): Multimodal RAG Tutorial: Build Video RAG for AI Agents
- URL slug: video-rag-tutorial
- Meta description (150–160 chars): A hands-on multimodal RAG tutorial: index scenes and speech, retrieve playable video moments, and feed timestamped citations back into your LLM answers.
- Eyebrow: Developer guide
- Read time: 9 min read
- CTA stage: docs
-->

# Video RAG: a hands-on tutorial

*For engineers who have shipped text RAG and now face a corpus that talks and moves — build retrieval that returns the moment, not the chunk.*

You build video RAG the same way you build text RAG — index, embed, retrieve, generate — except the retrieval unit is a timestamped video moment instead of a text chunk, and the index covers what was *shown* as well as what was *said*. **Multimodal RAG** over video means an agent can answer "how did the demo fail?" with a grounded paragraph *and* the 30-second clip that proves it. This tutorial builds that pipeline end to end: upload a corpus, index scenes and speech, retrieve playable moments, and feed them into an LLM answer with citations back to timestamps.

## Why isn't text RAG over transcripts enough?

The naive approach — run Whisper, chunk the transcripts, embed into a vector store, retrieve as text — works exactly until the answer was never spoken. Retrieval-augmented generation combines a parametric model with non-parametric retrieval memory ([Lewis et al., 2020](https://arxiv.org/abs/2005.11401)); the quality ceiling is whatever the retrieval memory contains. A transcript-only memory silently discards the visual channel:

- **Unspoken evidence vanishes.** The error dialog in a screen recording, the whiteboard sketch, the chart on a slide — none of it is in the transcript. A speech model like Whisper transcribes speech ([github.com/openai/whisper](https://github.com/openai/whisper)); it does not watch.
- **Chunks lose time.** Standard text chunking breaks the mapping back to timestamps, so even correct retrieval cannot yield a playable citation.
- **Answers are unverifiable.** Text RAG cites a passage; the user can read it. Transcript-RAG cites a passage from an hour-long video; the user cannot practically verify it without the moment itself.

| Dimension | Text RAG over transcripts | Video RAG (this tutorial) |
|---|---|---|
| Retrieval unit | Text chunk | Timestamped moment (start, end) |
| Visual channel | Lost | Scene index, searchable |
| Citation | Passage string | Playable clip URL + timestamp |
| Stack | Whisper + chunker + vector DB + store + glue | One API |
| Freshness | Re-chunk, re-embed pipeline | Re-index a layer |

Video RAG fixes this by treating the moment as the unit of retrieval — the data model at the center of [video infrastructure for AI agents ↗][internal-hub]. For the concept-level treatment, see [what is video RAG ↗][internal-what-is-rag]; this page is the build.

**Prerequisites:** Python 3.8+, a VideoDB API key (free tier), an LLM API key of your choice, a handful of corpus videos (talks, meetings, screen recordings), and `pip install videodb`.

> **The retrieval layer is four calls.** Everything RAG-specific in this tutorial is standard SDK surface. [Read the docs →][cta]

## How do you build video RAG? Six steps

### Step 1 — Upload the corpus

```python
import videodb

conn = videodb.connect()
coll = conn.get_collection()

urls = [
    "https://example.com/all-hands-june.mp4",
    "https://example.com/product-demo-v2.mp4",
    "https://www.youtube.com/watch?v=example",
]
videos = [coll.upload(url=u) for u in urls]
```

One collection is one retrieval scope. Per-user or per-workspace corpora should be separate collections so retrieval boundaries match permission boundaries.

### Step 2 — Index speech and scenes

Two additive layers over the same media — this is the "multimodal" in multimodal RAG:

```python
for video in videos:
    video.index_spoken_words()      # what was said
    video.index_scenes(
        prompt=(
            "Describe the scene: on-screen text, UI state, "
            "charts, people, and actions."
        )
    )
```

The scene prompt is your retrieval vocabulary — write it for the questions you expect. Indexes are built once and persist; embeddings for semantic search are part of the index layer, so there is no separate vector database to provision or sync ([VideoDB docs](https://docs.videodb.io)). The model behind scene indexing is pluggable (Twelve Labs, Gemini, OpenAI, Anthropic, or your own).

### Step 3 — Retrieve moments, not chunks

```python
question = "how did the checkout demo fail in the June review?"

spoken = coll.search(query=question,
                     index_type="spoken_word", search_type="semantic")
visual = coll.search(query=question,
                     index_type="scene", search_type="semantic")

shots = spoken.get_shots() + visual.get_shots()
```

Each shot carries `video_id`, `start`, `end`, and matched text or scene description. Searching both indexes and merging is the simplest fusion strategy; retrieval latency is on the order of ~120 ms even across petabyte-scale archives ([videodb.io](https://videodb.io)), so a two-index query costs little.

### Step 4 — Assemble the LLM context with timestamps intact

```python
def fmt(s):
    return f"[{s.video_id} @ {int(s.start)}-{int(s.end)}s] {s.text}"

context = "\n".join(fmt(s) for s in sorted(shots, key=lambda s: -s.score)[:8])

prompt = (
    "Answer using only the evidence below. Cite each claim "
    f"as [video @ seconds].\n\nEvidence:\n{context}\n\nQ: {question}"
)
answer = llm.complete(prompt)   # your LLM client here
```

The load-bearing detail is the citation format: because every evidence line carries its timestamps, the model's citations survive into the answer, and each one can be resolved back to a real moment. This is where transcript-chunk pipelines break — their chunks no longer know when they happened.

### Step 5 — Return playable citations

```python
top = max(shots, key=lambda s: s.score)
clip_url = spoken.play_stream()     # matched moments as an HLS stream

print(answer)
print("Watch the evidence:", clip_url)
```

Search results materialize as playable clips in milliseconds — the answer ships with its proof attached. In an agent setting, `{answer, moments[], clip_url}` is the tool result; the agent can quote, and the human can verify with one click.

### Step 6 — Wrap it as an agent tool

The pipeline above is a single function — `ask_corpus(question) -> answer + evidence` — which makes it a natural tool for any agent runtime, the same wiring covered in the [5-minute agent quickstart ↗][internal-quickstart]. The production reference for this exact shape is [StreamRAG](https://github.com/video-db/StreamRAG), VideoDB's open-source video retrieval and streaming agent: upload a collection, search it conversationally, and even publish it as a custom GPT. The [videodb-cookbook](https://github.com/video-db/videodb-cookbook) has the notebook variants — multimodal search, keyword search, scene-metadata retrieval.

![Bar chart comparing services required for a video RAG pipeline: a stitched stack of about 8 services versus 1 API with VideoDB](video-rag-stack-services.svg)
*A stitched video RAG stack (storage, ffmpeg, speech, vision, vectors, metadata, streaming, glue) vs. one API. Source: [videodb.io](https://videodb.io).*

> **Fork the reference, keep the architecture.** StreamRAG is the running version of this tutorial. [See the quickstart →][cta]

## What should you know before production?

**Tune fusion before touching models.** Most quality wins come from retrieval, not generation: adjust the scene prompt, rebalance spoken-vs-visual weighting per query type, and cap evidence at what the model actually uses. Only then consider swapping the indexing model.

**Re-index instead of re-ingesting.** When your taxonomy changes ("start tracking error dialogs"), add a new scene index with a new prompt over the same media. Indexes are additive layers; the corpus is uploaded once.

**Evaluate with moment-level ground truth.** Text-RAG eval habits carry over, but your gold labels should be timestamp ranges, not passages. A retrieved shot overlapping the gold range is a hit; build the harness early.

**Mind retrieval scope and retention.** Collections are your permission boundary, and memory is retention-aware — enterprise corpora (meetings, screen recordings) usually need both scoped per team and expiring on schedule.

**Live sources drop in unchanged.** Because batch and real-time are modes of one backend, the same RAG loop can run over indexed RTSP streams — RAG over yesterday's camera footage is the same four calls.

> **The unit is the moment, not the file.** Once retrieval returns moments, every downstream feature — answers, reels, alerts — is composition. [Read the docs →][cta]

## Frequently asked questions

**What is the difference between multimodal RAG and video RAG?**
Multimodal RAG is the general pattern — retrieval across text, images, audio, video. Video RAG is its hardest instance: continuous media where evidence is time-anchored and spans two channels (speech and visuals). Solve video RAG and the rest of multimodal retrieval is a subset.

**Do I need a separate vector database like Pinecone?**
No. Embedding and semantic search are part of the index layer, so there is no external vector store to provision, sync, or pay for. If you already run one for text, you can keep it for text and let video moments live where the video lives.

**Which LLM should generate the final answer?**
Any of them — the generation step in this tutorial is provider-agnostic by design. The pipeline hands your LLM timestamped evidence; GPT, Claude, and Gemini all handle the cite-from-context instruction well.

**How does this handle a corpus that grows daily?**
Uploads trigger indexing per asset; nothing global is rebuilt. That is the operational difference from chunk-and-embed pipelines, where corpus growth means re-running batch jobs and versioning an external index.

**Can the answer include an actual video clip, not just a timestamp?**
Yes — that is the defining feature. Search results resolve to playable stream URLs materialized in milliseconds, so your answer UI can embed the exact evidence moments rather than linking a full recording with a "seek to 41:32" instruction.

### Retrieval that returns the moment

Text RAG taught everyone the pattern; video breaks it only if your retrieval unit is a paragraph. Index speech and scenes as layers, retrieve timestamped moments, and let the LLM cite evidence a human can actually play. The pipeline is six steps and one API. [Read the docs →][cta]

The full working agent is open source: [StreamRAG](https://github.com/video-db/StreamRAG).

## Sources

- Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" — https://arxiv.org/abs/2005.11401
- StreamRAG, video retrieval and streaming agent (GitHub) — https://github.com/video-db/StreamRAG
- VideoDB cookbook, RAG and search notebooks (GitHub) — https://github.com/video-db/videodb-cookbook
- VideoDB documentation — https://docs.videodb.io
- VideoDB — https://videodb.io
- OpenAI Whisper (GitHub) — https://github.com/openai/whisper

[cta]: https://docs.videodb.io
[internal-hub]: /blog/what-is-video-infrastructure-for-ai-agents
[internal-what-is-rag]: /blog/what-is-video-rag
[internal-quickstart]: /blog/give-your-ai-agent-vision-in-5-minutes
