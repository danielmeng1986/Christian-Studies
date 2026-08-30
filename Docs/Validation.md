# Validation Contract

**Status:** Core normative specification

**Scope:** Generation, automated checks, and verification claims

Documentation defines repository truth and boundaries. Generators make derived
artifacts reproducible. Tests and policy checks detect violations. These roles
are complementary: a documented rule remains binding even before it has an
automated checker.

## 1. Verification principles

1. Validate the authoritative input and the generated behavior it affects.
2. Prefer deterministic generators so that repeated builds expose drift.
3. Test user-data writes for schema validation, revision conflicts, and
   preservation of unrelated data.
4. Test derived systems for rebuildability and source traceability.
5. Never describe a rule as automatically enforced unless a current check
   covers it.
6. Record gaps explicitly instead of treating an absent test as permission to
   violate a documented boundary.

## 2. Current reader commands

Run from the repository root after the environment described in the local
reader README has been prepared:

```sh
'Books/追寻敬虔/Web/.venv/bin/python' \
  'Books/追寻敬虔/Web/scripts/build.py'

'Books/追寻敬虔/Web/.venv/bin/python' -m unittest discover \
  -s 'Books/追寻敬虔/Web/tests'
```

The first command regenerates `Books/追寻敬虔/Web/dist/`. The second exercises
the current reader's build, note and discussion APIs, context assembly,
retrieval, local library, and related service behavior.

For a small change, targeted test modules may be run during iteration, but the
full suite is required before declaring a cross-cutting reader change complete.

## 3. Change-to-check matrix

| Changed area | Required minimum verification |
| --- | --- |
| `Reading/`, footnotes, Scripture config/data | Reader build and `test_build.py`; inspect affected chapter |
| `Web/src/` or `Web/scripts/build.py` | Reader build and `test_build.py`; inspect affected responsive/runtime behavior when visual |
| Annotation persistence or API | `test_notes_api.py` plus affected build/service tests |
| Discussion schema, persistence, or API | `test_discussions.py`, `test_discussions_api.py`, and affected context tests |
| Context assembly or retrieval | `test_context_builder.py`, `test_context_retrieval.py`, and discussion tests |
| Local source library | `test_local_library.py` and affected context/service tests |
| Core architecture or canonical paths | Documentation link/path audit and every subsystem test affected by the decision |
| Generated or derived format | Rebuild twice when determinism is part of the contract; compare declared outputs |

This matrix is a minimum. A change that crosses rows inherits all applicable
checks.

## 4. Enforced now

The current reader suite provides automated coverage for, among other behavior:

- deterministic multi-chapter reader generation;
- expected chapter and asset production;
- Scripture and footnote processing;
- annotation and discussion validation/persistence behavior;
- deterministic context construction and evidence classification;
- cross-chapter retrieval;
- supplemental-library preservation and index rebuilding; and
- service API behavior represented by the test suite.

The tests are the precise authority on covered cases. This summary must not be
used to infer a check that is not present in a test.

## 5. Documented but not yet repository-wide automated

There is currently no single root policy checker that proves all of the
following across every book:

- canonical book directories and metadata fields are complete;
- every generated path is ignored and reproducible;
- no generated index or `dist/` file was hand-edited;
- every Markdown link in `Docs/` resolves;
- every reading unit has complete provenance; or
- all user-data schemas preserve unknown compatible fields.

Until such checks are implemented, these are review obligations. Future policy
scripts should live in a clearly named repository-level tooling directory,
operate read-only unless explicitly formatting or generating, report exact
paths and violated rules, and have their own tests.

## 6. Completion report

A completion report for material work must state:

- authoritative files changed;
- generated or derived artifacts rebuilt;
- exact validation commands run and their result;
- any required visual or manual inspection; and
- known checks not run or automation gaps relevant to the change.

Passing tests does not authorize committing generated output that the
architecture says is disposable.
