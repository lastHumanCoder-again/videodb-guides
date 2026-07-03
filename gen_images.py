#!/usr/bin/env python3
"""Generate VideoDB blog hero images via kie.ai nano-banana-pro.

Reads prompts from image_prompts/<slug>.txt, generates one 16:9 image each,
downloads to _incoming_assets/<slug>.jpg (build_html.py auto-uses it as the hero).

Uses curl (not urllib) deliberately — kie.ai's WAF blocks Python's urllib
(convention from theAIVideo-Studio/videodb-video-studio/scripts/gen_image.py).

Usage:
  export KIE_API_KEY=...
  python3 gen_images.py               # generate for every prompt missing an image
  python3 gen_images.py slug1 slug2   # only these slugs (force re-gen)
"""
import os, sys, time, json, re, pathlib, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = pathlib.Path(__file__).resolve().parent
PROMPTS = ROOT / "image_prompts"; INCOMING = ROOT / "_incoming_assets"
INCOMING.mkdir(exist_ok=True)
API = "https://api.kie.ai/api/v1/jobs"
KEY = os.environ.get("KIE_API_KEY", "").strip()

def curl(args, timeout=90):
    raw = subprocess.check_output(["curl", "-s", "-H", f"Authorization: Bearer {KEY}"] + args, timeout=timeout)
    return json.loads(raw)

def create(prompt):
    d = curl(["-X", "POST", f"{API}/createTask", "-H", "Content-Type: application/json",
              "-d", json.dumps({"model": "nano-banana-pro",
                                "input": {"prompt": prompt, "aspectRatio": "16:9",
                                          "resolution": "2K", "output_format": "jpg"}})])
    data = d.get("data") or {}
    tid = data.get("taskId") or data.get("task_id")
    if not tid: raise RuntimeError(f"createTask failed: {json.dumps(d)[:200]}")
    return tid

def find_url(blob):
    m = re.findall(r'https?://[^\s"\\]+\.(?:jpe?g|png|webp)', json.dumps(blob), re.I)
    return m[0] if m else None

def poll(tid, timeout=300):
    t0 = time.time()
    while time.time() - t0 < timeout:
        d = curl([f"{API}/recordInfo?taskId={tid}"])
        data = d.get("data", d)
        rj = data.get("resultJson")
        if isinstance(rj, str):
            try: data["_rj"] = json.loads(rj)
            except Exception: pass
        state = str(data.get("state") or data.get("status") or "").lower()
        if state in ("success", "succeeded", "completed", "done"):
            return find_url(data)
        if state in ("fail", "failed", "error"):
            raise RuntimeError(f"task failed: {json.dumps(data)[:200]}")
        time.sleep(5)
    raise TimeoutError(f"timed out polling {tid}")

def one(p, force):
    slug = p.stem
    dest = INCOMING / f"{slug}.jpg"
    if dest.exists() and not force:
        return ("skip", slug)
    prompt = p.read_text().strip()
    last = "?"
    for attempt in range(1, 4):
        try:
            url = poll(create(prompt))
            if not url: raise RuntimeError("no image url in result")
            subprocess.check_call(["curl", "-s", "-L", "-o", str(dest), url])
            if dest.stat().st_size < 20_000: raise RuntimeError("download too small")
            return ("done", slug)
        except Exception as e:
            last = str(e)[:90]
            time.sleep(10 * attempt)
    return ("fail", f"{slug}: {last}")

def main():
    if not KEY:
        sys.exit("ERROR: set KIE_API_KEY env var first.")
    only = set(sys.argv[1:])
    prompts = sorted(PROMPTS.glob("*.txt"))
    if only: prompts = [p for p in prompts if p.stem in only]
    done = fail = skip = 0
    with ThreadPoolExecutor(max_workers=int(os.environ.get("GEN_CONCURRENCY", "5"))) as ex:
        futs = {ex.submit(one, p, bool(only)): p.stem for p in prompts}
        for f in as_completed(futs):
            status, msg = f.result()
            if status == "done": print(f"  ✓ {msg}"); done += 1
            elif status == "skip": print(f"  · {msg}: exists"); skip += 1
            else: print(f"  ✗ {msg}"); fail += 1
    print(f"\nDone. generated={done} skipped={skip} failed={fail}")

if __name__ == "__main__":
    main()
