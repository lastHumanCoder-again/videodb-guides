<!--
- Primary keyword: semantic video search   (20/mo · KD 0)
- Secondary keywords: ai video search (260/mo · KD 23) · video search engine (2,400/mo · KD 35)
- SEO title (<=60 chars): Semantic Video Search vs. Keyword Search, Explained
- URL slug: semantic-video-search-vs-keyword-search
- Meta description (150–160 chars): Semantic video search finds meaning; keyword search finds exact words. How embeddings and scene indexes work, why every hit should be a playable moment.
- Eyebrow: Build vs. buy
- Read time: 8 min read
- CTA stage: console
-->

# Semantic video search vs. keyword search: which one finds the moment?

*For developers deciding how search should work in a video product — and why the answer is usually "both, returning playable moments."*

**Semantic video search** retrieves moments by meaning: a query like "customer gets frustrated about pricing" finds the scene even if nobody in it says those words. Keyword search retrieves moments by exact text match against a transcript. They fail in opposite ways, they're built from different primitives — embeddings and scene indexes versus transcript grep — and a serious video search engine needs both. This piece defines each, shows how semantic search over video actually works, and makes one argument that matters more than either: a search hit should be a playable moment, not a timestamp.

## What is keyword search over video?

Keyword search over video is text search against a transcript. Speech is transcribed, the transcript is indexed with the string and inverted-index techniques search engines have used for decades, and a query matches where the exact words (or close variants) appear.

