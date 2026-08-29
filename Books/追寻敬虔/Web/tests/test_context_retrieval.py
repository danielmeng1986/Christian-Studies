from __future__ import annotations

import json
import sys
import unittest
from collections import Counter
from pathlib import Path


WEB_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = WEB_ROOT / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import context_builder as CONTEXT
import context_retrieval as RETRIEVAL


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures/cross-chapter-retrieval-cases.json"


class CrossChapterRetrievalEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        chapter_paths, footnote_paths = CONTEXT.discover_retrieval_paths()
        cls.units = RETRIEVAL.build_retrieval_units(
            chapter_paths,
            footnote_paths,
            CONTEXT.build_block_map,
        )
        cls.cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]

    def test_all_twenty_chapters_and_linked_footnotes_are_rebuildable(self) -> None:
        self.assertEqual({unit.chapter_id for unit in self.units}, {f"{number:02d}" for number in range(1, 21)})
        self.assertGreater(len(self.units), 1200)
        self.assertGreater(sum(bool(unit.footnotes) for unit in self.units), 400)
        self.assertTrue(all(len(unit.source_revision) == 64 for unit in self.units))
        self.assertTrue(all(unit.heading_path and unit.block_id for unit in self.units))

    def test_fixed_twenty_query_evaluation_meets_m4_baseline(self) -> None:
        self.assertEqual(len(self.cases), 20)
        unit_locators = {(unit.chapter_id, unit.block_id, unit.source_revision) for unit in self.units}
        relevant_results = 0
        total_results = 0
        answered_queries = 0
        empty_queries = 0

        for case in self.cases:
            passages = RETRIEVAL.retrieve_book_passages(
                self.units,
                current_chapter_id="20",
                selected_block_id="20-p-9999",
                question=case["question"],
                selection="",
                entities=case.get("entities", []),
                scripture_ids=case.get("scriptureIds", []),
            )
            self.assertLessEqual(len(passages), 5, case["id"])
            self.assertLessEqual(
                max(Counter(passage["chapterId"] for passage in passages).values(), default=0),
                2,
                case["id"],
            )
            self.assertEqual(
                len({passage["passageId"] for passage in passages}),
                len(passages),
                case["id"],
            )
            for passage in passages:
                self.assertIn(
                    (passage["chapterId"], passage["blockId"], passage["sourceRevision"]),
                    unit_locators,
                    case["id"],
                )

            if case.get("expectEmpty"):
                empty_queries += 1
                self.assertEqual(passages, [], case["id"])
                continue

            self.assertTrue(passages, case["id"])
            self.assertIn(passages[0]["chapterId"], case["expectedTopChapterIds"], case["id"])
            answered_queries += 1
            relevant = set(case["relevantChapterIds"])
            relevant_results += sum(passage["chapterId"] in relevant for passage in passages)
            total_results += len(passages)

        precision_at_five = relevant_results / total_results
        self.assertEqual(answered_queries, 19)
        self.assertEqual(empty_queries, 1)
        self.assertGreaterEqual(precision_at_five, 0.75)


if __name__ == "__main__":
    unittest.main()
