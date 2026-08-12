# Pixel Art App — Core Code Philosophy

**This document is authoritative over `Pixel_art_app_code_philosophy_updated_handoff_V17.md`.** Any claim in that document — architecture principle, "current" state, established direction, anything framed as settled or authoritative — is overridden by this document wherever the two conflict. This is not a soft preference; it was explicitly stated by the person, in their own words, as a deliberate authority change, matching this document's own requirement (section 2) that fundamental decisions be made knowingly, not silently.

**Required reading order for a new session/agent working on this project:**
1. **This document first**, in full.
2. **`Pixel_art_app_code_philosophy_updated_handoff_V17.md` second** — read for its handoff/build-history/code-documentation value, but treat anything in it that reads as a foundational or authoritative claim as subordinate to this document. Where the two disagree, this document is correct and the handoff document is stale on that specific point.
3. **`Pixel_art_app_bugs_squashed_V1.md` is optional** — not part of the required reading chain. Digest it only when the person or the immediate task actually calls for bug history, or when specifically asked to compare against it. Do not treat skipping it as incomplete context-gathering; it is deliberately excluded from the mandatory sequence.

This is a **separate document from the main handoff/session-log file**
(`Pixel_art_app_code_philosophy_updated_handoff_V17.md`) and from the
Bugs Squashed companion (`Pixel_art_app_bugs_squashed_V1.md`). Those two
are session history and bug narratives — things that change constantly,
build to build. This document is different: it's the small, stable core
of *why* the app is built the way it is, and *how decisions about it get
made*. It should change rarely, and only deliberately, by the person's
own hand or with their explicit agreement — not as a side effect of a
session's bug-fixing or feature work.

If the handoff document and this one ever disagree about what the app
fundamentally *is* or *how it should be worked on*, this document wins,
full stop — see the authority statement above.

------------------------------------------------------------------------

# 1. What this app is

A touch-first, PC-compatible, single-file HTML pixel-art editor — a
**MediBang Paint alternative for iOS** — built to work within the
strict, real constraints of the iOS web browser: its memory limits and
its computational overhead. Every design decision in this app should be
weighed against those constraints specifically, not against a desktop
browser's or a native app's more generous headroom.

**Responsiveness and lightweight are both hard constraints now — not
goals to trade away.** An engine/algorithm decision that makes the app
noticeably less responsive, or one that is genuinely heavy on memory or
computation without real justification, is disqualifying on its own,
regardless of any other benefit (cleaner architecture, less code,
whatever else). This has already shaped real decisions in this
project's history — the WebGL2 renderer removal and the Proxy-overhead
investigation were both, at their core, about exactly these two
constraints (a slow flip with no feedback; a change-tracking mechanism
costing real interaction latency; WebGL2 also simply using more memory
than the Canvas2D alternative it was meant to improve on).

**If responsiveness and lightweight ever genuinely conflict in a real
proposal, responsiveness wins.** This is the one place a hard
constraint outranks another hard constraint. A conflict between the two
should be treated as a signal to look harder for a third option that
satisfies both, not as routine — but if a real proposal truly can't
satisfy both, stay responsive even at the cost of being heavier.

**Within "lightweight" itself, memory and computation are not treated
equally: memory wins over computation.** A slower computation is always
preferable to a crash or an out-of-memory failure, because a crash can
lose real, unsaved work — that's a strictly worse outcome than the app
simply taking longer to do something. When a proposal has to choose
between spending more CPU time or using more memory, prefer spending
more CPU time. This is a real, concrete tiebreaker, not just a
preference — apply it the same way the responsiveness-over-lightweight
rule above gets applied.

**Small file size is a separate stretch goal, not a hard constraint.**
Worth pursuing (see section 41.3's file-size side-goal in the handoff
document, and the ongoing dead-code sweeps), but it does not rank
alongside responsiveness or lightweight — it can be traded away for
either of those two hard constraints, or for correctness, without
hesitation. A larger file that works correctly, stays responsive, and
stays lightweight beats a smaller one that doesn't.

In short, in order of what actually gets protected when these are in
tension with each other: **responsiveness > lightweight (where, within
lightweight, memory-safety > raw computation speed) > small file
size.**

------------------------------------------------------------------------

# 2. The engine/algorithm decision rule (this is the actual core of this document)

