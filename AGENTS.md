# AGENTS.md — Global Output Governance

These rules apply to every agent in this configuration, in every session.
They shape *how* agents write code, prose, and explanations. When a rule
here conflicts with a lower-priority instruction, this file wins — except
where an agent's own hard rules explicitly override it.

## YAGNI (You Aren't Gonna Need It)

Solve the immediate problem, nothing more. Do not build for hypothetical
future requirements. Do not add configuration knobs, extension points, or
generic layers until a concrete second use case actually exists.

## No speculative abstraction

Do not wrap functions, classes, or patterns in utility layers "just in
case". Introduce an abstraction only when the duplication or complexity it
removes is real and present in the code today.

## No single-use wrappers

A wrapper earns its place only when it encapsulates complexity that occurs
in two or more call sites. A function called once should usually be inlined.

## Comments explain why, not what

Comments capture intent, design decisions, and non-obvious tradeoffs. They
must not restate what the code already says. If a comment merely narrates
the next line, delete it and let the code speak.

## No silent catch

All error handling is explicit. Never swallow an exception with an empty or
catch-all handler. If you catch, you must handle it, log it with context, or
re-throw with added context. Silent failures hide bugs.

## No dead code

Remove unused imports, variables, functions, parameters, and branches. Do
not leave commented-out code behind. Dead code misleads future readers and
rots quietly.

## Follow project conventions

Match the patterns already established in the project — naming, file layout,
error handling, tool usage, formatting. Consistency beats personal
preference. If the right convention is unclear, match nearby existing code
or ask.

## Concise output

Be direct. Avoid filler, throat-clearing, and unnecessary preamble. State
what you did or found in as few words as carry the meaning. Do not pad
explanations with jargon or restate the question back to the user.

## Progress updates

For a related exploration phase, send at most one kickoff update. Combine
related discoveries into one update. Send another update only for materially
new evidence, a blocker, a changed plan, or a user decision. Continue silently
when there is no new information.

Do not restate or paraphrase a conclusion already communicated. Do not repeat
progress conclusions in the final response. Keep every update concise and
factual.

## Epistemological honesty

Admit uncertainty. Say "I don't know" or "I'm not sure" rather than
guessing with false confidence. Distinguish clearly between what you have
verified (read in the code, ran, observed) and what you are inferring or
assuming. Flag edge cases and paths you have not tested, so the reader knows
where the risk lives.
