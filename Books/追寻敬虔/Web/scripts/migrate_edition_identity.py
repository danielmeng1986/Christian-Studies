#!/usr/bin/env python3
"""Validate and persist edition identity in reader-owned user data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import discussions
import serve


def migrate(*, apply: bool) -> tuple[int, int]:
    manifest = json.loads(serve.EDITION_MANIFEST_PATH.read_text(encoding="utf-8"))
    changed_notes = 0
    changed_discussions = 0
    for edition in manifest["editions"]:
        edition_id = edition["editionId"]
        for chapter_id, chapter in edition["chapters"].items():
            note_path = serve.BOOK_ROOT / chapter["notesPath"]
            note_content = note_path.read_bytes()
            note_document = serve.normalize_note_document(
                json.loads(note_content), chapter_id, edition_id
            )
            normalized_notes = serve.serialize_note_document(note_document)
            if normalized_notes != note_content:
                changed_notes += 1
                if apply:
                    serve.write_notes_atomically(note_path, normalized_notes)

            discussion_root = serve.BOOK_ROOT / chapter["discussionsPath"]
            if not discussion_root.exists():
                continue
            for discussion_path in sorted(discussion_root.glob("*.json")):
                document, content = discussions.load_discussion(
                    discussion_path, chapter_id, edition_id=edition_id
                )
                normalized_discussion = discussions.serialize_discussion_document(document)
                if normalized_discussion != content:
                    changed_discussions += 1
                    if apply:
                        discussions.write_atomically(discussion_path, normalized_discussion)
    return changed_notes, changed_discussions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Persist validated migrations atomically")
    args = parser.parse_args()
    notes, discussions_count = migrate(apply=args.apply)
    action = "Migrated" if args.apply else "Would migrate"
    print(f"{action} {notes} note files and {discussions_count} discussion files.")


if __name__ == "__main__":
    main()
