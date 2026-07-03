<!--
- Primary keyword: ai agent memory   (110/mo · KD 53)
- SEO title (<=60 chars): AI Agent Memory: Desktop Capture for Coding Agents
- URL slug: desktop-capture-for-coding-agents
- Meta description (150–160 chars): Give coding agents replayable screen memory. Stream screen, mic, and system audio with the VideoDB Capture SDK into searchable, playable AI agent memory.
- Eyebrow: Developer guide
- Read time: 9 min read
- CTA stage: docs
-->

# AI Agent Memory: Desktop Capture for Coding Agents

*For developers building pair-programmer agents who want the agent to remember what happened on screen — and prove it with a playable clip.*

**AI agent memory** is the layer that lets an agent recall what it has perceived and done across sessions, instead of starting every conversation blind. For a coding agent, the richest memory source is not a chat log — it is the desktop itself: the editor, the terminal, the browser, the standup call. This tutorial builds replayable screen memory with the VideoDB Capture SDK: continuous capture of screen, microphone, and system audio, indexed into searchable moments, so your agent can answer "when did the test start failing?" with a playable clip.

## Why do coding agents need screen memory?

Coding agents need screen memory because most of what happens during a working session never reaches the agent's context window. The flaky test that started failing two hours ago, the config change you made in a terminal the agent never saw, the decision your teammate explained on a call — all of it scrolls past and disappears. Text-based memory (chat history, embeddings of notes) captures what was *said to the agent*, not what *happened on the machine*.

