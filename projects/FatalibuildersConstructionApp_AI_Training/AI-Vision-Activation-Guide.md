# AI Vision & Render Activation Guide — Fatalibuilders Construction App

**For:** Eng Ali Ahmed · **Created:** 2026-08-16
**Status:** Both AI features are **built, tested, and pushed** (app repo
`fatalibuilders-cloud/fatalibuilders-app` @ main). They follow the same
**mock-until-keys** pattern as payments: the app works fully without any key
(deterministic extraction + schematic render), and switches to the real AI the
moment you add the keys below. This guide is the step-by-step to switch them on.

> **Security:** No API keys are written anywhere in this repository. They live
> only in the app's environment variables (Vercel → Settings → Environment
> Variables) — never in chat, never in files, never committed to git.

---

## What the two AI features do

1. **AI vision read of drawings** (`VISION_API_*`) — on **📐 Analyze drawings**,
   when a buyer uploads a **PDF or image**, the app rasterizes the first page and
   asks a vision model to *suggest* the footprint, floor count and room list. Shown
   as a separate **"🤖 AI suggestion — verify"** block the buyer confirms before
   applying. Without the key, PDFs still get deterministic **text + dimension**
   extraction; DXF/IFC always give exact quantities with or without AI.

2. **AI concept render** (`IMAGE_API_*`) — turns a project into a
   photoreal-*style* exterior image. Without the key, the app returns the
   schematic massing render instead. Illustrative concept, never the final design.

Both are **paid features** (lifetime access) and both are **optional** — set one,
both, or neither.

---

## What's already built (so you know what "on" means)

- **`src/lib/drawing-vision.ts`** — `visionConfigured()`, `rasterizeForVision()`
  (mupdf WASM for PDF, sharp for images), `suggestFromDrawing()` (OpenAI-compatible
  vision chat call), `parseVisionSuggestion()` (strict JSON, bounded values).
- **`src/lib/render-ai.ts`** — `aiRenderConfigured()`, `generateRender()` (image
  API when configured, schematic fallback otherwise).
- Wired into **`/api/projects/[id]/analyze-drawing`** (vision) and
  **`/api/projects/[id]/render-ai`** (render); both fall back safely if the key is
  missing or the provider errors.
- Tests: vision JSON parsing/bounding + PDF rasterization; render fallback. Full
  suite **224 passing**.

---

## Step-by-step activation

### 1. Get an API key
- **OpenAI** is the simplest match (the app speaks the OpenAI-compatible format):
  sign up at **https://platform.openai.com**, add billing, create an API key under
  **API keys**. The *same key* works for both vision and image generation.
- Any OpenAI-compatible endpoint works too (Azure OpenAI, OpenRouter, a local
  gateway) — just point the `*_URL` at that endpoint and use its key/model names.

### 2. Set the environment variables (Vercel → Settings → Environment Variables)

**For AI drawing reading (vision):**
```
VISION_API_URL=https://api.openai.com/v1/chat/completions
VISION_API_KEY=sk-...            # your OpenAI (or compatible) key
VISION_API_MODEL=gpt-4o-mini     # any vision-capable model; gpt-4o for best accuracy
```

**For AI concept renders (image generation):**
```
IMAGE_API_URL=https://api.openai.com/v1/images/generations
IMAGE_API_KEY=sk-...             # can be the SAME key as above
IMAGE_API_MODEL=gpt-image-1      # or dall-e-3
IMAGE_API_SIZE=1024x1024
IMAGE_API_RESPONSE_FORMAT=       # leave blank for gpt-image-1; set b64_json for dall-e-3
```
Redeploy so the app picks them up.

### 3. Test
- **Vision:** open a project → **📐 Analyze drawings** → upload a PDF plan. You
  should see the purple **"🤖 AI reading — suggestion"** block with a suggested
  size/floors/rooms and an **Apply AI suggestion** button.
- **Render:** on a paid project, open the drawings/render view (or Analyze
  drawings) — the render should now be a photoreal-style image labelled "AI
  concept render" instead of the schematic massing.
- If a key is wrong or the provider errors, the app **quietly falls back** to the
  deterministic/schematic path (check Vercel logs for the error line).

---

## Cost notes (indicative — confirm current provider pricing)

Pricing changes; treat these as ballpark and check the provider's live rates.

- **Vision (`gpt-4o-mini`)** — reading one rasterized drawing page is roughly a
  fraction of a US cent to ~1–2 cents, depending on image detail/tokens. Cheap
  enough to run per upload. `gpt-4o` is more accurate but several times pricier.
- **Image generation (`gpt-image-1` / `dall-e-3`)** — on the order of **~US$0.04
  per 1024×1024 image** at standard quality. This runs once per render.
- **Control spend:** three layers protect the bill:
  1. Both features are **paywalled** — only lifetime buyers can call them.
  2. A built-in **per-user daily cap** (default **25 AI reads + 25 renders per user
     per day**), set in Vercel env:
     ```
     AI_VISION_DAILY_LIMIT=25   # AI drawing reads / user / day (0 = unlimited)
     AI_RENDER_DAILY_LIMIT=25   # AI renders / user / day (0 = unlimited)
     AI_DAILY_LIMIT=            # optional fallback for both
     ```
     Over the cap, the app quietly returns the free schematic render / skips the AI
     read (the deterministic DXF/IFC/PDF extraction still runs) — no error, no spend.
  3. Your **provider spend cap** in the OpenAI dashboard as the hard backstop.

---

## Honesty caveats (kept in the product on purpose)

- The vision output is an **AI suggestion to confirm**, not a measured take-off.
  Real auto-quantities come from **DXF (AutoCAD)** and **IFC (Revit)** exports; PDF
  is read for text/suggestions; **DWG/RVT** must be exported to DXF/IFC first.
- The render is an **illustrative concept**, not the buyer's final or to-scale
  design — a licensed architect still designs the real thing.
- Every extracted/suggested figure stays labelled **"indicative — verify with a
  licensed QS/engineer."** The printed BOQ numbers still depend on validating the
  rate card once with a QS.

---

*App integration: `src/lib/drawing-vision.ts`, `src/lib/render-ai.ts`,
`src/app/api/projects/[id]/analyze-drawing/`, `src/app/api/projects/[id]/render-ai/`
— in `fatalibuilders-cloud/fatalibuilders-app`. Env template: `.env.example`.*