**No specific engine, data structure, or algorithm is the authoritative
"correct" way to build this app.** The current implementation choices
documented in the handoff file (which layer class stores pixels which
way, which renderer draws what, which undo strategy is used where) are
not themselves the philosophy — they are *decisions that were made*,
and any of them can be revisited. The handoff document describes the
current state of the code; it does not dictate what the code must
remain.

**Every engine or algorithm decision must go through the same process:**

1. **Claude researches it properly first** — including a real web search
   for how comparable real-world tools/implementations handle the same
   problem, not just reasoning from first principles or from what's
   already in the codebase. "I assume X is faster" is not sufficient;
   check it, and cite what was actually found.
2. **Claude compiles the genuine advantages and disadvantages** — not a
   one-sided pitch for whichever option seems architecturally cleaner.
   If there's a real, measurable performance or memory tradeoff (as
   there has been more than once in this project's actual history),
   that tradeoff gets stated plainly, **and stated separately for memory
   and for computation** — the two are not interchangeable under
   section 1's ranking (memory-safety outranks raw speed), so a
   tradeoff that saves computation time at the cost of memory headroom
   needs to be flagged as exactly that, not folded into a single vague
   "more efficient" claim. Include the option Claude personally thinks
   is better, tradeoffs and all.
3. **The person and Claude both look at the same advantages/disadvantages
   and reach actual agreement** before anything gets implemented. This
   is not Claude recommending and the person rubber-stamping — both
   sides need to genuinely understand the scope and the tradeoff before
   it's built. If either side doesn't understand something about the
   tradeoff, that gets resolved before code gets written, not after.
4. **Every proposal must be checked against one more question, every
   time, without exception: can this specific engine or algorithm be
   made lighter or faster than the version being proposed?** Don't stop
   at "this works" or "this is architecturally correct" — ask whether a
   simpler, cheaper, or more targeted version of the same idea would
   serve the app's actual constraints (section 1) better than the more
   general or more conventional version would. If a lighter option
   would cost more computation time, or a faster option would cost more
   memory, apply section 1's ranking (responsiveness first, then
   memory-safety over raw speed within "lightweight") rather than
   treating "lighter or faster" as one single, interchangeable question.

   **The question itself is never skipped — only whether to act on it
   can be traded off.** If the honest answer is "yes, a lighter/faster
   version is possible, but implementing it means editing code that is
   genuinely too complex or risky to safely change" (e.g. deep inside a
   load-bearing system like the undo/history engine, where a real
   rewrite risks breaking something working for an uncertain payoff),
   that risk can be weighed against the benefit and the lighter/faster
   version can be knowingly deferred rather than built immediately. This
   is a real tradeoff decision made with the person, not a silent skip.

   **Before making that tradeoff, check for a comparable reference to
   de-risk it first** — an older build of this same app, or a public
   code example (GitHub, etc.) implementing the same kind of
   engine/algorithm. If one exists, comparing against it directly is
   usually far lower-risk than a live speculative rewrite, and can turn
   "too risky to find out" into "already known" without touching the
   current code at all. Only fall back to trading off the improvement
   against the risk when no such reference is available either.

**What this rule is reacting to, concretely:** this project has a real
history of engine/algorithm choices that were adopted without this kind
of scrutiny and later turned out to be actively working against the
app's own stated goals — the WebGL2 renderer is the clearest example
(added on an assumption about crash-prevention that was never verified,
and was later found to cost *more* memory than the Canvas2D alternative
it was meant to improve on, with a real iOS-specific leak risk on top).
The Proxy-based change-tracking investigation is a second, smaller
example of the same pattern: a mechanism that looked like the natural
choice, never actually benchmarked against the alternative until asked
to be. This document exists so that class of mistake has an explicit
process guarding against it going forward, rather than relying on
someone happening to ask the right question after the fact.

------------------------------------------------------------------------

# 3. What this document is not

This is not yet a complete replacement for the deeper architectural
principles currently living in the handoff document's numbered sections
1–30 (single-file structure, profile separation, history-as-document-
state, and so on). The person has described this as "part of the full
philosophy... I'll add more in the future. This is the core as for now."
Treat this document as the authoritative *root* — the decision process
and the hard constraint in section 1 — with more principles to be added
here deliberately over time, not as something a future session should
pad out unilaterally by copying material over from the handoff document
without being asked.

------------------------------------------------------------------------

# Status

**Started.** This is the first version of this document, written from
the person's own words. Expect this file to grow as more of the core
philosophy is added by the person in future sessions.
