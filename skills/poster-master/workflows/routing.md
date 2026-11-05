# Routing

Read after `SKILL.md`. Select exactly one top-level route and, when the route offers
profiles, exactly one profile. Do not ask the user to choose a route when the signals below
already resolve it.

## Decision order

1. **Existing artefact?** If the request points at a poster file, a component source, a project
   folder, or a version number, the route is decided by what the user wants done with it
   (table below).
2. **No artefact?** The route is *Create a new poster*. Pick the profile by whether the user
   asked to skip the confirmation round trip.
3. **Ambiguous?** Resolve with the smallest question that changes the route. If a wrong guess
   only affects a later, reversible step, proceed and state the assumption.

## Signals

| The request says | Route | Runtime authority |
|---|---|---|
| "make / design / create a poster about …" | Create a new poster | `new-poster.md` |
| "quickly mock this up, don't ask me" | Create a new poster — Quick | `new-poster.md` §Quick |
| "change the headline / swap the photo / fix the layout" | Revise an existing poster | `revise-poster.md` |
| "open it in the editor, let me tweak the layers" | Refine in the component editor | `editor-refine.md` |
| "export / adapt for A4, Xiaohongshu, WeChat / check the delivery" | Adapt, export, and deliver | `deliver.md` |

## Route prerequisites

| Route | Prerequisite | If missing |
|---|---|---|
| Create a new poster | A subject, a purpose, or an audience — however vague | Ask for the subject and who it is for. Do not start a generic poster. |
| Revise an existing poster | The artefact itself (file path or project folder) | Ask for the path. Do not regenerate from a description of a poster. |
| Refine in the component editor | A component source file, or artwork convertible into one | Offer the editor route only after a component source exists |
| Adapt, export, and deliver | At least one artwork file and the target channel list | Ask for the file and the channels; sizes are not guessed silently |

## Route boundaries

- **Create** ends at a delivered poster. Do not switch to Revise to fix a detail — fix it
  inside Create.
- **Revise** changes an existing artefact and re-issues the same deliverable set. A revision
  that changes the channel or the size is **Deliver**, not Revise.
- **Editor refine** is a way of executing part of Revise or Create, not a third opinion about
  the design. Direction changes made in the editor still follow the direction gate in
  `new-poster.md` stage 3.
- **Deliver** may be entered directly from Create or Revise at stage 6.

## Profile selection within Create

The default profile is **Default**: stage 1 and stage 2 end at a user gate where the brief and
the copy set are confirmed before artwork begins.

Select **Quick** only when the request explicitly says to skip confirmation, to work
autonomously, or to produce a first draft immediately. Quick removes the confirmation gate
but never removes the delivery gate, the compliance rules, or the requirement to label
unconfirmed facts as unconfirmed.

