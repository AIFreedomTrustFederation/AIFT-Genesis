"""Regression tests for public Atlas entity evidence links."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools" / "validation"))

from validate_atlas import validate_links  # noqa: E402


class PublicAtlasLinkTests(unittest.TestCase):
    def validate_uri(self, uri):
        errors = []
        validate_links(
            [{"label": "Evidence", "uri": uri, "type": "documentation"}],
            "entity sample",
            errors,
        )
        return errors

    def test_absolute_https_link_accepted(self):
        self.assertEqual(
            self.validate_uri("https://github.com/AIFreedomTrustFederation/AIFT-Genesis"), []
        )

    def test_https_query_fragment_accepted(self):
        self.assertEqual(self.validate_uri("https://example.org/page?q=1#evidence"), [])

    def test_http_link_rejected(self):
        self.assertTrue(self.validate_uri("http://example.org"))

    def test_javascript_link_rejected(self):
        self.assertTrue(self.validate_uri("javascript:alert(1)"))

    def test_protocol_relative_link_rejected(self):
        self.assertTrue(self.validate_uri("//example.org/claim"))

    def test_relative_link_rejected(self):
        self.assertTrue(self.validate_uri("docs/claim.md"))

    def test_scheme_only_link_rejected(self):
        self.assertTrue(self.validate_uri("https:"))

    def test_missing_host_link_rejected(self):
        self.assertTrue(self.validate_uri("https:///claim"))

    def test_userinfo_link_rejected(self):
        self.assertTrue(self.validate_uri("https://alice@example.org/claim"))

    def test_invalid_port_link_rejected(self):
        self.assertTrue(self.validate_uri("https://example.org:bad/claim"))

    def test_backslash_link_rejected(self):
        self.assertTrue(self.validate_uri("https://example.org\\@attacker.test/claim"))


if __name__ == "__main__":
    unittest.main()
