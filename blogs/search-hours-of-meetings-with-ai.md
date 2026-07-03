<!--
- Primary keyword: ai meeting notes   (1,600/mo · KD 73); secondary: meeting transcription (590/mo · KD 85)
- SEO title (<=60 chars): AI Meeting Notes Without Bots: Search Months of Meetings
- URL slug: search-hours-of-meetings-with-ai
- Meta description (150–160 chars): Build AI meeting notes without bots: capture screen and audio with the Capture SDK, index spoken words, and search months of meetings for playable moments.
- Eyebrow: Developer guide
- Read time: 9 min read
- CTA stage: docs
-->

# Search hours of meetings with AI — no bot in the room

*For developers building meeting intelligence into their product, and for teams tired of a "notetaker" joining every call.*

You search hours of meetings by capturing them at the desktop — screen, microphone, and system audio, no bot participant — indexing every spoken word, and querying the whole archive semantically. **AI meeting notes** built this way return more than a summary: every decision comes back as a playable moment with a timestamp, so "when did we agree to drop the Q3 feature?" resolves to the 40 seconds where it happened. This tutorial builds that pipeline end to end on VideoDB, the [video infrastructure layer for AI agents ↗][internal-hub], and closes with an honest comparison against bot-based note-takers.

## What will you build?

A meeting memory system with three properties:

1. **Botless capture** — recording happens on your machine via the Capture SDK (screen, mic, and system audio as separate channels), so it works across Zoom, Meet, Teams, and calls that never touched a calendar.
2. **Meeting transcription as an index, not a document** — spoken words become a searchable layer with timestamps, not a wall of text.
3. **Semantic search across months** — one query spans every meeting in the collection and returns playable evidence.