Continuous desktop perception fixes the asymmetry. Research on video-capable language models frames this as the missing modality for agents: video carries temporal, causal context that text summaries lose ([Video Understanding with LLMs: A Survey, arXiv:2312.17432](https://arxiv.org/abs/2312.17432)). VideoDB's own reference agents demonstrate the pattern in production shape: [pair-programmer](https://github.com/video-db/pair-programmer) is a screen- and voice-aware coding assistant, [focusd](https://github.com/video-db/focusd) is a desktop app that records and understands your screen, and [openclaw-monitoring](https://github.com/video-db/openclaw-monitoring) watches computer-use agents in real time — useful when the thing you need to replay is another agent's behavior.

The build-it-yourself alternative is a mini frankenstack: a screen recorder, Whisper for speech, a VLM for frames, a vector store for retrieval, object storage for the footage, and glue to keep timestamps aligned. The Capture SDK collapses that into one SDK with structured insights arriving in about two seconds ([videodb-capture-quickstart](https://github.com/video-db/videodb-capture-quickstart)).

![Bar chart comparing components required for replayable screen memory: a six-component DIY stack versus the single VideoDB Capture SDK](screen-memory-stack.svg)
*Replayable screen memory: the DIY stack versus one SDK with ~2-second insight latency. Source: [github.com/video-db/videodb-capture-quickstart](https://github.com/video-db/videodb-capture-quickstart).*

> **Memory your agent can replay, not just recall.** The Capture SDK quickstart takes one session from screen pixels to searchable transcript. [See the quickstart →][cta]

## What you'll build

A pair-programmer memory loop with four moving parts:

1. A backend that creates a capture session and mints short-lived client tokens (your API key never touches the desktop client).
2. A desktop client that streams three channels — screen, microphone, and system audio.
3. Indexing pipelines that turn the streams into a transcript layer and a visual scene layer as they arrive.
4. A search interface your agent calls to answer questions like "when did the test start failing?" — every answer a timestamped, playable moment.

## Prerequisites

- Python 3.9+ and `pip install videodb`
- A VideoDB API key from the console
- The Capture SDK quickstart cloned locally: [github.com/video-db/videodb-capture-quickstart](https://github.com/video-db/videodb-capture-quickstart)
- A desktop with screen-recording permission granted to your terminal or app

## Step 1 — Create a capture session on the backend

Sessions follow a token-based flow: the backend holds the API key, creates the session, and hands the desktop client a short-lived token. This matters in practice — a desktop app that ships with your API key embedded is a credential leak waiting to happen.

```python
import videodb

conn = videodb.connect(api_key="YOUR_API_KEY")  # server-side only

# Create a capture session — the container for one working session's memory
session = conn.create_capture_session(
    name="pairing-session-2026-07-03",
    channels=["display:1", "mic:default", "system_audio:default"],
)

# Mint a short-lived token for the desktop client
client_token = session.generate_client_token(expires_in=3600)
```

The three channels are the full sensory field of a pair-programming session: `display:1` sees the editor and terminal, `mic:default` hears you think out loud, and `system_audio:default` hears the other side of the call.

## Step 2 — Start capture from the desktop client

The desktop client authenticates with the token only, then starts streaming. The quickstart ships both Python and Node.js clients with the same conceptual flow ([videodb-capture-quickstart](https://github.com/video-db/videodb-capture-quickstart)).

```python
from videodb.capture import CaptureClient

client = CaptureClient(token=client_token)
client.start(
    channels=["display:1", "mic:default", "system_audio:default"]
)
# Streams flow to VideoDB Cloud; your backend gets a
# `capture_session.active` webhook when media is live.
```

From here the session is continuous media, not a pile of files. The same ingestion path handles uploads, RTSP cameras, and screen capture — one normalized pipe ([docs.videodb.io](https://docs.videodb.io)).

## Step 3 — Index the streams as they arrive

When your backend receives the `capture_session.active` webhook, switch on the AI pipelines. Two layers cover most coding-agent questions: a spoken-word layer for everything said, and a visual layer described through a prompt you control.

```python
# Backend, on webhook: capture_session.active
session.start_transcript(channel="mic:default")
session.start_transcript(channel="system_audio:default")

session.index_visuals(
    channel="display:1",
    prompt=(
        "Describe the developer's screen: application in focus, "
        "file names, terminal commands, test results, and error "
        "messages. Note when tests pass or fail."
    ),
)
```

The prompt is doing real work. Because indexing is prompt-programmable, you can teach the visual layer your domain vocabulary — "note when tests pass or fail" turns a generic scene description into a queryable engineering event stream. Indexes are additive layers, so you can add a second one later (say, "flag any credentials visible on screen") without re-capturing anything ([docs.videodb.io](https://docs.videodb.io)).

> **Indexes as code.** One prompt turns raw screen pixels into a structured event stream your agent can query. [Read the docs →][cta]

## Step 4 — Consume live events over WebSocket

Structured insights arrive within about two seconds of capture ([videodb-capture-quickstart](https://github.com/video-db/videodb-capture-quickstart)). Your agent can subscribe and react in the moment — the same loop [openclaw-monitoring](https://github.com/video-db/openclaw-monitoring) uses to supervise computer-use agents.

```python
async for event in session.events.receive():
    if event.channel == "transcript":
        agent.observe(f"[heard] {event.text}")
    elif event.channel == "scene_index":
        agent.observe(f"[saw] {event.description}")
        if "test failed" in event.description.lower():
            agent.investigate(event.start, event.end)
```

This is the "See" and part of the "Understand" in VideoDB's See → Understand → Act loop. The agent is no longer limited to what you paste into chat; it perceives the session as it happens.

## Step 5 — Search session history like a database

Memory earns its name when the session is over. Everything captured persists as scene-level memory — scoped per user, agent, or workspace, and re-indexable later with better models ([videodb.io](https://videodb.io)). Ask the question every developer asks at 4 p.m.:

```python
results = session.search("when did the test suite start failing?")

for shot in results.shots:
    print(f"{shot.start}s–{shot.end}s: {shot.text}")

stream_url = results.play()  # a playable clip, not a timestamp
```

The result is the differentiating part: not a log line, not a float offset, but a playable clip materialized in milliseconds. Your agent can cite it; you can watch it. The unit is the moment, not the file.

Here is how the approaches to agent memory compare for a coding agent:

| Memory approach | What it captures | Can it replay the moment? | Temporal context |
|---|---|---|---|
| Chat history | What was said to the agent | No | Weak |
| Notes + embeddings | What someone wrote down | No | None |
| Screenshots + OCR | Static frames, no audio | No | Fragmented |
| Continuous capture (this guide) | Screen + mic + system audio, indexed | Yes — playable clips | Native |

> **"When did the test start failing?" is a query now.** Session history becomes a database your agent reads. [See the quickstart →][cta]

## Production notes

- **Privacy is a product decision, not an afterthought.** Capture sessions see everything on screen, including secrets. Scope memory per user or workspace, set retention windows, and consider a visual index prompt that flags exposed credentials. VideoDB's memory is retention-aware by design ([videodb.io](https://videodb.io)).
- **Keep the API key server-side.** The token flow in Step 1 exists so desktop clients hold only short-lived credentials. Do not shortcut it in production.
- **Index selectively if cost matters.** Transcripts are cheap; visual indexing every second of an eight-hour workday is not. Many teams transcribe continuously but index visuals only around events — test runs, deploys, meetings.
- **The same backend scales past one desktop.** The SDK that powers a single pair-programmer session also powers 1,000+ concurrent live feeds — capture is one ingest mode of the same platform, part of the broader case for [video infrastructure for AI agents ↗][internal-hub] and the [agentic perception ↗][internal-agentic-perception] pattern.
- **Start smaller if this is your first agent.** If you have never wired vision into an agent before, the five-minute version — one uploaded video, one index, one search — is covered in [giving your AI agent vision ↗][internal-agent-vision].

## Frequently asked questions

**What is AI agent memory?**
AI agent memory is the persistent layer that lets an agent recall past observations, actions, and context across sessions. For desktop agents, the strongest form is perceptual memory: continuous screen and audio capture indexed into searchable, replayable moments, rather than text summaries of what the agent was told.

**How is this different from taking screenshots and running OCR?**
Screenshots are discrete samples with no audio and no temporal continuity — they miss everything that happens between frames and everything that is said. Continuous capture preserves the timeline, pairs vision with speech, and returns playable clips, so the agent can reason about *when* and *why*, not just *what*.

**Does the desktop client need my VideoDB API key?**
No. The backend creates the capture session and mints short-lived client tokens; the desktop client authenticates with the token only. Your API key stays server-side ([videodb-capture-quickstart](https://github.com/video-db/videodb-capture-quickstart)).

**How fast do insights arrive after something happens on screen?**
Structured events — transcript lines and scene descriptions — arrive over WebSocket within about two seconds of capture, which is fast enough for an agent to react during the session rather than after it ([videodb-capture-quickstart](https://github.com/video-db/videodb-capture-quickstart)).

**Can I search across many sessions, not just one?**
Yes. Sessions persist as scene-level memory in a collection, scoped per user, agent, or workspace. Collection-level search spans all of them, so "when did we last touch the auth config?" can search a month of sessions and return the playable moment.

### Give your agent a memory it can replay

A coding agent that saw the session is more useful than one that was told about it. Capture screen, mic, and system audio through one SDK, index it into searchable layers, and every "when did X happen?" becomes a query with a playable answer. To see is to know. [Read the docs →][cta]

## Sources

- VideoDB Capture SDK Quickstart — https://github.com/video-db/videodb-capture-quickstart
- pair-programmer: screen- and voice-aware coding assistant — https://github.com/video-db/pair-programmer
- focusd: desktop app that records and understands your screen — https://github.com/video-db/focusd
- openclaw-monitoring: monitor computer-use agents in real time — https://github.com/video-db/openclaw-monitoring
- VideoDB Documentation — https://docs.videodb.io
- VideoDB — https://videodb.io
- Video Understanding with Large Language Models: A Survey (arXiv:2312.17432) — https://arxiv.org/abs/2312.17432

[cta]: https://docs.videodb.io
[internal-hub]: /blog/what-is-video-infrastructure-for-ai-agents
[internal-agentic-perception]: /blog/agentic-perception
[internal-agent-vision]: /blog/give-your-ai-agent-vision-in-5-minutes
