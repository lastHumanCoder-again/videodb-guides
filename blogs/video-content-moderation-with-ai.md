<!--
- Primary keyword: video moderation api   (50/mo · KD 18); secondary: content moderation api (210/mo · KD 36)
- SEO title (<=60 chars): Video Moderation API: Build an AI Moderation Pipeline
- URL slug: video-content-moderation-with-ai
- Meta description (150–160 chars): Build a video moderation API pipeline: profanity detection, visual policy checks with custom indexes, and human review queues with playable evidence clips.
- Eyebrow: Developer guide
- Read time: 9 min read
- CTA stage: docs
-->

# Video Moderation API: Build an AI Moderation Pipeline

*For platform engineers who need to screen uploaded and live video against policy — with evidence a human reviewer can watch, not a score they have to trust.*

A **video moderation API** screens video content against policy programmatically: it transcribes speech to catch profanity and harassment, analyzes visuals for policy violations, and routes flagged moments to human reviewers. The pipeline worth building has one property most miss — every flag carries a playable evidence clip, so a reviewer judges the actual moment instead of a thumbnail and a confidence score. This tutorial builds that pipeline in Python: a spoken-word layer for language, custom-prompt visual indexing for policy, and a review queue with watchable evidence.

## Why is video moderation harder than text moderation?

