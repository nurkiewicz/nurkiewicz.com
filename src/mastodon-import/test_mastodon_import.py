import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

import mastodon_import


class MastodonImportTest(unittest.TestCase):
    def test_default_output_uses_current_date(self) -> None:
        with patch.object(mastodon_import, "date") as mocked_date:
            mocked_date.today.return_value = date(2026, 7, 23)

            output = mastodon_import.default_output("mastodon.social")

        self.assertEqual(output.name, "2026-07-23-mastodon.social-archive.md")

    def test_load_instance_uses_actor_url(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive_path = Path(temporary_directory) / "archive.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(
                    "actor.json",
                    '{"url": "https://Mastodon.Social/@user"}',
                )

            with zipfile.ZipFile(archive_path) as archive:
                instance = mastodon_import.load_instance(archive)

        self.assertEqual(instance, "mastodon.social")

    def test_skips_boosts(self) -> None:
        outbox = """{
          "orderedItems": [{
            "type": "Announce",
            "published": "2022-11-20T09:15:25Z",
            "object": "https://social.example/users/other/statuses/456"
          }]
        }"""
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive_path = Path(temporary_directory) / "archive.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("outbox.json", outbox)

            with zipfile.ZipFile(archive_path) as archive:
                posts = mastodon_import.load_archive(archive)

        self.assertEqual(posts, [])

    def test_html_to_markdown_preserves_links_and_line_breaks(self) -> None:
        html = '<p>Hello <a href="https://example.com"><span>world</span></a><br>Again</p>'

        self.assertEqual(
            mastodon_import.html_to_markdown(html),
            "Hello [world](https://example.com)\nAgain",
        )

    def test_imports_post_and_captioned_image(self) -> None:
        outbox = """{
          "orderedItems": [{
            "type": "Create",
            "published": "2022-11-07T09:55:58Z",
            "object": {
              "type": "Note",
              "url": "https://social.example/@user/123",
              "content": "<p>Post content</p>",
              "summary": null,
              "inReplyTo": null,
              "to": ["https://www.w3.org/ns/activitystreams#Public"],
              "attachment": [{
                "url": "/media/image.png",
                "mediaType": "image/png",
                "name": "Useful caption"
              }]
            }
          }]
        }"""
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            archive_path = root / "archive.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(
                    "actor.json", '{"url": "https://social.example/@user"}'
                )
                archive.writestr("outbox.json", outbox)
                archive.writestr("media/image.png", b"image")

            with zipfile.ZipFile(archive_path) as archive:
                posts = mastodon_import.load_archive(archive)
                page = mastodon_import.render_page(
                    archive, posts, root / "assets", "/img/mastodon"
                )

            self.assertIn('<span id="mastodon-123"></span>', page)
            self.assertIn(
                "![Useful caption](/img/mastodon/123-image.png)", page
            )
            self.assertNotIn("<figcaption>", page)
            self.assertIn(
                "[Mon Nov 07 09:55:58 2022](https://social.example/@user/123)",
                page,
            )
            self.assertEqual((root / "assets/123-image.png").read_bytes(), b"image")


if __name__ == "__main__":
    unittest.main()
