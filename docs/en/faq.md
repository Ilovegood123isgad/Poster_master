# FAQ

[中文](../faq.md) · [Docs index](README.md)

**Does it produce artwork on its own?**
Yes, but it passes the gates first. The default route asks the few questions that change the
design. Say "do not ask, just make it" and it takes the Quick profile: assumptions get labelled
and the delivery gate stays closed.

**Do I need the Python dependencies?**
Not to start. The editor and the scaffolder are pure Node standard library. Install
<code>requirements.txt</code> only when you use the rendering, delivery, PSD, QR or cutout scripts.

**Why can I not just use the client's QR image?**
Because it may be a screenshot with a cropped quiet zone, or it may point at an expired group.
The workflow decodes it, compares it character by character with the confirmed link, regenerates a
clean code, and tests it on a phone.

**The delivery check says "no QR code detected". Is that a failure?**
No, it is a warning. The script cannot know whether that file was supposed to contain a code. If
it should, then the code is missing and a human has to fix it.

**The delivery check says "QR graphic detected but not decodable".**
That is a failure. Common causes: modules not landing on whole pixels (regenerate at the final
size), an interpolated resize blurring the edges (use <code>"resample": "nearest"</code>), a
cropped quiet zone, weak contrast, or a code that is simply too small at delivery size (at least
3 px per module; roughly 150 px for a common code in a digital poster).

**Will the editor and the agent produce different results?**
No. Both render the same component source with the same rules for size, layering and type.
Only the interaction differs.

**Can I run a single stage?**
Yes — the deliver and revise routes can be entered directly. Whatever you skip must be reported
explicitly as unverified assumption.

**Can I use images found online?**
Yes, as long as the source and rights state are recorded in the asset ledger. An asset with an
unknown rights state never ships.

**Can I plug in our own image model?**
Generation is one step. What the skill defines is what happens after it: verify the facts (numbers,
prices, dates, slogans), check the fit with the existing layout, and register the result in the
asset ledger.

**Can it make posters in Chinese and English?**
Yes. The language follows the user and the source material. Font licensing still needs its own
check.

**Can I modify the skill?**
Yes — it is Markdown, JSON and scripts. Read
[Why it is built this way](why-poster-master.md) and [CONTRIBUTING.md](../../CONTRIBUTING.md) first.