The reference implementation for this pattern is [call.md](https://github.com/video-db/call.md), VideoDB's open-source desktop app that records, transcribes, and analyzes meetings with live AI assistance — worth reading alongside this guide.

**Prerequisites:** Python 3.8+, a VideoDB API key (free tier), `pip install videodb`, and — for live capture — the [Capture SDK quickstart](https://github.com/video-db/videodb-capture-quickstart), which ships minimal Node.js and Python starters. If you only have existing recordings, you can skip capture and start at Step 3.

> **The Capture SDK has its own quickstart.** Session tokens, channel setup, and event delivery are documented end to end. [Read the docs →][cta]

## How do you build botless meeting search? Five steps

### Step 1 — Set up capture sessions

The Capture SDK uses a small backend-plus-client split: your backend creates a session and mints a short-lived client token; the desktop client streams media without ever holding your API key ([videodb-capture-quickstart](https://github.com/video-db/videodb-capture-quickstart)).

```python
import videodb

conn = videodb.connect()               # server side, holds the API key
coll = conn.get_collection()

session = conn.create_capture_session(user_id="shiv")
token = session.generate_client_token()   # hand this to the desktop client
```

The client then opens the channels you ask for — screen, microphone, system audio. System audio is the piece DIY approaches miss: it is how you record the *other* side of a call without joining it as a participant.

### Step 2 — Capture a meeting

On the desktop side (the quickstart provides this scaffolding), a capture session streams during the meeting and lands in your collection as media when it ends. No participant named "Notetaker" appears in the roster; nothing depends on the meeting platform's bot API. This is the same capture surface that powers pair-programmer agents and [desktop-aware coding assistants ↗][internal-capture], so the investment reuses beyond meetings.

If you have historical recordings instead, ingestion is one call:

```python
video = coll.upload(file_path="all-hands-2026-06-12.mp4")
```

### Step 3 — Index spoken words

```python
video.index_spoken_words()
```

That single call is the entire transcription pipeline. Under the hood this is the job you would otherwise self-host with a speech model such as OpenAI's Whisper, a general-purpose open-source speech recognition model ([github.com/openai/whisper](https://github.com/openai/whisper)) — plus the parts Whisper does not do: storage, timestamps aligned to playable media, and a search index over the result. Indexing is additive and re-runnable, so a year of backlog can be indexed once and queried forever.

### Step 4 — Search months of meetings in one query

Search at the collection level, not per file:

```python
result = coll.search(
    query="when did we decide to drop the Q3 pricing experiment?",
    index_type="spoken_word",
    search_type="semantic",
)

for shot in result.get_shots():
    print(shot.video_id, shot.start, shot.end, shot.text)

print(result.play_stream())   # the decision moments, playable
```

Semantic search means the query does not need the words that were actually said — "drop the pricing experiment" matches "let's kill the A/B on the new tiers." Every hit is a moment with a start and end, materialized as a playable clip in milliseconds; retrieval runs at roughly ~120 ms even across very large archives ([videodb.io](https://videodb.io)).

### Step 5 — Turn moments into notes, tickets, and agents

Structured moments compose into whatever "notes" means in your product:

```python
decisions = [
    {"text": s.text, "at": s.start, "clip": result.play_stream()}
    for s in result.get_shots()
]
# → render as AI meeting notes, push to your ticket tracker,
#   or return as a tool result to an agent
```

call.md demonstrates the agentic end state: live assistance during the call, multi-part summaries after it, and MCP-triggered tools — with exports into n8n and Zapier workflows ([call.md](https://github.com/video-db/call.md)). Because the archive is queryable, the same data also feeds [video RAG ↗][internal-video-rag]: an agent that cites the meeting where a decision happened, with a link that plays it.

> **Decision moments with playable evidence.** That is the difference between a summary you trust and a summary you re-watch the call to verify. [See the quickstart →][cta]

## How does this compare to bot-based note-takers?

Bot-based tools (the familiar meeting-notes SaaS pattern) join the call as a participant, record server-side, and email a summary. Honest comparison:

| Dimension | Bot note-taker | Capture-based (this guide) |
|---|---|---|
| Presence in call | Visible participant; joins via platform API | None; records at your desktop |
| Coverage | Calendar meetings on supported platforms | Any audio/video on the machine — huddles, ad-hoc calls, demos |
| Screen content | Usually audio/speech only | Screen is a first-class channel |
| Output | Summary document | Indexed archive + summaries; every claim playable |
| Search | Within their app, per meeting | One semantic query across months, via API |
| Build-your-own | Closed SaaS | SDK primitives; it is *your* product |

Where bots genuinely win: they capture the call even when your machine is off, they can operate organization-wide without desktop software, and mature vendors ship polished speaker-identification and CRM integrations out of the box. If you want a finished notes app for a sales team and have no engineering appetite, a bot product is the pragmatic buy.

The capture approach wins when you are *building* — a meeting feature inside your own product, an agent that needs meeting memory as a tool, or a team that finds a bot in every candidate interview and customer call unacceptable. And structurally: a bot pipeline produces documents, while an indexed archive produces data. Only one of those can answer a question it was not summarized for.

![Bar chart comparing services required for a meeting intelligence feature: a stitched stack of about 6 services versus 1 API with VideoDB](meeting-intelligence-stack.svg)
*Shipping meeting search yourself: recorder, speech model, storage, vector DB, player, glue — vs. one API. Source: [videodb.io](https://videodb.io).*

> **Your meetings, your API.** Capture, transcription, and search are primitives you compose — not a SaaS you embed. [Read the docs →][cta]

## What should you know before production?

**Consent is a product feature.** Recording laws vary by jurisdiction (one-party vs. all-party consent). Botless does not mean silent — build the disclosure into your UX, and scope retention windows per workspace. VideoDB's memory is retention-aware for exactly this.

**Scope collections per user or team.** Meeting archives are sensitive by default. Use per-user or per-workspace collections so search boundaries match permission boundaries.

**Index visuals when screens matter.** `index_spoken_words()` covers the conversation; adding a scene index over the screen channel makes shared slides and demos searchable too ("the dashboard we saw in the vendor demo").

**Data control:** capture-based pipelines can run against your own VPC deployment when meeting content cannot leave your infrastructure — a hard blocker with most hosted bot vendors.

## Frequently asked questions

**Is this meeting transcription accurate enough for notes?**
Spoken-word indexing is built on modern speech models of the Whisper generation and returns timestamped text designed for retrieval. The practical safeguard is structural: every extracted note links to the playable moment, so verification is one click rather than a transcript hunt.

**Do participants know they are being recorded?**
Nothing appears in the meeting roster, so disclosure is your application's responsibility. Treat consent UX as a launch requirement, not an afterthought — the legal duty is unchanged whether the recorder is a bot or a desktop client.

**Can I search meetings I recorded before adopting this?**
Yes. Upload historical recordings into the collection and run `index_spoken_words()` over the backlog; old and new meetings become one searchable archive.

**How is this different from Zoom's or Meet's built-in AI notes?**
Built-ins summarize one meeting inside one platform. This pipeline is cross-platform, API-first, and cumulative: months of meetings across every tool become a single queryable memory your own product or agent can call.

**What does an agent get from this compared to a transcript file?**
A tool result, not a document: matched moments with video ID, start, end, text, and a stream URL. An agent can quote the decision, cite the timestamp, and hand a human the clip — the same shape used across VideoDB's agent examples.

### Meetings are a database now

The recording was never the hard part; retrieval was. Capture without bots, index the words once, and months of meetings collapse into a query that returns the moment itself. Build the pipeline in an afternoon and let your product answer "when did we decide that?" with proof. [Read the docs →][cta]

The full open-source reference — live assist, summaries, MCP tool calls — is [call.md](https://github.com/video-db/call.md).

## Sources

- call.md, meetings-to-agents reference app (GitHub) — https://github.com/video-db/call.md
- VideoDB Capture SDK quickstart (GitHub) — https://github.com/video-db/videodb-capture-quickstart
- VideoDB documentation — https://docs.videodb.io
- VideoDB — https://videodb.io
- OpenAI Whisper (GitHub) — https://github.com/openai/whisper
- Model Context Protocol — https://modelcontextprotocol.io

[cta]: https://docs.videodb.io
[internal-hub]: /blog/what-is-video-infrastructure-for-ai-agents
[internal-capture]: /blog/desktop-capture-for-coding-agents
[internal-video-rag]: /blog/video-rag-tutorial
