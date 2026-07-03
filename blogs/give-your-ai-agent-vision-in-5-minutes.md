<!--
- Primary keyword: video ai agents   (40/mo · KD 45)
- SEO title (<=60 chars): Video AI Agents: Give Your Agent Vision in 5 Minutes
- URL slug: give-your-ai-agent-vision-in-5-minutes
- Meta description (150–160 chars): Build video AI agents in minutes: pip install videodb, upload, index, and search footage through one API, with MCP and skills for any tool-calling agent.
- Eyebrow: Developer guide
- Read time: 8 min read
- CTA stage: docs
-->

# Give your AI agent vision in 5 minutes

*A working quickstart for developers who want their agent to see: upload a video, index it, and answer questions about it — before your coffee cools.*

You give an agent vision by connecting it to a video backend: `pip install videodb`, upload a file, index its speech and scenes, and your agent can query footage the way it queries a database. **Video AI agents** are ordinary tool-calling agents — Claude Code, Cursor, an n8n flow, a Zapier zap — pointed at [video infrastructure ↗][internal-hub] instead of a folder of MP4s. This guide walks the whole path in five numbered steps, with runnable code at each one. The unit you end up with is the moment, not the file.

## What will you build?

By the end of this tutorial you will have a Python script that ingests a video, builds two indexes over it (spoken words and visual scenes), and answers a natural-language question with a playable clip of the exact moment — then you will expose that capability to any agent runtime through MCP or a one-command skill install.

Concretely, the flow is: **connect → upload → index → search → hand the tool to your agent.** That is the same See → Understand → Act loop that VideoDB's own reference agents use ([VideoDB docs](https://docs.videodb.io)), and it is the smallest honest version of [agentic perception ↗][internal-agentic-perception] you can ship.

