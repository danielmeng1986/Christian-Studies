from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


WEB_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = WEB_ROOT / "scripts/local_library.py"


def load_module():
    spec = importlib.util.spec_from_file_location("qfg_local_library_tests", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load local-library module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


LIBRARY = load_module()


def minimal_pdf(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    content = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, value in enumerate(objects, 1):
        offsets.append(len(content))
        content.extend(f"{number} 0 obj\n".encode("ascii") + value + b"\nendobj\n")
    xref = len(content)
    content.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    content.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    content.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    return bytes(content)


class LocalLibraryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "Sources"
        self.library = LIBRARY.LocalLibrary(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def metadata(**overrides):
        value = {
            "title": "Local source",
            "author": "Test Author",
            "language": "en",
            "sourceType": "book",
            "theologicalTradition": None,
            "authorityClass": "scholarly",
            "url": None,
            "licenseNote": "test fixture",
            "sensitivity": "standard",
        }
        value.update(overrides)
        return value

    def test_markdown_import_preserves_original_and_rebuilds_index(self) -> None:
        original = b"# Grace\n\nPuritan grace forms durable godliness.\n"
        preview = self.library.preview_import("grace.md", original, self.metadata())
        self.assertEqual(preview["format"], "markdown")
        self.assertEqual(preview["sampleChunks"][0]["headingPath"], ["Grace"])
        source = self.library.confirm_import(preview)
        original_path = self.root / source["originalPath"]
        self.assertEqual(original_path.read_bytes(), original)
        self.assertEqual(hashlib.sha256(original_path.read_bytes()).hexdigest(), source["sha256"])

        self.assertEqual(self.library.search("Puritan grace")[0]["locator"], "section:1:1")
        removed = self.library.remove_derived_index(source["sourceId"])
        self.assertGreater(removed, 0)
        self.assertEqual(self.library.search("Puritan grace"), [])
        rebuilt = self.library.rebuild_index()
        self.assertEqual(rebuilt, {"sourceCount": 1, "chunkCount": 1})
        self.assertEqual(self.library.search("Puritan grace")[0]["sourceId"], source["sourceId"])
        self.assertEqual(original_path.read_bytes(), original)

    def test_pdf_import_has_page_locator_and_requires_outbound_approval(self) -> None:
        original = minimal_pdf("Puritan grace and godliness")
        preview = self.library.preview_import("paper.pdf", original, self.metadata(title="PDF source"))
        self.assertEqual(preview["format"], "pdf")
        self.assertTrue(preview["sampleChunks"][0]["locator"].startswith("page:1:"))
        source = self.library.confirm_import(preview)
        hit = self.library.search("Puritan grace")[0]
        self.assertFalse(hit["externalSharingApproved"])
        updated = self.library.update_source(source["sourceId"], {"approveExternalSharing": True})
        self.assertIsNotNone(updated["externalSharingApprovedAt"])
        self.assertTrue(self.library.search("Puritan grace")[0]["externalSharingApproved"])

    def test_private_source_is_disabled_by_default(self) -> None:
        preview = self.library.preview_import(
            "private.txt", b"Private pastoral note", self.metadata(sensitivity="private")
        )
        source = self.library.confirm_import(preview)
        self.assertFalse(source["enabled"])
        self.assertEqual(self.library.search("pastoral note"), [])
        self.library.update_source(source["sourceId"], {"enabled": True})
        self.assertEqual(len(self.library.search("pastoral note")), 1)

    def test_json_uses_json_pointer_locators(self) -> None:
        preview = self.library.preview_import(
            "entry.json", b'{"topic":{"name":"godliness"}}', self.metadata()
        )
        self.assertEqual(preview["sampleChunks"][0]["locator"], "json:/topic/name")


if __name__ == "__main__":
    unittest.main()
