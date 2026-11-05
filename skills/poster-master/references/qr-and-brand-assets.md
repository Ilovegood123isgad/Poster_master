# QR Codes and Brand Assets

Read before a QR code or a logo enters the layout. Both are high-risk assets: a QR that fails
is invisible until the viewer tries, and a broken wordmark is permanent.

## QR codes

**A QR code is never redrawn, AI-generated, stylised beyond legibility, or eyeballed.** It is
decoded, confirmed, regenerated, and tested.

### What to ask the client for

1. The final URL / group link / contact target — the authoritative value.
2. The original QR file or a clean screenshot (not a chat forward, not a photo of a screen).
3. Where the screenshot came from and when it was taken, so compression can be judged.
4. Whether the link stays valid for the whole publication period, and whether it requires
   login, a specific region, or a specific app.
5. Whether the code may be recoloured, have a logo overlaid, or be rounded.

### Extraction from a screenshot

1. **Protect the original.** Copy it to a read-only master. Keep the PNG or the original
   album file with its metadata. Never re-send it through a chat app first — that is what
   destroys the module edges.
2. **Locate the code.** Use a QR detector to find the three finder patterns and the outer
   contour, then confirm by eye that the detection did not latch onto an avatar, a group
   name, a bubble border, or a sticker.
3. **Perspective-correct and crop.** If the code was photographed or tilted, transform the
   four corners into a square. Do not crop into the quiet zone. Never content-aware-fill,
   AI-repair, or filter the modules.
4. **Decode with at least two independent decoders** — for example OpenCV
   `QRCodeDetector` and a ZXing / ZBar / browser-side decoder. Record the input
   file, the crop coordinates, whether perspective correction was applied, the result, and the
   failure reason.
5. **Compare with the client's link character by character** — protocol, domain, path,
   parameters, and case. "It opens" is not confirmation; a group QR may be expired or
   permission-limited.
6. **Regenerate a clean asset** from the confirmed link as SVG or high-quality PNG, and
   record the error-correction level, the colours, the logo overlay, and the size.
7. **Test before publication** — at least two different phones, the real viewing distance,
   the real brightness. For print or LED, test at the actual size on the actual medium.

### Design constraints

- Keep the full quiet zone and strong contrast. No background graphic may pass through the
  modules.
- Never stretch the code into a non-proportional rectangle, and never turn the modules into
  a decorative texture.
- **Every module must land on whole pixels.** A code scaled to an arbitrary size gets uneven
  modules, and an uneven code is the usual reason a perfectly good QR stops decoding once it
  is placed in a poster. Generate the code at its final pixel size, or at an integer multiple
  of it, and never resample it with smoothing. When a source file must be scaled into a
  layout, mark the element `"resample": "nearest"`.
- **Give the code room to be read.** As a working minimum: at least 3 px per module in a
  digital file (so roughly 150 px for a common version-3/4 code with its quiet zone), and at
  least 25 mm on a printed piece. When the code is the main call to action, make it larger
  than the minimum and keep the instruction text next to it.
- Confirm the error-correction level before recolouring, overlaying a logo, or rounding.
- Put a clear instruction next to it: "扫码进群", "扫码报名", "查看详情".
- No test codes, no personal temporary links, no expired group codes in a final file.
- If the code is blurred, obstructed, or decodes inconsistently, stop: ask for the link or a
  fresh export.

Machine checks confirm that a code decodes; they cannot confirm that a person standing in
front of the poster can find it and scan it in time. Both have to pass.

### Test record

| Field | Value |
|---|---|
| Original file | |
| Source and size | |
| Crop and correction | |
| Decoder and version | |
| Decoded result | |
| Client-confirmed link | |
| Regenerated file | |
| Device / distance / light | |
| Failures observed | |
| Reviewer and date | |

## Logos and brand assets

### What to request

1. **Vector source** — SVG, EPS, AI, or PDF. Ask for the font-outlined version if the logo
   is type-based.
2. **Transparent PNG** at high resolution as a fallback, at the intended final width.
3. **The brand guide** — clear space, minimum size, permitted combinations, background
   restrictions, colour values, and the version of the guide.
4. **Do-not-modify list** — the parts that may never be redrawn, recoloured, rotated, or
   restyled.

### Rules

- A logo is placed, never redrawn. Never trace it from a screenshot, never rebuild it in a
  text box, never recolour it outside the brand rules, and never stretch it.
- Respect the clear space and the minimum size on the actual carrier. A wordmark on a
  600 mm board is a different artefact from the same wordmark on a phone screen.
- If only a low-resolution raster logo exists, either ask for the source or place it small
  enough to stay crisp, and record the limitation.
- Brand colours are specified in the guide; the poster's palette is built around them, not
  the other way round.

## Fonts

- Record the font family, the exact weight used, the licence, and whether it may be embedded
  or must be outlined for this delivery.
- A font that cannot be embedded or licensed for this use is not an option, however well it
  matches the direction.
- Never send a file that depends on a font the recipient may not have. Outline or embed per
  the delivery spec.
- When a client supplies "our brand font", confirm they have the right to license it for
  this use — a brand's internal font is often licensed only for that organisation.
- Check the CJK and Latin faces together; the Latin default silently substitutes and breaks
  the type system.