The alternative is assembling it yourself: object storage for the file, ffmpeg for normalization, Whisper for speech, a vision model for frames, a vector database for embeddings, and glue code to keep timestamps aligned. That stitched pipeline typically means 8 services and about 6 weeks to a first feature; the single-API path is about 5 minutes to a first query ([videodb.io](https://videodb.io)).

![Bar chart comparing time to first video query: a stitched 8-service pipeline at ~6 weeks versus VideoDB at ~5 minutes](agent-vision-time-to-first-query.svg)
*Time to first working video query: stitched pipeline vs. one API. Source: [videodb.io](https://videodb.io).*

## What do you need before you start?

- Python 3.8+ and a terminal.
- A free VideoDB API key from the console (free tier, no card).
- A video to test with — a public URL (YouTube link, MP4) or a local file.
- Optional, for the agent step: any runtime that speaks tools — Claude Code, Cursor, n8n, Zapier, or your own MCP client.

That is the entire list. There is no ffmpeg install, no GPU, no vector database to provision.

> **Skip the prose, run the code.** The official quickstart mirrors every step below with copy-paste cells. [See the quickstart →][cta]

## How do you give an agent vision? Five steps

### Step 1 — Install the SDK and connect

```bash
pip install videodb
export VIDEO_DB_API_KEY="sk-..."
```

```python
import videodb

conn = videodb.connect()          # reads VIDEO_DB_API_KEY from env
coll = conn.get_collection()      # your default collection
```

A `Collection` is the container everything else lives in — videos, audio, images, and the indexes built over them ([VideoDB docs](https://docs.videodb.io)). Think of it as a database schema for continuous media.

### Step 2 — Upload a video

```python
video = coll.upload(url="https://www.youtube.com/watch?v=example")
# or: video = coll.upload(file_path="demo.mp4")

print(video.id, video.length)
```

Upload accepts URLs and local files through one normalized ingestion path; the same path also handles RTSP cameras, RTMP, and screen capture, which matters later when your agent graduates from files to [live feeds ↗][internal-rtsp]. The file is transcoded and made streamable on ingest — no ffmpeg step.

### Step 3 — Index speech and scenes

Indexes are additive layers of understanding over the same media. Build the two most useful ones:

```python
# What was said
video.index_spoken_words()

# What was shown — described by a model you choose
index_id = video.index_scenes(
    prompt="Describe the scene, on-screen text, and any people or objects."
)
```

`index_spoken_words()` creates a semantic transcript index; `index_scenes()` runs a vision model over sampled frames and stores scene-level descriptions ([VideoDB docs](https://docs.videodb.io)). Intelligence is pluggable — VideoDB is the data layer, and the vision/LLM model behind an index can be Twelve Labs, Gemini, OpenAI, Anthropic, or your own.

### Step 4 — Let the agent ask questions

```python
result = video.search(
    query="where does the speaker explain pricing?",
    index_type="spoken_word",
    search_type="semantic",
)

for shot in result.get_shots():
    print(shot.start, shot.end, shot.text)

print(result.play_stream())   # playable HLS URL of the matched moments
```

This is the property that makes the whole exercise agent-ready: search does not return a transcript line or a timestamp for a human to scrub to. It returns the moment as data — start, end, text — plus a stream URL materialized in milliseconds, with retrieval around ~120 ms even across large archives ([videodb.io](https://videodb.io)). An answer an agent can act on, and a clip a human can verify.

> **This is the whole loop.** Four calls: connect, upload, index, search. Everything past here is distribution. [Read the docs →][cta]

### Step 5 — Plug it into any agent runtime

You could wrap the four calls above in your own tool definition. You do not have to. VideoDB ships the agent surface pre-built, two ways:

```bash
# Option A: install video skills into your agent (Claude Code, Cursor, ...)
npx skills add video-db/skills

# Option B: run the MCP server
uvx videodb-director-mcp --api-key=$VIDEO_DB_API_KEY
```

The [skills repo](https://github.com/video-db/skills) packages server-side video workflows — capture, transcribe, search, edit, stream — as skills any coding agent can invoke. The [agent-toolkit](https://github.com/video-db/agent-toolkit) exposes the same capabilities as an MCP server plus maintained `llms.txt` context files, so AI IDEs stay in sync with the SDK. MCP is the open standard for connecting AI applications to external systems ([modelcontextprotocol.io](https://modelcontextprotocol.io)), which is exactly what makes this portable: one integration, and Claude Code, Cursor, n8n, Zapier, or your in-house agent all get the same video backend.

| Runtime | Integration path | What the agent gets |
|---|---|---|
| Claude Code / Cursor | `npx skills add video-db/skills` or MCP | Video tools inside the IDE loop |
| n8n / Zapier | HTTP nodes on the API, or skills | No-code video steps in workflows |
| Custom agent (Python) | SDK directly as a tool function | Full control, ~4 calls |
| Any MCP client | `videodb-director-mcp` | Standardized tool discovery |

For a heavier starting point, [Director](https://github.com/video-db/Director) is the open-source framework with 20+ pre-built video agents — summarization, search, clipping, dubbing — you can fork rather than write.

> **One command, your agent gets a video backend.** Skills install in the time it takes to read this sentence. [Browse the docs →][cta]

## What should you know before production?

**Index once, query forever.** Indexes persist with the collection, so the cost of understanding a video is paid once; agent queries against it are effectively unlimited ([videodb.io](https://videodb.io)). Structure your pipeline so ingestion and indexing happen on upload events, not per query.

**Scope memory deliberately.** Collections can be scoped per user, per agent, or per workspace. An agent that can search *everything* is rarely what you want in production; give each agent the narrowest collection that answers its questions.

**Compose indexes at query time.** Spoken-word search answers "what was said"; scene search answers "what was shown." Real questions often need both — that composition is the core move in [video RAG ↗][internal-video-rag], covered in its own tutorial.

**Batch and live are the same backend.** The SDK calls in this guide work unchanged when the source is an RTSP camera or a screen-capture session instead of a file. Real-time and recorded are modes, not separate products.

**Deployment follows compliance.** The same SDK runs against managed cloud, your own VPC, or edge — relevant the moment your footage includes patients, plants, or people's screens.

> **Prototype free, then load-test.** The common pattern is a four-week POC: install, integrate the agent loop, then test on 10,000+ items. [Start with the quickstart →][cta]

## Frequently asked questions

**Do I need my own vision model to index scenes?**
No. `index_scenes()` works out of the box with VideoDB's default models. If you have a preferred model — Twelve Labs, Gemini, OpenAI, Anthropic, or a fine-tuned one of your own — you can plug it in, and it wraps as an index like any other layer.

**Does this work with live camera feeds or only files?**
Both. The same ingestion path accepts RTSP, ONVIF, and RTMP sources, and the real-time component (RTStream) runs event detection and alerts at 1,000+ concurrent feeds. The file-based flow in this guide is the simplest on-ramp; the live-feed version is covered in the RTSP tutorial.

**How is this different from calling a multimodal LLM on video frames?**
A frame-by-frame VLM call gives you an answer and forgets everything. VideoDB builds persistent, queryable indexes, so the agent has memory: it can search a year of footage in one call, and every hit comes back as a playable clip rather than a token stream.

**What does the agent actually receive as a tool result?**
Structured moments: start time, end time, matched text or scene description, and a stream URL. That shape drops directly into an LLM context window as evidence, and into a UI as a playable clip.

**Is there a Node.js SDK?**
Yes — `videodb` on npm mirrors the Python SDK, and the MCP/skills route is language-agnostic anyway: if your agent speaks tools, it does not care what the backend SDK is written in.

### Five minutes was the point

Vision used to be the hardest tool to hand an agent — eight services and six weeks of glue. Now it is four SDK calls and one install command, and the agent gets back moments it can act on, not files it cannot watch. Wire it up and ask your footage a question. [Read the docs →][cta]

## Sources

- VideoDB documentation — https://docs.videodb.io
- VideoDB — https://videodb.io
- VideoDB skills (GitHub) — https://github.com/video-db/skills
- VideoDB agent-toolkit, MCP server (GitHub) — https://github.com/video-db/agent-toolkit
- Director agent framework (GitHub) — https://github.com/video-db/Director
- Model Context Protocol — https://modelcontextprotocol.io
- VideoDB cookbook (GitHub) — https://github.com/video-db/videodb-cookbook

[cta]: https://docs.videodb.io
[internal-hub]: /blog/what-is-video-infrastructure-for-ai-agents
[internal-agentic-perception]: /blog/agentic-perception
[internal-video-rag]: /blog/video-rag-tutorial
[internal-rtsp]: /blog/rtsp-stream-to-real-time-alerts
