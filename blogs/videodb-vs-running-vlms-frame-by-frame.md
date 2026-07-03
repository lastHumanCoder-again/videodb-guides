<!--
- Primary keyword: video llm   (140/mo · KD 34)
- Secondary keyword: vision language models   (1,300/mo · KD 58)
- SEO title (<=60 chars): Video LLM Costs: Frame-by-Frame vs. Indexing Once
- URL slug: videodb-vs-running-vlms-frame-by-frame
- Meta description (150–160 chars): Sampling frames and sending each to a video LLM gets expensive fast. Real cost math for vision language models on video — and when indexing once wins.
- Eyebrow: Build vs. buy
- Read time: 8 min read
- CTA stage: console
-->

# Video LLMs: frame-by-frame calls vs. indexing once

*For engineers who got a video demo working with GPT, Gemini, or Claude — and now need it to survive real archives and real query volume.*

A **video LLM** pipeline usually starts the same way: sample frames from the video, send each frame (or a batch) to a vision language model, and stitch the answers together. It works, it demos well, and it quietly encodes a decision that gets expensive — every question re-reads the entire video. This piece walks through the actual cost math with stated assumptions, the latency and memory problems that arrive before the bill does, when frame-by-frame is genuinely the right call, and how the same models behave differently when they're plugged in as indexes instead of being called in a loop.

## What does running a VLM frame by frame actually involve?

Frame-by-frame video analysis means converting a continuous stream into a sequence of still images and paying model-inference prices for each one. There is no video-native step: the model sees pictures, and your code is responsible for sampling, batching, ordering, and reconciling the answers.

The canonical loop looks like this: extract frames at some rate (commonly 0.5–2 frames per second), resize them, base64-encode them, attach them to a chat completion request, and parse the text that comes back. OpenAI's vision models bill those images as tokens using a tile calculation — a 512×512 image at high detail costs roughly 255 tokens (an 85-token base plus 170 tokens per 512-px tile) ([OpenAI vision guide](https://developers.openai.com/api/docs/guides/images-vision)). Gemini accepts video files directly, but under the hood it does the same thing on your behalf: it samples at 1 frame per second and charges about 300 tokens per second of video at default resolution — 258 tokens per frame plus 32 tokens of audio ([Gemini video understanding docs](https://ai.google.dev/gemini-api/docs/video-understanding)).

Either way, the unit of work is the token, and tokens are ephemeral. Nothing about the video persists after the response arrives.

> **The loop is the architecture.** If your video pipeline is a `for` loop over frames, the costs below are already committed. See what the index-once pattern looks like. [Try VideoDB free →][cta]

## What does frame-by-frame video analysis cost?

For one short clip and one question, almost nothing — that is why the demo works. The problem is that cost scales with *video length × question count*, because every new question re-processes every frame.

Here is the math, with assumptions stated so you can rerun it with your own numbers:

