AI-Automated-Video-Gen 🎬🤖

Autonomous shorts creator that scrapes trending topics, writes a tight script, generates visuals + voice, assembles a vertical video, and uploads it to Cloudflare—hands-off.

Mode: Dynamic agent only (no static/series).

Stack: Flask backend • Pollinations (images) • ElevenLabs (TTS) • ffmpeg (assembly) • Cloudflare R2 (artifacts) • Postgres (state) • Akash (deploy scraper + backend on CPU).

Why this is different

Agentic, not just “prompt → video.” A planner decides when to scrape, how to dedupe topics, how many shots to use, whether the script is claimable and on-time, and when to publish.

Vendor-swap friendly. Start with Pollinations/ElevenLabs; later plug in your own Akash GPU services for /t2i or /i2v without changing the control plane.

Storage-first. Every artifact is private in R2; you share short-lived signed links only.

Architecture (current reality)

Flask Backend (control plane):
Single public API to kick off runs, stream progress, and expose signed URLs. Coordinates scraping, script/storyboard building, image + TTS calls, captioning, and ffmpeg assembly. Persists run state to Postgres.

Scraper (CPU microservice on Akash):
Fetches trending/news items from whitelisted sources, normalizes them, dedupes by URL/title/hash, and writes a compact facts JSON for the backend.

External AI services:

Pollinations for text-to-image (frames).

ElevenLabs for voiceover (narration).

Processing:
ffmpeg to stitch frames, transitions, narration, and captions into a vertical MP4.

Storage:
Cloudflare R2 for frames, audio, captions, and final video; all access via signed URLs only.

Database:
Postgres to track topics processed, run status/timings, dedupe keys, and cost counters.

Scheduler:
Simple cron/job runner that triggers the dynamic agent N times/day per category.

End-to-end flow

Scrape & select
Scraper pulls trending items for configured categories → filters by freshness window (e.g., last 24–48h), domain allowlist, and novelty (dedupe) → produces facts.json (title, summary, URL, timestamp, source).

Script
Backend converts facts into an 80–120 word voice script with a punchy hook, 3–5 beats, and an outro line.

Storyboard
Planner emits shots.json: 5–7 shots, on-screen text per beat, style preset, and which 1–2 shots get light emphasis (Ken Burns today; i2v later).

Media generation

Images: Pollinations → frame_1..N.png

Voice: ElevenLabs → narration.wav (+ char count for cost)

Captions
Build captions.srt aligned to narration (word/phrase timing from the script beats).

Assembly
ffmpeg composes vertical (720×1280 or 1080×1920), applies transitions, mixes narration (and optional BG music), burns captions if desired, exports final/video.mp4.

Upload & publish
Backend uploads artifacts to R2 and returns a signed URL to the final MP4. (Platform auto-publish can be toggled later.)

Configuration you actually need

Create environment variables (or a config file) for:

ElevenLabs: API key, default voice id, speed

Pollinations: base URL and any rate/backoff parameters

Cloudflare R2: account id, access key, secret key, bucket name, signed URL TTL

Postgres: connection URL

App: Flask secret, base URL, allowed origins, log level

Scraper policy: categories, freshness window (hours), domain allowlist, max items/run, max runs/day

Planner policy: target duration (e.g., 30–45s), number of shots (5–7), caption style, music on/off, failure fallbacks (e.g., drop music if mux fails)

Keep secrets server-side only. Do not expose keys in the browser.

What each run produces

facts.json (scraper output + references)

script.json (beats + timestamps)

shots.json (prompts, on-screen text, durations)

frame_i.png (Pollinations)

narration.wav (ElevenLabs)

captions.srt

final/video.mp4 (stored in R2, returned as a signed URL)

Local development checklist (no code here, just the order)

Set your environment variables (above).

Run the Flask backend locally and point it at your Postgres/R2.

Start the scraper locally and verify facts.json lands in R2 (or returns to backend).

Trigger a single dynamic run with one category and confirm: script → images → TTS → captions → ffmpeg → R2 signed URL.

Test rate limits: throttle Pollinations + ElevenLabs with backoff/retry and verify graceful degradation (e.g., fewer shots).

Turn on the scheduler for 1 run/day and verify automation.

Deployment on Akash (CPU-only to start)

Containers:

backend (Flask app + ffmpeg + R2 client)

scraper (lightweight Python job service)

Networking:
Expose only the backend’s HTTP port publicly; scraper can be private and talk to backend/storage.

State:
Use a managed Postgres (Neon/Supabase/RDS) so you don’t lose state when leases churn.

Storage:
Keep the R2 bucket private. Backend issues uploads/downloads via signed URLs.

Scheduling:
Easiest: cron inside scraper container or a small scheduler thread in backend. Safer: an external job runner that calls backend’s “start run” endpoint.

Observability:
Emit step events and durations; log vendor responses (status codes, ms, chars). Persist a run_audit.json per video with counts and costs.

Guardrails, costs & reality (brutally honest)

Pollinations: convenient but style can wander; use a prompt scaffold + consistent “style preset” and consider a seed to reduce jitter; expect occasional failures—retry with exponential backoff.

ElevenLabs: great quality; watch character quotas; cache intro/outro lines to save cost.

ffmpeg: most failures are from timing or audio mux; if assembly fails, retry without background music and with simpler transitions.

R2 egress: storage is cheap, egress isn’t—prefer signed links over public hosting; avoid re-downloading large assets during retries.

Akash GPUs: currently scarce—don’t block on them. Your path is correct: run scraper + backend on CPU now; swap Pollinations for your Akash /t2i when you land a GPU lease.

Operational policies that make it feel “agentic”

Freshness: ignore items older than your window (e.g., 36h).

Novelty: dedupe by URL + title hash; don’t cover the same topic twice within N days.

Quality gate: minimal source quality score per domain; auto-reject low-cred sites.

Time budget: if image or TTS stalls, drop to 5 shots and publish anyway.

Compliance: apply a safe-content filter on scraped text and prompts; show a compact “sources” overlay or description.

Roadmap (immediate next steps)

Today

Lock planner policy JSON (duration, shots, presets, fallback rules).

Finish scraper dedupe + allowlist and wire it to backend.

Add per-run cost chip (TTS chars, image calls, egress estimate).

Ship minimal status page that streams step updates and shows the final player via signed URL.

Next

Background music library + loudness normalization.

Thumbnail auto-gen.

Multi-category scheduling with concurrency caps.

Later (when GPUs free up)

Self-host /t2i on Akash; optional /i2v for 1–2 animated shots.

Auto-publish to YouTube/TikTok with rate guards.