Video moderation is harder because a violation can live in any layer — the words spoken, the things shown, the text on screen — and because context decides severity: the same clip can be medical education or graphic content. Text moderation is a single classification over a string; even there, production systems require careful category design and continuous human feedback ([OpenAI, A Holistic Approach to Undesired Content Detection, arXiv:2208.03274](https://arxiv.org/abs/2208.03274)). Video multiplies the problem across time and modality.

Scale is the other constraint. Human-only review does not scale to platform volume; the established industry pattern is ML-first triage, where models filter the stream and humans review the **1–5% of volume** that gets flagged ([AWS Rekognition moderation docs](https://docs.aws.amazon.com/rekognition/latest/dg/moderation.html)). That makes the moderation problem an infrastructure problem: the pipeline must index everything, flag reliably, and hand reviewers exactly the moments that matter — which is what a video database is for, as covered in [video infrastructure for AI agents ↗][internal-hub].

![Bar chart showing share of content volume reaching human reviewers: 100 percent under manual-first moderation versus roughly 1 to 5 percent with ML-first triage](moderation-human-review-volume.svg)
*ML-first triage cuts the human review queue to roughly 1–5% of total volume. Source: [AWS Rekognition documentation](https://docs.aws.amazon.com/rekognition/latest/dg/moderation.html).*

## What you'll build

A moderation pipeline with four stages:

1. **Speech screening** — profanity and policy language detection over a spoken-word index.
2. **Visual policy checks** — your written content policy compiled into a custom-prompt visual index.
3. **A human-review queue** — flagged moments with playable evidence clips and timestamps.
4. **Live mode** — the same checks running on streams with webhook alerts.

## Prerequisites

- Python 3.9+ and `pip install videodb`
- A VideoDB API key
- A written content policy — the pipeline is only as good as the policy you can articulate

## Step 1 — Ingest and index speech

```python
import videodb

conn = videodb.connect(api_key="YOUR_API_KEY")
coll = conn.get_collection()

video = coll.upload(url="https://example.com/user-upload-8271.mp4")
video.index_spoken_words()

flags = []
for term in ["profanity", "threats of violence", "harassment"]:
    results = video.search(term)
    for shot in results.shots:
        flags.append({"layer": "speech", "reason": term,
                      "start": shot.start, "end": shot.end,
                      "text": shot.text})
```

Semantic search over the spoken-word index catches more than a wordlist: "threats of violence" matches phrasing a blocklist never anticipated. VideoDB's published safety examples cover this exact pattern — content moderation and profanity detection are two of its documented AI-safety use cases ([docs.videodb.io](https://docs.videodb.io)).

## Step 2 — Compile your policy into a visual index

Custom-prompt indexing lets you express policy in plain language and run it as an index layer. This is the moderation-specific payoff of "indexes as code":

```python
video.index_scenes(
    prompt=(
        "You are a content policy reviewer. Flag and describe any "
        "scene containing: graphic violence or injury; nudity or "
        "sexual content; weapons brandished at people; drug use; "
        "or visible personal data such as ID documents. "
        "State which category applies and what is visible."
    )
)

visual_hits = video.search("policy violation", index_type="scene")
```

Because intelligence is pluggable, the model behind this layer can be Gemini, OpenAI, Anthropic, Twelve Labs, or your own classifier wrapped as an index — teams with proprietary moderation models keep their model IP private while using the same pipeline ([videodb.io](https://videodb.io)). On-screen text (slurs in overlays, phone numbers, doxxing) is its own sublayer; see [extracting text from video with OCR ↗][internal-ocr].

> **Your policy, compiled to an index.** Write the rule in plain language; run it over every upload. [Read the docs →][cta]

## Step 3 — Build the human-review queue

Automated flags should route to humans with evidence attached. The materialized clip is the difference between a review queue and a guessing game:

```python
def enqueue_for_review(video, flag):
    clip_url = video.generate_stream(
        timeline=[(max(0, flag["start"] - 5), flag["end"] + 5)]
    )
    review_queue.push({
        "video_id": video.id,
        "reason": flag["reason"],
        "evidence_clip": clip_url,          # playable, padded ±5s
        "timestamp": (flag["start"], flag["end"]),
        "auto_action": "hold" if flag["layer"] == "speech" else "block",
    })

for flag in flags:
    enqueue_for_review(video, flag)
```

The ±5 second padding gives reviewers context — the sentence before the slur, the scene before the cut. Clips materialize in milliseconds without re-encoding, so the queue stays cheap even at platform volume ([docs.videodb.io](https://docs.videodb.io)).

## Step 4 — Run the same checks on live streams

Recorded and live are modes of the same backend, so live moderation is the same indexes pointed at a stream, with alerts instead of queries:

```python
rtstream = conn.get_rtstream(url="rtmp://ingest.example.com/live/creator-991")

rtstream.index_scenes(prompt="Flag nudity, graphic violence, or weapons")
rtstream.create_alert(
    event="policy violation",
    webhook="https://trust.example.com/hooks/moderation",
)
```

RTStream delivers webhook and WebSocket events with sub-second latency and is tested at 1,000+ concurrent feeds ([videodb.io](https://videodb.io)) — the same architecture behind [live camera intelligence ↗][internal-live].

> **Live and recorded, one pipeline.** The index that screens uploads also watches streams. [See the quickstart →][cta]

## How accurate is AI moderation — honestly?

Not accurate enough to run unsupervised, and you should design for that. Three realities to plan around:

- **False negatives are structural.** Violations can be oblique — coded language, context-dependent imagery, policy-violating text in a corner of the frame. Measured VLM accuracy on video text tasks ranges from 49% to 76% depending on model ([ocr-benchmark](https://github.com/video-db/ocr-benchmark)); assume comparable variance on your policy categories until you have measured them.
- **False positives burn reviewers and creators.** Medical content, news footage, and art trip naive visual checks. Calibrate thresholds per category on a labeled sample of your own content, and track precision per category, not one blended score.
- **Human-in-the-loop is the system, not a fallback.** OpenAI's production moderation work found continuous human labeling and active learning essential to keep classifiers aligned with evolving policy ([arXiv:2208.03274](https://arxiv.org/abs/2208.03274)). Route uncertain flags to review, feed reviewer decisions back as labeled data, and re-index when models or policies improve — indexes are additive and re-runnable, so yesterday's footage can be re-screened under today's policy.

| Design choice | Auto-block | Auto-hold + human review | Auto-pass |
|---|---|---|---|
| When | High-confidence, severe categories | Medium confidence, or severe-but-ambiguous | Below flag threshold |
| Risk | False positives silence users | Queue latency | False negatives ship |
| Mitigation | Appeal path with evidence clip | Padded clips speed review | Spot-sample audits |

## Production notes

- **Compliance posture matters in moderation, where footage can involve minors, health data, or regulated content.** VideoDB runs managed cloud, in your VPC, or at the edge, with SOC 2 Type II, ISO 27001, HIPAA-ready, and GDPR-aligned posture, multi-region across US, EU, and India ([videodb.io](https://videodb.io)).
- **Keep the evidence trail.** Store flag, clip URL, reviewer decision, and policy version together; when a takedown is appealed or regulators ask, the playable moment is your audit record.
- **Retention is policy too.** Scene-level memory is retention-aware — set windows that match your legal obligations rather than keeping everything forever.
- **Trade-offs, honestly:** if you only moderate still images, a point classifier API is simpler and cheaper. The indexed-pipeline approach earns its keep when content is continuous — long uploads and live streams — where "where in these three hours is the violation?" is the actual problem.

> **Flags with evidence, not just scores.** Every item in the queue is a watchable moment. [Read the docs →][cta]

## Frequently asked questions

**What is a video moderation API?**
A video moderation API screens video against content policy programmatically: transcribing speech, analyzing visuals, detecting policy-relevant events, and returning flags with timestamps. Built on a video database, each flag also carries a playable evidence clip for human review.

**Can AI fully automate content moderation?**
No. Production systems use ML-first triage with humans reviewing the flagged 1–5% of volume ([AWS Rekognition docs](https://docs.aws.amazon.com/rekognition/latest/dg/moderation.html)), because context-dependent categories — satire, news, medical content — resist full automation. Design the pipeline around the review queue, not instead of it.

**How does profanity detection work on video?**
The audio is indexed as time-aligned spoken words, then searched — semantically, not just by wordlist — for profanity, threats, and harassment. Each hit returns the timestamp and surrounding speech, and a padded evidence clip is materialized for review.

**How do you moderate live streams?**
Point the same index types at the stream: RTStream ingests RTMP/RTSP feeds, runs speech and visual policy indexes continuously, and fires webhook alerts with sub-second latency, tested at 1,000+ concurrent feeds ([videodb.io](https://videodb.io)).

**Can I use my own moderation model?**
Yes. Intelligence is pluggable: your classifier wraps as an index alongside the built-in layers, and your model IP is not exposed — the pattern proprietary-CV teams like Voxel use on the same platform ([videodb.io](https://videodb.io)).

### Moderation is a data problem with a human at the end

A video moderation pipeline is three index layers — speech, visuals, on-screen text — plus a review queue where every flag is a playable moment. Build it on infrastructure that treats live and recorded the same, and re-screen history whenever policy changes. To see is to know. [Read the docs →][cta]

## Sources

- VideoDB — https://videodb.io
- VideoDB Documentation — https://docs.videodb.io
- Amazon Rekognition: Moderating content — https://docs.aws.amazon.com/rekognition/latest/dg/moderation.html
- A Holistic Approach to Undesired Content Detection in the Real World (arXiv:2208.03274) — https://arxiv.org/abs/2208.03274
- OCR Benchmark: VLMs vs. traditional OCR on video — https://github.com/video-db/ocr-benchmark
- Director: agent framework and editing SDK — https://github.com/video-db/Director
- Video Understanding with Large Language Models: A Survey (arXiv:2312.17432) — https://arxiv.org/abs/2312.17432

[cta]: https://docs.videodb.io
[internal-hub]: /blog/what-is-video-infrastructure-for-ai-agents
[internal-ocr]: /blog/extract-text-from-video-ocr
[internal-live]: /blog/live-camera-intelligence