- **Sampling rate:** 1 frame per second (Gemini's default) ([Gemini docs](https://ai.google.dev/gemini-api/docs/video-understanding)).
- **Tokens per second of video:** ~300 at default resolution (258 frame + 32 audio) ([Gemini docs](https://ai.google.dev/gemini-api/docs/video-understanding)).
- **Model pricing:** Gemini 2.5 Flash at **$0.30 per 1M input tokens** for text, image, and video ([Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)). Output tokens ($2.50/1M) excluded to keep the math conservative.

One hour of video is 3,600 seconds ≈ **1.08M input tokens ≈ $0.32 per full pass**. Harmless. Now scale both axes:

- A **1,000-hour archive** is ~1.08B input tokens. Every question that has to consider the whole archive costs **~$324** — per question.
- **100 questions** against that archive: **~$32,400**. On Gemini 2.5 Pro ($2.50/1M for prompts over 200k tokens), the same workload runs ~8× higher ([pricing](https://ai.google.dev/gemini-api/docs/pricing)).

![Bar chart comparing cumulative cost of frame-by-frame VLM questions against a 1,000-hour archive versus indexing once](frame-by-frame-cost-curve.svg)
*Question N costs the same as question 1 when every query re-reads the archive; an index pays the model cost once. Source: derived from Gemini API pricing (ai.google.dev) at ~300 tokens/s of video; retrieval latency from videodb.io.*

The index-once pattern spends roughly the same as *one* frame-by-frame pass — the model still has to see the footage once — and then answers question 2 through question 10,000 from the index, at retrieval cost instead of inference cost. VideoDB serves those lookups in **~120ms across petabyte-scale archives** ([videodb.io](https://videodb.io)).

## Why do latency and memory break before cost does?

Latency fails first because a question cannot return faster than the model can re-read the footage. A single 1-hour video at default resolution is ~1.08M tokens — at or beyond the 1M-token context window, which caps out at about one hour of default-resolution video per request ([Gemini docs](https://ai.google.dev/gemini-api/docs/video-understanding)). Longer footage forces chunking, chunking forces parallel calls, and parallel calls force you to write the stitching logic that reconciles contradictory per-chunk answers. Your user waits minutes for what should be a lookup.

Memory fails second, and more fundamentally: vision language models are stateless. Ask "when did the demo crash?" today and "what was on screen right before that?" tomorrow, and the model starts from zero both times. There is no accumulated understanding of the archive, no scoping per user or agent, no way for an agent to *remember* video between sessions. Frame-by-frame pipelines have no unit smaller than "the whole video, again" — while the useful unit is the moment ([VideoDB docs](https://docs.videodb.io)).

> **Agents need recall, not re-reads.** Give your agent scene-level memory it can query across sessions instead of a context window it refills every turn. [Get an API key →][cta]

## When is frame-by-frame the right call?

For one-off questions on short clips, frame-by-frame is fine — honestly, it's the right tool. If you're analyzing a 90-second clip once, or prototyping to learn what a model can even see, an index would be overhead: a direct Gemini or GPT call is simpler, and at ~$0.32 per hour-long pass the cost is irrelevant at small scale.

Frame-by-frame holds up when all three are true: the videos are short (under the context window), each video is queried once or twice ever, and nothing needs to persist. Ad-hoc clip QA, single-pass moderation checks on user uploads, and quick experiments all qualify. The pattern breaks when any axis grows — archive size, question volume, or the need for memory. If you're re-processing the same footage to answer a second question, you've crossed the line.

## How does VideoDB use the same models differently?

VideoDB doesn't replace the vision language model — it changes where the model sits. VideoDB is bring-your-own-model infrastructure: **Twelve Labs, Gemini, OpenAI, Anthropic, or your own model** wraps cleanly as an *index* — a reusable, additive layer of understanding over the media — rather than being invoked per question ([videodb.io](https://videodb.io)). The model runs once at index time; queries hit the index thereafter. In regulated settings your model IP is never exposed.

```python
import videodb  # pip install videodb
from videodb import SearchType

conn = videodb.connect(api_key="YOUR_API_KEY")
coll = conn.get_collection()
video = coll.upload(url="https://example.com/keynote.mp4")

# index once — the VLM you choose runs here, not per question
video.index_spoken_words()
video.index_scenes(prompt="Describe products, people, and on-screen text")

# query forever — every hit is a playable moment, not a frame number
results = video.search("when does the pricing slide appear?",
                       search_type=SearchType.semantic)
results.play()
```

Because indexes are additive, you can layer them: a transcript index, a Twelve Labs scene index, a custom-prompt index for your domain's events — and compose them at query time. Re-indexing with a better model later doesn't mean rebuilding the pipeline; it means adding a layer. This is the practical difference between a video LLM *call* and video infrastructure: the model is a component, not the architecture. For how search behaves on top of those indexes, see [semantic search vs. keyword search over video ↗][internal-semantic-search], and for the full stack picture, the hub on [video infrastructure for AI agents ↗][internal-hub].

> **Same model, one-time cost.** Plug the VLM you already trust in as an index and stop paying it per question. [Start free in the console →][cta]

## Which model should you plug in?

Measure on your own footage, because VLM performance varies more by task than by leaderboard. VideoDB's research arm, [labs.videodb.io](https://labs.videodb.io), publishes evaluations aimed at exactly this decision.

Two useful data points. The [ocr-benchmark](https://github.com/video-db/ocr-benchmark) repo tested VLMs on text extraction across 25 videos in five categories: GPT-4o and Gemini 1.5 Pro both landed around 76% accuracy, well ahead of traditional OCR engines like RapidOCR at ~57% — evidence that VLMs-as-indexes beat classic CV pipelines for in-video text. The [gemini-reasoning-eval](https://github.com/video-db/gemini-reasoning-eval) repo benchmarked Gemini 2.5 Flash variants across 100 hours of video and found reasoning-quality gains plateau after roughly 300 thinking tokens — the smaller Flash Lite configuration matched or beat larger budgets while using ~30% fewer tokens. Bigger spend is not automatically better perception; a swappable model layer lets you act on that finding without re-architecting. If you're comparing this build against managed options more broadly, the [ffmpeg-plus-vector-database comparison ↗][internal-ffmpeg] covers the rest of the stack.

## Frequently asked questions

**What is a video LLM?**
"Video LLM" usually refers to a vision language model applied to video — either by sampling frames into a multimodal model (GPT-4o-style) or via video-native ingestion (Gemini, Twelve Labs). No mainstream model watches video continuously; all of them tokenize sampled frames, typically at around 1 frame per second.

**How many tokens is an hour of video?**
On Gemini at default resolution, about 1.08M tokens (~300 tokens per second, covering frames plus audio). At low resolution it drops to ~100 tokens per second, trading visual detail for a 3-hour ceiling per request.

**Can GPT-4o or Claude watch a video directly?**
Not as a stream. OpenAI and Anthropic vision models accept images, so video must be sampled into frames client-side and billed per image tile. Gemini accepts video files but samples them to ~1 fps internally — the frame-by-frame economics still apply.

**Do vision language models have memory across requests?**
No. Each request is stateless; understanding exists only inside that context window. Persistent, queryable memory over video requires an external layer — that's what an index-and-memory system like VideoDB provides, with the VLM plugged in as the intelligence.

**Is 1 frame per second enough to catch fast events?**
Often not — a fumble, a flash of on-screen text, or a safety event can pass between samples. Denser sampling raises cost linearly in a frame-by-frame pipeline. Index-based systems can sample densely once at ingest and never pay that density again per query.

### Index once. Ask forever.

The models are good; the loop is the problem. Keep the VLM you trust, run it once as an index, and turn every question after the first into a ~120ms lookup instead of a full re-read. First query in about five minutes. [Try VideoDB free →][cta]

## Sources

- Gemini API pricing — https://ai.google.dev/gemini-api/docs/pricing
- Gemini video understanding (tokenization, 1 fps sampling, context limits) — https://ai.google.dev/gemini-api/docs/video-understanding
- OpenAI images & vision guide (image token calculation) — https://developers.openai.com/api/docs/guides/images-vision
- VideoDB OCR benchmark (VLMs vs. traditional OCR on video) — https://github.com/video-db/ocr-benchmark
- VideoDB Gemini reasoning evaluation (thinking tokens vs. quality) — https://github.com/video-db/gemini-reasoning-eval
- VideoDB Labs research — https://labs.videodb.io
- VideoDB (retrieval latency, bring-your-own-model) — https://videodb.io
- VideoDB documentation — https://docs.videodb.io

[cta]: https://console.videodb.io
[internal-hub]: /blog/what-is-video-infrastructure-for-ai-agents
[internal-semantic-search]: /blog/semantic-video-search-vs-keyword-search
[internal-ffmpeg]: /blog/videodb-vs-building-with-ffmpeg-and-a-vector-database
