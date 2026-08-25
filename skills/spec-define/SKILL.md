---
name: spec-define
description: Use when the user wants to define a spec, write a spec, capture requirements, or describes a feature, bug, refactor, or chore they want specified. Produces a structured markdown spec file at specs/<slug>.md through dialogue.
---

# Spec Define

Capture a feature request, bug report, refactor, or chore as a structured
spec definition saved at `specs/<slug>.md`.

## Workflow

### Step 1 — Read the Initial Description

Read the user's initial message. Extract everything you can about:

- What they want (or what is broken).
- Why it matters.
- Any constraints, deadlines, or context already mentioned.

Do not write the spec yet. First, assess what you know and what is missing.

### Step 2 — Have a Conversation

This is a dialogue, not an intake form. Your goal is to understand the user's
need well enough to write a spec that captures their intent precisely.

Engage naturally: acknowledge what they have already told you, show you
understood it, then ask only about the gaps. Do not run through a checklist —
ask what genuinely matters given what they said.

**How to ask questions:**

Use the `question` tool. After each call, stop and wait for the user's
answer; it will arrive as the next user message. You may repeat this cycle
as many times as needed. Prefer multiple focused questions over one long
question.

**Formatting question text:**

- Markdown is rendered. Use `-`, `*`, or `1.` for lists, each on its own
  line, with a blank line before the list. Do not use `a)`, `b)`, `(i)`,
  etc. — they render as plain text.
- When asking the user to choose from a fixed set of options, pass them as
  the tool's `options` argument rather than embedding them in the question
  text.
- Ask one focused question per call.

**Areas to explore (touch only what is still unclear):**

- **What kind of change is this?** `feature`, `bug`, `refactor`, or `chore`.
- **What is the underlying problem?** Why does this need to happen?
- **Current vs. desired state.** What happens now, and what should happen
  instead?
- **How will we know it is done?** Concrete acceptance criteria.
- **What could go wrong?** Edge cases, error scenarios.
- **Anything off-limits?** Things that might seem in scope but should not
  be touched.
- **Constraints.** Dependencies, compatibility, tech limitations.

Go back and forth as many rounds as needed. Lead each round with what you
have understood so far, then ask only the next most important question.
Stop when you have enough to write a precise spec — not when every checkbox
is ticked.

If the user's initial message is already comprehensive, skip directly to
Step 3.

### Step 3 — Pick a Slug

Derive a `<slug>` from the title:

- Lowercase.
- Words separated by `-`.
- Alphanumeric and `-` only.
- Up to ~50 characters.

Confirm the slug with the user via `question` before writing anything. The
slug becomes the filename: `specs/<slug>.md`.

### Step 4 — Draft the Spec

Use this structure exactly. Omit any section that has no content (do not
write "None" or "N/A").

```text
# <Title>

| Field         | Value                                                  |
|---------------|--------------------------------------------------------|
| **Title**     | <title>                                                |
| **Type**      | <feature \| bug \| refactor \| chore>                  |
| **Scope**     | <optional: noun describing the section of code affected> |
| **Created**   | <YYYY-MM-DD HH:mm:ss>                                  |
| **Status**    | DRAFT                                                  |

## Problem Statement

<Why this work matters and what problem it solves.>

## Current Behavior

<What happens today. OMIT this section entirely for new features.>

## Desired Outcome

<What should the world look like after this is implemented.>

## Acceptance Criteria

- [ ] <Concrete, verifiable criterion>
- [ ] <Concrete, verifiable criterion>

## Edge Cases & Error Handling

- <Scenario>: <Expected handling>

## Dependencies & Constraints

<Technical constraints, dependencies, compatibility requirements.>

## Out of Scope

<What this spec explicitly does NOT cover.>

## Notes

<Additional context, references, open questions.>
```

Save the draft to disk first, then ask the user to review it.

**Important — never embed the full spec markdown inside a `question`
tool call.** Tool-call payloads have practical size limits and large
embedded markdown causes timeouts and aborted tool executions. Always
write the file first, then keep the `question` text short.

Steps:

1. Set the `Created` field to the current date/time (your best
   knowledge of "now"; use `YYYY-MM-DD HH:mm:ss`).
2. Use the `write` tool to save the full spec markdown to
   `specs/<slug>.md` with the **Status** row set to `DRAFT`. (You will
   flip it to `DEFINED` only after the user approves in Step 5.)
3. Call `question` with a **short** message — no embedded markdown:

   > I've written a draft spec to `specs/<slug>.md`. Please open it
   > and review.
   >
   > Quick summary:
   >
   > - Type: <type>
   > - <one-line problem statement>
   > - <count> acceptance criteria
   > - <count> edge cases listed
   >
   > Reply `looks good` to finalise, or describe any changes you want.

4. If the user requests changes, **edit `specs/<slug>.md` directly**
   using the `edit` tool (do not rewrite the whole file unless you
   really mean to), then call `question` again with a short summary
   of what changed. Repeat until the user approves.

Do not paste the spec contents into chat unless the user explicitly
asks you to. The file on disk is the source of truth during review.

### Step 5 — Finalise the Spec

The spec file is already on disk from Step 4 with Status `DRAFT`.
Once the user has approved (replied `looks good` or equivalent):

1. Use `edit` to flip the **Status** row in `specs/<slug>.md` from
   `DRAFT` to `DEFINED`.
2. Send a one-line confirmation to the user, e.g.:
   `Spec finalised at specs/<slug>.md (Status: DEFINED).`

If the project is a git repo, append a one-line warning to the
confirmation message:

> Note: leave `specs/<slug>.md` uncommitted on the current branch.
> The spec-implementer will create a feature branch from your repo's
> base branch, and any uncommitted spec/plan files will follow it onto
> the new branch automatically. Committing the spec to your base
> branch (e.g. `develop` or `main`) before implementation runs is
> usually not what you want.

Do not perform any git operations yourself — branch creation is the
spec-implementer's job. Do not suggest next steps. The user controls
what happens after this phase ends.

## Guidelines

- **This is a conversation, not a form.** React to what the user says.
  Acknowledge their words, ask follow-ups that flow naturally from their
  answers.
- **Ask less, listen more.** One well-placed question beats five mediocre
  ones.
- **Omit empty sections.** If a section has no content, omit it entirely.
- **Use the user's language.** Mirror their terminology exactly.
- **Keep acceptance criteria concrete and verifiable.**
- **Make reasonable assumptions when needed.** Note them in the spec rather
  than blocking on every detail.
- **Never flip the Status to DEFINED before the user approves the draft.**
  The DRAFT file is written to disk first (Step 4); only the status flip
  waits on approval (Step 5).
