# Image Generation

Read this in stage 3, when the direction needs a key visual that no supplied asset can
provide, and in stage 4 before the first artwork exists.

The skill does not ship an API key and does not call any service until you configure one.
Generation is an optional step that the user turns on with their own account.

## Configure it once, with the user's own key

```bash
python "${SKILL_DIR}/scripts/setup_imagegen.py"
```

Three questions, in this order, because each decides the next:

| # | Ask for | Why it cannot be guessed |
|---|---|---|
| 1 | **base_url** | An OpenAI-compatible endpoint, usually ending in `/v1`. The official API is `https://api.openai.com/v1`; a relay (中转站) uses its own host. It is not derivable from the model name. |
| 2 | **api_key** | Entered at a hidden prompt. Stored at `~/.poster-master/imagegen.json`, never in a project folder, never in a chat message, never in a log. |
| 3 | **model** | Must be an image model that this endpoint actually serves. `--list-models` prints what it advertises. |

Then prove it without spending anything:

```bash
python "${SKILL_DIR}/scripts/setup_imagegen.py" --test
```

`--test` calls `GET /models` and lists the image models it finds. Use
`--test-generate` only when you are ready to pay for one real round trip.

Environment variables override the file, which is how a user switches providers per
shell: `POSTER_IMAGEGEN_API_KEY`, `POSTER_IMAGEGEN_BASE_URL`, `POSTER_IMAGEGEN_MODEL`.

**When the user has not configured a provider, do not improvise.** Say so, offer the
two alternatives below, and continue. Writing the key visual by hand in a script is the
last resort, not the default: in one real run it consumed about forty percent of the
total time and produced a subject that read as a bucket before it read as an island.

## Decide the source before deciding the treatment

| Situation | Best source | Why |
|---|---|---|
| The client supplied a usable photo or illustration | the supplied asset | it is a fact, and facts are never regenerated |
| The client supplied something usable after cleanup | processed asset | cutout, retouch, extension |
| No asset exists and the subject is atmosphere | **generate** | background, lighting, texture, mood, abstract scene |
| No asset exists and the subject is a fact | photograph it, or commission it | a product, a person, a venue |
| The subject is a concept with no object | generate, then check it still signals the category | abstract work must still say what it is |

## What may be generated

| May be generated | May not be generated |
|---|---|
| Backgrounds, atmosphere, abstract shapes, patterns, light | Logos, brand marks, wordmarks,校徽 |
| Non-branded props, scenery, generic figures when no real person is involved | Packaging text, ingredient lists, prices, certification marks |
| Colour fields, textures, gradients | A specific real person's likeness |
| Illustration styles named in the direction sheet | A product's factual structure or features |

Deciding this is `asset-processing.md`'s job, not a matter of taste. If the entry is in
the right-hand column, generation is the wrong tool and the direction has to change.

## Writing the prompt

The prompt describes a **picture**, not a poster. Everything that must be readable is set
in type later, by the component source, where it stays editable and provable.

1. **Subject and action** — what is in frame and what it is doing.
2. **Composition** — where the subject sits, how much empty space remains, where the
   type will go. Ask for the negative space explicitly; a full-bleed subject leaves the
   layout nowhere to live.
3. **Style** — the four decisions from the direction sheet: structure, image language,
   colour behaviour, type voice (type voice is carried by the layout, so mention only the
   first three).
4. **Colour** — the actual hex-adjacent words from the palette, plus what must not appear.
5. **Boundary** — "no text, no logo, no watermark" belongs in almost every prompt. Text
   that the model invents cannot be verified and cannot be corrected.
6. **Aspect and crop** — ask for the frame you will actually use, and leave room for the
   carrier's crop and safe area.

Keep it short. A prompt longer than five sentences is usually several prompts that have
not been separated yet.

## Size, resolution and what generation cannot fix

Image models return a fixed set of pixel sizes. A generated asset is therefore almost
never the final print resolution: a 1536 px wide generation placed across a 3508 px wide
A3 is being upscaled 2.3×.

| Carrier | Asset needed at final size | Consequence |
|---|---|---|
| Screen 1080 wide | 1080–2160 | generated size is often enough |
| A3 print at 300 dpi | 3508 × 4961 | generate the largest size offered, then check sharpness at 100 % |
| A2 or larger | 4961 px and up | generation is a composition guide, not the final asset |

Rules that follow:

- Generate the largest size the model offers, then judge it at the final size, not in a
  thumbnail.
- Never upscale a generated image and call it print resolution. If it cannot hold 300 dpi
  at final size, either the layout changes or the asset is replaced.
- Generated imagery is an asset with a licence state. Record the service, the model, and
  the date, and check the provider's commercial-use terms before delivery.

## Every generation is recorded

`generate_artwork.py` writes a `.json` sidecar next to the image and prints a row ready
for `templates/素材台账.md`:

```bash
python "${SKILL_DIR}/scripts/generate_artwork.py" \
    --prompt "深空中的悬浮岛，扁平矢量，薄荷色顶面与深青岩体，四周留出白场" \
    --size 1536x1024 --output assets/主视觉.png
```

The row records the model, the prompt, the size, and the date. An unrecorded generation
is not usable in a deliverable, for the same reason an unlicensed photograph is not.

## Acceptance checklist

Nothing here is a matter of taste. Each item fails a real delivery when skipped.

- [ ] The generated part is atmosphere, not a fact.
- [ ] No text, no logo, no watermark, no invented packaging lettering.
- [ ] No real person's likeness was generated.
- [ ] The subject is recognisable at thumbnail size and at the final size.
- [ ] Negative space exists where the copy will sit.
- [ ] The asset survives a 100 % crop at final size without looking upscaled.
- [ ] The palette matches the direction sheet, or the direction sheet is updated.
- [ ] The generation is recorded in the asset ledger with model, prompt and date.
- [ ] Commercial use is permitted by the provider's terms.
