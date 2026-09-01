# Voice Capability Hypothesis

**Version:** 0.1
**Status:** Future capability hypothesis — not implementation authority
**Scope:** Speech playback, recognition, realtime conversation, and
language-practice sessions around reading

> Chinese review version:
> [`Voice-Capability-Hypothesis-zh.md`](Voice-Capability-Hypothesis-zh.md).

## 1. Purpose and authority

This document preserves a direction that may extend the personal
AI-assisted reading environment into an **AI-assisted reading and language
practice environment**. It records product intent, staged experiments, data
boundaries, and unresolved decisions. It does not authorize a provider,
schema, mobile framework, audio pipeline, or implementation phase.

Voice is not treated as a synonym for text-to-speech. The long-term hypothesis
is that reading, trusted lookup, listening, active recall, spoken use, and
book-based discussion can form one continuous learning loop.

Implementation remains gated by a representative English or German reading
use case, the relevant Open Questions, compatibility fixtures, and an accepted
decision before durable schemas or shared services are introduced.

## 2. Staged capability direction

| Stage | Reader question | Candidate outcome |
| --- | --- | --- |
| Voice 1 | What does this word mean, and how is it pronounced? | Dictionary evidence, IPA/pronunciation data, and standard playback |
| Voice 2 | How would this sentence be spoken naturally? | Natural, slow, or emphasized playback with optional prosody guidance |
| Voice 3 | Can I actively use this expression? | Short contextual speaking practice around a saved target |
| Voice 4 | Can I discuss this book in the target language? | Context-aware spoken discussion of a passage, chapter, character, or argument |

The stages are evidence gates, not a commitment to build the complete system.
The smallest useful stage should be tested first after the language-learning
use case begins. Later stages proceed only when repeated use shows value.

### 2.1 Voice 1 — word pronunciation

Selecting a word may combine:

- a trusted dictionary definition;
- IPA or other provider-supplied pronunciation information; and
- playable pronunciation from a legally usable recording or speech provider.

Dictionary evidence and generated speech remain different source types. A
human recording supplied under appropriate rights may be preferred, while
AI/TTS remains a generated capability and must not be presented as an
authoritative dictionary record.

### 2.2 Voice 2 — sentence pronunciation and prosody

A selected sentence may be played at natural speed, at a slower learning
speed, or with deliberate emphasis. Optional guidance may describe sentence
stress, reduction, linking, pauses, intonation, and rhythm.

Generated audio and generated prosody explanation must remain labeled. This
stage aims to explain why natural speech sounds as it does, not merely to emit
audio for written text.

### 2.3 Voice 3 — vocabulary and expression practice

A saved word, expression, collocation, or grammar pattern may launch a short
spoken scenario that invites the learner to use the target naturally. The
preferred interaction is a brief conversation followed by consolidated
feedback, rather than correction after every utterance.

The objective is active retrieval and appropriate use in context, not only
recall of a definition or completion of an isolated sentence exercise.

### 2.4 Voice 4 — book-based voice discussion

An advanced learner may discuss the current passage, chapter, character, or
argument in the target language. The Context Service may assemble the book,
current reading focus, relevant earlier context, selected notes, accepted
language knowledge, and eligible Source Provider evidence.

At this stage language becomes the medium for discussing the book rather than
only the object of a translation or grammar exercise.

## 3. Discussion profiles

Discussion remains a shared concept, but its policy and evaluation goal may
vary by profile:

| Profile | Primary goal | Typical emphasis |
| --- | --- | --- |
| Study | Understand the content | Claims, reasoning, source text, evidence, cross-reference |
| Language Tutor | Improve language while discussing content | Vocabulary, grammar, collocation, naturalness, register |
| Speaking Practice | Repeatedly use selected targets | Fluency, retrieval, target expressions, delayed feedback |
| Free Discussion | Continue a natural target-language conversation | Communication and continuity with lighter intervention |

Profiles may share book identity, stable anchors, Context Service, model
providers, and Source Providers. They must not silently share prompt policy,
evaluation criteria, correction style, or session output. The exact profile
contract remains open under OQ-021 and OQ-023.

## 4. Voice sessions as learning events

A completed session may produce separately typed records:

- a transcript, complete or explicitly edited/condensed;
- a content-oriented discussion summary;
- language feedback with examples and uncertainty;
- target-expression usage results;
- AI proposals for expressions, grammar points, or recurring mistakes;
- future-practice signals; and
- session metadata such as language, profile, duration, context references,
  model/provider, and consent state.

Language feedback should distinguish successful usage, specific improvements
with an original and better form where appropriate, and which target
expressions were or were not actively used. It should preserve uncertainty
rather than presenting every stylistic preference as an error.

These records have different authorship and authority. A transcript is not
automatically verified source text. Feedback and summaries are AI-generated
material. A suggested knowledge item becomes durable accepted knowledge only
after the user accepts or edits it, preserving the existing human-reviewed
knowledge boundary.

Future-practice signals may record successful active use, targets not yet used,
repeated errors, and candidates for later practice. Their schema, retention,
and export behavior must be decided before persistence.

## 5. Audio retention and privacy hypothesis

Raw audio should be ephemeral by default. The durable value is expected to be
in the transcript, summary, feedback, accepted knowledge, usage records, and
session metadata. A user may explicitly save a named **speaking sample** for
longitudinal comparison, but opt-in audio is user-owned sensitive data with
explicit retention, deletion, export, and provider-transmission rules.

Microphone capture, transcription, generated speech, and realtime conversation
may cross different local or external provider boundaries. The UI must make the
active boundary and material sent externally understandable before capture or
transmission when consent is required. Credentials remain in approved secret
storage and never enter audio, transcripts, manifests, or exports.

## 6. Capability and domain boundary

The candidate shared capability layer contains:

```text
Capabilities
├── Speech Playback
├── Speech Recognition
├── Realtime Conversation
└── Practice Session
```

Domain Profiles decide how those capabilities are used. Language Learning may
configure target expressions, feedback policy, and practice goals. Christian
Studies may later use playback for a passage or support a spoken question or
walk-based discussion. Neither domain owns the generic speech transport or
provider adapter merely because it uses it first.

This separation is a target hypothesis, not proof that all four capabilities
belong in the shared core. A responsibility moves into shared architecture only
after two real workflows demonstrate a stable contract.

## 7. Specialized pronunciation assessment

Natural conversation, general pronunciation suggestions, fluency feedback, and
language-expression feedback may be appropriate for general voice models.
Phoneme-level assessment, acoustic measurement, strict scoring, and
language-laboratory-grade diagnostics are a separate specialized capability.

The first Voice stages must not imply that a general speech or realtime model
can produce reliable quantified phoneme scores. Such assessment requires its
own provider evaluation, ground-truth fixtures, error policy, and user-facing
limitations before it can be offered.

## 8. Evidence and decision gates

Before the first durable Voice implementation:

1. genuinely use a representative English or German book;
2. identify the smallest repeated voice need rather than implementing all four
   stages;
3. resolve the relevant parts of OQ-020, OQ-021, and OQ-023;
4. specify capture, provider transmission, retention, deletion, export, and
   recovery behavior;
5. define compatibility and evaluation fixtures, including accessibility and
   failure behavior; and
6. accept an ADR or scoped implementation specification if the experiment
   changes shared architecture or durable data authority.

Until those gates are met, Voice remains a documented future capability. It
must not displace current reading, the second-book evidence gate, portable user
data, or the working Reader baseline.
