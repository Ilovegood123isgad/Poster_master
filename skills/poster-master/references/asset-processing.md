# Asset Processing and Generation

Read before cutting out, retouching, extending, or generating any imagery. The rule that
matters: **the fact survives, the atmosphere does not.**

## Fact subjects vs atmosphere subjects

| Category | What is in it | Rule |
|---|---|---|
| **Fact subject** | A person's face and identity, product appearance, packaging text, model numbers, quantity, certification marks, venue signage, logos | Never restyled, regenerated, or "improved". Retouch only what does not change the fact, and only with approval. |
| **Atmosphere subject** | Background, lighting, material texture, decorative patterns, abstract surroundings | May be art-directed within the agreed boundary |

## Person imagery

Before processing, record:

- The person's identity, and whether they are an employee, a client, a minor, or a public
  figure.
- Whether a portrait release exists, and its scope: this project, these channels, this term.
- Which features must survive exactly: face, hairstyle, clothing, posture, held objects.

Never substitute an unauthorised portrait with a generated lookalike, and never change a
person's apparent age or identity.

### Cutout and repair order

1. Choose the highest-resolution original with natural light and complete edges. A phone
   screenshot has already lost information that no tool can restore — treat it as a
   high-risk input, not a formality.
2. Segment the subject first; then handle hair, transparent clothing, fingers, and small
   edges separately.
3. Repair only dust, light noise, and background bleed-through. Never change face shape,
   body shape, clothing facts, or brand marks.
4. Export a transparent PNG **and keep the mask or path** so the cutout stays editable.
5. After compositing, check foot contact, perspective, light direction, colour temperature,
   shadow, and subject scale. A pasted subject that does not share the scene's light reads as
   a sticker.

### Model and tool reality

Local ONNX background removal (RMBG, BiRefNet via rembg) is good enough for a **first
pass**, not for a final cutout. Observed behaviour on the project's brand poster: the model
preserved the model's proportions and face, kept one side of the curly hair reasonably, but
retained dark clothing from the original scene as foreground.

Rules that follow from that:

- "The model ran successfully" is not "the cutout is accepted". Acceptance is judged on the
  hair outline, the gaps between strands, the shoulder and clothing edge, the arm outline,
  the white halo on transparent edges, and whether the proportions changed.
- Never hide a failed cutout with more smoke, more shadow bands, or a tighter crop. That
  defers the defect; it does not fix it.
- If the cutout cannot reach an acceptable standard, the alternatives are the manual path
  (a human in Photopea, GIMP, Krita, or CapCut) or an editorial-photography treatment that
  keeps the original scene instead of faking a new one.
- Uploading an authorised model photo to a third-party cutout service is a privacy and cost
  decision. Ask before sending, not after.

## Product and object imagery

### Must stay accurate

Model number, colour, packaging front and back, capacity, ingredients, price, certification
marks, printed text, structure, quantity, ports, buttons, texture, brand logo, and the
client-specified viewing angle.

### May be requested and applied

Cutout, dust removal, minor scratch repair, colour-temperature unification, exposure
adjustment, background extension, adding a shadow that matches the real light direction,
replacing a non-factual background, and slight perspective correction.

### Never done by default

- AI rewriting or redrawing packaging text, ingredients, price, or certification.
- Adding quantity, accessories, effects, or functions the product does not have.
- Presenting a generated product image as proof of the real product.
- Warping a logo, trademark, or package letterform until it cannot be checked.
- Perspective correction that makes the product look bigger, thinner, brighter, or different.

## Building a composed key visual

Layer in this order. Flattening everything into one image destroys the separation that lets
you revise:

1. **Propagation subject** — the person or product that carries the theme.
2. **Spatial relationship** — ground, wall, table, or scene; it sets scale and position.
3. **Light relationship** — one main light direction, contact shadows, environment colour.
4. **Brand layer** — logo, brand colour, typography, graphic language.
5. **Mood layer** — texture, particles, colour blocks, illustration, generated atmosphere.
6. **Information layer** — title, benefits, time, CTA, QR.

## Generation boundary

State the boundary in the direction sheet, before generating anything.

| May be generated | May not be generated |
|---|---|
| Backgrounds, atmosphere, abstract shapes, patterns | Logos, brand marks, wordmarks |
| Non-branded props, scenery, lighting | Packaging text, ingredient lists, prices, certification marks |
| Generic human figures when no real person is involved | A specific real person's likeness |
| Colour fields, textures, gradients | A product's factual structure or features |

Everything generated is recorded: the tool, the model, the prompt, the date, the reviewer, and
the version. A generated image is an asset with a licence state like any other — record it in
the ledger.

## Composition acceptance

- No white or black halo, no visible gap in the cutout.
- Subject scale is plausible for the scene; perspective lines agree.
- Light direction, shadow softness, and colour temperature are consistent.
- Product text, faces, and logos survive magnification.
- Decoration does not cover factual information, the QR quiet zone, or brand clear space.
- Generated parts are on separate layers and remain traceable to their source and edit scope.
- If the original could not reach the target size, the client was told before delivery and
  chose between repair, re-shoot, or a different asset.