Classic lexical methods score documents by surface overlap — shared words and word frequencies, in the style of TF-IDF and its successors. That gives keyword search its two defining properties. It is *precise*: searching a 4-hour deposition for "exhibit 14" finds exactly the utterances of "exhibit 14," which is what a legal team wants. And it is *literal*: it knows nothing about meaning, so "two sentences that share nothing but words like 'the', 'a', 'is'" can score as similar while true paraphrases score as unrelated ([Pinecone, semantic search](https://www.pinecone.io/learn/semantic-search/)). Search "budget concerns" and the moment where someone says "we can't afford this" is invisible.

The deeper limitation is scope: a transcript only encodes what was *said*. The whiteboard diagram, the product on screen, the moment a demo visibly crashes — none of it exists in a transcript, so no amount of keyword cleverness can find it.

## What is semantic video search?

Semantic video search matches the *meaning* of a query against the *content* of the video — spoken and visual — rather than matching strings. It's the technology behind most things marketed as AI video search: describe the moment in your own words, get the moment back.

Two research results made this practical. Sentence-embedding models like SBERT showed that text with "essentially identical meaning whilst not sharing any of the same keywords" can be matched reliably by comparing dense vectors ([Reimers & Gurevych, 2019](https://arxiv.org/abs/1908.10084)). And CLIP showed that images and natural language can be embedded into a shared space, so a sentence can retrieve a picture ([Radford et al., 2021](https://arxiv.org/abs/2103.00020)). Put together: both the query and every scene in a video can become vectors, and "which moment is closest in meaning?" becomes a nearest-neighbor lookup.

Semantic search inverts keyword search's failure modes. It finds paraphrases and visual content effortlessly, but it's weaker at exact strings — a specific SKU, a person's name, "exhibit 14." That's why the honest answer is both, composed.

> **Your users describe moments; they don't quote transcripts.** Ship search that understands both in one SDK. [Try VideoDB free →][cta]

## How does semantic search over video work?

The pipeline is: structure the video into moments, describe and embed each moment, then answer queries with vector similarity. In VideoDB's model this happens through indexes — reusable, additive layers over the media ([VideoDB docs](https://docs.videodb.io)).

Concretely, four stages:

1. **Segment.** The continuous stream is cut into scenes — coherent spans of seconds, not whole files. The unit is the moment, not the file.
2. **Describe.** Each scene is described across modalities: the transcript of what's said, plus a vision model's account of what's visible. VideoDB is bring-your-own-model here — Twelve Labs, Gemini, OpenAI, Anthropic, or your own model wraps as the scene index ([videodb.io](https://videodb.io)).
3. **Embed.** Scene descriptions and transcript segments become dense vectors, the semantic layer alongside the keyword layer.
4. **Retrieve.** A query is embedded and compared by cosine similarity — smaller angle between vectors, closer meaning ([Pinecone](https://www.pinecone.io/learn/semantic-search/)) — with approximate-nearest-neighbor indexes keeping lookups sub-second at archive scale.

Keyword search, by contrast, needs only stage 1's transcript and an inverted index. That's why it's cheap — and why it's blind to everything visual. If you're building the surrounding stack yourself, this is the point where the frankenstack appears: transcription, a vision model, an embedding model, a vector database, and glue. That build-versus-buy trade is the subject of the hub piece on [video infrastructure for AI agents ↗][internal-hub], and the retrieval pattern on top of it is [video RAG ↗][internal-video-rag].

## Why should a hit be a playable moment, not a timestamp?

Because a timestamp is homework, not an answer. When search returns `{"video_id": "v-829", "t": 3417}`, a human still has to open the file and scrub, and an AI agent has to orchestrate download, seek, and clip extraction before it can *do* anything — summarize, verify, publish, alert.

The alternative is search that materializes results: every hit resolves to a playable clip, streamable immediately. In VideoDB, search returns moments that compile straight to a stream — retrieval runs in **~120ms across petabyte-scale archives, roughly 100× faster** than a conventional pipeline that searches an index, seeks into storage, and cuts a clip on demand ([videodb.io](https://videodb.io)). The open-source [StreamRAG](https://github.com/video-db/StreamRAG) agent is a working example: query in, watchable stream out, no intermediate plumbing.

![Bar chart comparing time from query to playable moment: conventional pipeline versus VideoDB semantic search](moment-retrieval-latency.svg)
*From query to a watchable clip: a stitched search-seek-cut pipeline versus retrieval that materializes the moment. Source: videodb.io.*

> **Stop shipping timestamps.** Return moments your users can watch and your agents can act on, straight from the search call. [Get an API key →][cta]

## How do semantic and keyword video search compare?

Keyword search wins on exact strings and cost; semantic search wins on meaning and visual content; only moment-based retrieval makes either useful downstream. The table is the summary:

| | Keyword search | Semantic video search |
|---|---|---|
| Matches on | Exact words in the transcript | Meaning of speech *and* visuals |
| Query style | `"exhibit 14"` | "the moment the witness contradicts herself" |
| Finds visual moments | No — transcript-only | Yes — via scene indexes |
| Handles paraphrase | No | Yes |
| Exact names, SKUs, jargon | Excellent | Weaker — can blur specifics |
| Index cost | Low (transcription + inverted index) | Higher (scene descriptions + embeddings, one-time) |
| Failure mode | Misses everything not literally said | Occasionally retrieves look-alike moments |
| Best for | Compliance, legal, known-item lookup | Discovery, agents, natural-language product search |

The practical pattern in production: semantic search as the default path, keyword search as the precision path, and both returning the same currency — playable moments.

## How do you run both with the VideoDB SDK?

Both search types are one parameter apart in the VideoDB SDK (`pip install videodb`), and a scene index adds visual search on top ([VideoDB docs](https://docs.videodb.io)):

```python
import videodb
from videodb import SearchType, IndexType

conn = videodb.connect(api_key="YOUR_API_KEY")
coll = conn.get_collection()
video = coll.upload(url="https://example.com/all-hands.mp4")

# keyword search: exact words, needs a transcript index
video.index_spoken_words()
exact = video.search("quarterly roadmap", search_type=SearchType.keyword)

# semantic search: meaning, not spelling
sem = video.search("where do we discuss what ships next quarter?",
                   search_type=SearchType.semantic)

# scene search: what's visible, not what's said
video.index_scenes(prompt="Describe slides, demos, and speakers")
visual = video.search("the slide with the architecture diagram",
                      search_type=SearchType.scene, index_type=IndexType.scene)

sem.play()  # every result compiles to a playable stream
```

Indexes are additive and composable at query time, so adding scene search later doesn't disturb the transcript layer — and swapping the underlying model re-indexes the same media rather than rebuilding the pipeline. If your current plan is to call a vision model per query instead, the cost math in [frame-by-frame VLM calls vs. indexing once ↗][internal-frame-by-frame] is worth reading first.

> **One upload, three search types.** Transcript, semantic, and scene search on the same video, first query in about five minutes. [Start free in the console →][cta]

## Frequently asked questions

**What is semantic video search?**
Search that retrieves video moments by meaning rather than exact words. Queries and video scenes are embedded as vectors in a shared space; results are the scenes closest in meaning to the query — including visual moments no transcript contains.

**How is AI video search different from a video search engine like YouTube's?**
Platform search engines mostly rank whole videos by title, description, and engagement metadata. AI video search operates *inside* the footage: it indexes speech and scenes so a query resolves to the exact moment within a video, not to a watch page.

**Is semantic search always better than keyword search?**
No. Keyword search is more reliable for exact strings — names, part numbers, legal phrases — and cheaper to index. Semantic search is better for paraphrase, discovery, and visual content. Production systems compose both against the same media.

**Do I need a vector database to build semantic video search?**
If you build it yourself, yes — plus transcription, a vision model, an embedding model, and storage glue. A video database like VideoDB ships the embedding, indexing, and retrieval layers behind one API, with the model swappable.

**How fast can semantic video search be?**
Retrieval itself is a vector lookup and can be very fast: VideoDB serves results in ~120ms across petabyte-scale archives, with every hit materialized as a playable clip rather than a timestamp (videodb.io).

### The query is a sentence. The answer is a moment.

Keyword search tells you where words were said; semantic search understands what you meant; the system underneath decides whether the result is a timestamp to scrub or a clip to play. Index once, search both ways, return moments. [Try VideoDB free →][cta]

## Sources

- Pinecone — Semantic search (lexical vs. dense retrieval, cosine similarity) — https://www.pinecone.io/learn/semantic-search/
- Reimers & Gurevych — Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks — https://arxiv.org/abs/1908.10084
- Radford et al. — Learning Transferable Visual Models From Natural Language Supervision (CLIP) — https://arxiv.org/abs/2103.00020
- VideoDB (retrieval latency, bring-your-own-model, search stats) — https://videodb.io
- VideoDB documentation (index and search types) — https://docs.videodb.io
- StreamRAG — video search and streaming agent — https://github.com/video-db/StreamRAG

[cta]: https://console.videodb.io
[internal-hub]: /blog/what-is-video-infrastructure-for-ai-agents
[internal-video-rag]: /blog/what-is-video-rag
[internal-frame-by-frame]: /blog/videodb-vs-running-vlms-frame-by-frame
