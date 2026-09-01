# 1. Vision

Christian Studies is a long-term AI-assisted reading and study environment, not an archive of books, a loose collection of Markdown files, or a generic chat interface. It provides a durable home for source material, careful reading, discussion, notes, and knowledge that becomes more useful as additional books are studied. It is also the first real domain profile and evidence base for a broader personal AI-assisted reading environment; Christian study remains a coherent domain rather than becoming the name for every future reading workflow.

The repository supports:

- reading books in a discussion-friendly format;
- AI-assisted questions, summaries, and exploration;
- personal and shared study notes;
- theological study grounded in identifiable sources;
- cross-book accumulation of people, concepts, Scripture, events, and timelines; and
- maintenance that remains understandable years from now.

The wider product direction is **local-first and mobile-first**. “Local-first”
means the current device retains the core reading capability and the user's
authoritative personal data, not that a Mac backend must always be running.
Reading, local evidence lookup, search, notes, and saved knowledge should remain
useful offline; explicitly networked AI calls are an optional capability layered
on top. “Mobile-first” makes the phone reading flow a primary design case, but
does not authorize an immediate native rewrite.

The environment may later support language practice through speech playback,
recognition, realtime conversation, and book-based discussion. Voice is a
candidate capability layer used by Domain Profiles, not a reason to redefine
Christian Studies as a language product or to start implementation before a
real language-learning workflow exists. A separate commercial language-reading
hypothesis is worth preserving, but it remains subordinate to building for one
real reader and gathering complete-book evidence. See the
[Voice Capability Hypothesis](Voice-Capability-Hypothesis.md) and
[Commercial Product Hypothesis](Commercial-Product-Hypothesis.md).

The repository is designed around a simple distinction: a book is a source of study, while the knowledge produced through studying it may outlast and connect to that book.

Its central product insight is that useful reading assistance depends on controllable context. The system should know where the reader is, assemble relevant local evidence, distinguish each source type, expose what will be sent, and preserve a manifest of what informed the answer. Model capability matters, but a more expensive model is not a substitute for accurate, focused, source-linked context.

AI assists reading; it does not replace the reader's judgment, the author's text, or evidence review. The environment must remain useful for reading and notes when AI or network access is unavailable.

## Design principles

1. **Preserve sources.** Original source material is retained unchanged.
2. **Make generated work reproducible.** Normalized and derived files should state their source and be regenerable where practical.
3. **Optimize reading for people.** Reading files should serve comprehension and discussion, not merely mirror an imported file format.
4. **Keep knowledge reusable.** Knowledge pages belong to the repository, not exclusively to one book.
5. **Distinguish provenance.** Original text, editorial normalization, human notes, and AI-generated material must be clearly identifiable.
6. **Prefer durable simplicity.** A convention is adopted only when it improves long-term clarity more than it adds maintenance.
7. **Make context inspectable.** AI evidence selection, source type, revision, and external transmission should be visible and reviewable.
8. **Remain provider-independent.** Durable books, notes, and knowledge must not depend on one model, model provider, or tool protocol.
9. **Evolve without discarding working value.** Generalize the current reader through compatible, testable steps rather than a big-bang rewrite.
10. **Keep personal data portable.** Runtime storage may be optimized for the device, but durable user data needs versioned export/import and must not be owned only by a cloud service or opaque database copy.
11. **Generalize from evidence.** Christian Studies is the first domain; extract a shared Reading Core only after a second representative real use case demonstrates the abstraction.

The current single-book reader is the compatibility baseline for the wider
platform. The immediate strategy is continued real reading and grouped problem
discovery, not roadmap-driven refactoring. Product direction and staged
evolution are defined in [`Product-Plan.md`](Product-Plan.md), with a Chinese
review version in [`Product-Plan-zh.md`](Product-Plan-zh.md). Repeated reading
practice, a representative second use case, and explicit decisions must
continue to inform later revisions.
