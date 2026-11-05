# Compliance and Delivery

Read in stage 6, and at any moment a claim, a person, or a payment path appears in the copy.

## Sensitive categories

These need evidence, a disclaimer, or a review before delivery:

| Category | Why | What is needed |
|---|---|---|
| Health, medical, treatment | Harm | Evidence or a disclaimer; no disease or cure claims without a source |
| Finance, lending, investment | Financial harm | Terms, risk disclosure, and the correct licence |
| Food, supplements | Safety | Ingredient accuracy, allergen information, no unsubstantiated claims |
| Education, training, certification | Credential misrepresentation | Accurate accreditation and qualification claims |
| Safety, compliance, public warning | Public behaviour | Unambiguous instruction; correct standard references |
| Donation, fundraising | Trust and money | Transparent use of funds; the payment target verified |
| Children, minors | Protection | Guardian consent and age-appropriate treatment |
| Events with a capacity limit | Expectation | The real number and the real condition |
| Claims of statistics or data | Truth | The source of the figure, and its date |

## The four review gates

1. **Intake** — every asset and every fact has a recorded state.
2. **Rights** — every shipped asset has a licence, a release, or brand evidence.
3. **Fact** — every P0 fact and identity-bearing element is confirmed by the client.
4. **Delivery** — the files match the confirmed facts, and the ledger matches the files.

Each gate must be clear before the next begins. A gate that is "mostly clear" is not clear.

## The delivery checklist

Machine-checkable:

- [ ] Every output file opens.
- [ ] Pixel dimensions match the delivery list, exactly.
- [ ] Colour mode matches the carrier (RGB for screen, CMYK or supplier spec for print).
- [ ] Effective resolution at final physical size meets the carrier requirement.
- [ ] File naming matches the delivery list.
- [ ] The QR decodes in the exported file, where one is present.

Human-checkable:

- [ ] Read from the real viewing distance: the main title is the first thing seen.
- [ ] The smallest required text is legible at that distance.
- [ ] Every date, price, place, contact, and claim matches the confirmed copy sheet.
- [ ] The QR scans on at least two real phones, at the real distance, at the intended
      brightness.
- [ ] Fonts are licensed and embedded or outlined.
- [ ] Image licences, portrait releases, and brand evidence are on file.
- [ ] The print version was proofed on the actual substrate, or the screen version was
      checked on the actual screen.
- [ ] Nothing temporary survives in the file: no test code, no placeholder copy, no
      "待确认" text, no debug layer.
- [ ] The project folder contains the source, the exports, and the records.

## Naming

```text
<project>-<version>-<carrier>.<ext>
```

For example `骑行社团招新-v1-print-A2.png` or
`骑行社团招新-v2-social-3x4.png`. The name must let someone find the file without
opening it, and it must match the delivery list.

## Failure handling

| Failure | Where it is repaired | Never |
|---|---|---|
| Wrong date or price | The copy sheet, after client confirmation | Fix it in the layout only |
| QR does not decode | The QR asset, from the confirmed link | Darken it and hope |
| Logo distorted | The source asset | Rescale it again |
| Low-resolution image | The asset ledger — replace or re-shoot | Ship a blurred print |
| Unlicensed font | The type decision | Send it and note the risk |
| Cropped safe area | The layout | Ship it and let the printer complain |
| Text collision at final size | The layout | Shrink the type below legibility |

## Honest reporting

Report the delivery as it is:

- Say what was verified and how — "checked at 100% on a phone at 2 m, scanned on two
  devices".
- Say what was not verified — "the CMYK proof has not been printed yet".
- Say what is assumed — "the venue address was confirmed verbally; no written confirmation
  on file".
- Never describe a draft as final, a mock as a photograph, a plan as a build, or a model
  output as a photograph of a real thing.

