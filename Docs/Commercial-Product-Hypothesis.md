# Commercial Product Hypothesis: Book-Centered Language Learning

**Version:** 0.1
**Status:** Exploratory product hypothesis — not a roadmap or implementation commitment
**Scope:** A possible language-reading and speaking product derived from shared
reading-platform capabilities

> Chinese review version:
> [`Commercial-Product-Hypothesis-zh.md`](Commercial-Product-Hypothesis-zh.md).

## 1. Hypothesis and current boundary

Christian Studies remains a personal reading and theological-study project
built first for its owner. A separate future product may emerge from the shared
Reading Platform and Voice capabilities:

> An **AI-assisted Language Reading & Speaking Platform** for learners who
> already have some English or German and want to improve through real books.

This is a product hypothesis, not evidence of a market and not permission to
build commercial infrastructure. The project continues to follow **build for
one real user first**, delayed abstraction, and delayed commercialization.

## 2. Product thesis

The candidate product is not primarily a conventional language course. Its
core is a **Book-centered Learning Loop**:

```text
Read
  ↓
Understand
  ↓
Look Up
  ↓
Listen
  ↓
Save
  ↓
Speak
  ↓
Discuss
  ↓
Review
  ↓
Encounter Again
```

The differentiation hypothesis is **context continuity**, not a checklist of
features. A reader should be able to move from one sentence through trusted
lookup, word and sentence audio, AI explanation, saved expressions, spoken
practice, chapter discussion, and reviewed personal knowledge without losing
the book, passage, source, or learning target that connects those actions.

## 3. Domain separation

```text
Shared Reading Platform Core
├── Christian Studies
│   └── Personal / research domain
└── Language Learning Product
    └── Consumer / possible commercial domain
```

The language product must not contain Christian theology books, Bible-specific
content, or the owner's personal Christian Studies knowledge merely because it
uses the same platform. It may reuse only contracts that real evidence has
shown to be shared, such as Reader behavior, Context Service, stable anchoring,
Discussion, Source Providers, knowledge proposals, provenance, portable data,
mobile runtime, and Voice capabilities.

Commercial accounts, telemetry, cloud storage, content licensing, and business
operations must not leak backward into the Christian Studies domain as hidden
requirements.

## 4. Candidate book learning package

A future publisher or content partner might provide more than an EPUB or text
file. A candidate **Book Learning Package** could contain:

```text
Book Learning Package
├── Original Text
├── Language
├── CEFR and difficulty metadata
├── Chapter metadata
├── Vocabulary guidance
├── Grammar metadata
├── Discussion prompts
├── Optional pronunciation metadata
└── Rights and license metadata
```

The platform could add contextual explanation, dictionary integration, Voice,
vocabulary tracking, speaking practice, book discussion, reviewed knowledge,
and adaptive assistance. Package metadata is curated content with provenance;
AI-generated enrichment must remain labeled and reviewable.

This package is only a hypothesis. It does not change the current canonical
book format or authorize a new schema. OQ-015, OQ-020, OQ-022, and a future
commercial content decision must govern any implementation.

## 5. Difficulty and CEFR hypothesis

A future catalog may use A1–C2 CEFR levels for discovery and onboarding, but it
should not assume that one book has one exact difficulty. Difficulty may vary
by book, chapter, passage, vocabulary, or grammar feature. A label such as
`B1+` is guidance, not a precise measurement or guarantee.

Learner profile and content difficulty may later help the system decide when
to offer more support and when to reduce interruption. Any adaptive behavior
requires transparent policy, user control, evaluation, and care not to replace
publisher or human judgment with unreviewed AI classification.

## 6. Onboarding and initial content

The product-value experiment should not require a new user to upload an EPUB
before seeing the experience. A candidate first-use path is:

```text
Choose language
  ↓
Choose level
  ↓
Choose a free book
  ↓
Start reading
```

Initial content may come from public-domain works, self-created material, or
explicitly licensed content. Every item still needs rights, provenance, and
distribution metadata. Publisher licensing must not be a prerequisite for
testing whether dictionary lookup, pronunciation, sentence voice, AI
explanation, expression saving, and speaking practice create a useful loop.

## 7. Distant commercial possibilities

Licensed books, publisher partnerships, book sales, subscriptions, and revenue
sharing may be explored only after product value and rights constraints are
better understood. The long-term hypothesis is that a publisher may provide
content while the platform provides the learning experience.

The current Roadmap explicitly excludes work on:

- DRM or a publisher portal;
- payments, subscriptions, sales, or revenue sharing;
- public accounts or commercial cloud infrastructure;
- App Store commercialization;
- commercial analytics, growth systems, or support operations; and
- licensing negotiations undertaken only to make the hypothesis look complete.

## 8. Validation gate

Before serious commercial product development, the project owner should use
the system to finish at least one complete original English or German book,
preferably two books of different difficulty or type. That use should establish
evidence about:

- which AI actions are repeatedly useful;
- which attractive ideas are rarely used;
- whether speaking practice becomes a habit;
- which expressions are worth saving and revisiting;
- when AI help should appear or remain quiet;
- which correction style preserves reading immersion;
- the natural length of a voice session;
- whether learning features disrupt literary reading; and
- whether accumulated knowledge improves later reading and speaking.

Commercial discovery may then use interviews or a small explicitly scoped
experiment, but accounts, payment, licensing systems, or cloud tenancy require
a separate accepted product decision. Evidence from the owner's use remains a
necessary gate, not sufficient proof of market demand.

## 9. Promotion criteria

This hypothesis may be promoted into an active delivery phase only when:

1. the complete-book usage gate has been met;
2. a repeated problem and target learner are supported by evidence;
3. the Christian Studies and commercial-domain data boundaries are specified;
4. rights, privacy, Voice, portable-data, and distribution questions relevant
   to the proposed experiment are resolved; and
5. a new decision explicitly allocates development scope and defines what will
   not be built.

Until then, the hypothesis preserves an opportunity without competing with the
current real-user reading work.
