#!/usr/bin/env python3
"""Convert a Mastodon archive ZIP into a Jekyll Markdown archive page."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parent.parent
PUBLIC_AUDIENCE = "https://www.w3.org/ns/activitystreams#Public"


def default_output(instance: str) -> Path:
    filename = f"{date.today().isoformat()}-{instance}-archive.md"
    return REPOSITORY_ROOT / "docs/_posts" / filename


def default_assets_dir(instance: str) -> Path:
    return REPOSITORY_ROOT / "docs/img" / instance


def default_assets_url(instance: str) -> str:
    return f"/img/{instance}"


class MastodonHtmlToMarkdown(HTMLParser):
    """Translate the small HTML subset used in Mastodon post content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[tuple[str, list[str]]] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag == "a":
            href = dict(attrs).get("href") or ""
            self.links.append((href, []))
        elif tag == "br":
            self._append("\n")

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.links:
            href, text_parts = self.links.pop()
            text = "".join(text_parts).strip() or href
            rendered = f"[{escape_link_text(text)}]({href})" if href else text
            self._append(rendered)
        elif tag in {"p", "div", "blockquote"}:
            self._append("\n\n")

    def handle_data(self, data: str) -> None:
        self._append(data)

    def markdown(self) -> str:
        text = "".join(self.parts).replace("\xa0", " ")
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _append(self, text: str) -> None:
        if self.links:
            self.links[-1][1].append(text)
        else:
            self.parts.append(text)


@dataclass(frozen=True)
class Post:
    activity_type: str
    identifier: str
    published: datetime
    external_url: str
    content: str
    summary: str | None
    in_reply_to: str | None
    attachments: tuple[dict[str, object], ...]
    public: bool


def escape_link_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def html_to_markdown(content: str) -> str:
    parser = MastodonHtmlToMarkdown()
    parser.feed(content)
    parser.close()
    return parser.markdown()


def parse_timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"Invalid Mastodon timestamp: {value}") from error


def status_identifier(url: str) -> str:
    path_parts = [part for part in urlparse(url).path.split("/") if part]
    if not path_parts:
        raise ValueError(f"Cannot determine post identifier from URL: {url}")
    identifier = path_parts[-1]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", identifier):
        raise ValueError(f"Unsafe post identifier in URL: {url}")
    return identifier


def load_archive(archive: zipfile.ZipFile) -> list[Post]:
    try:
        outbox = json.loads(archive.read("outbox.json"))
    except KeyError as error:
        raise ValueError("The ZIP does not contain outbox.json") from error
    except json.JSONDecodeError as error:
        raise ValueError("outbox.json is not valid JSON") from error

    activities = outbox.get("orderedItems")
    if not isinstance(activities, list):
        raise ValueError("outbox.json does not contain an orderedItems list")

    posts: list[Post] = []
    for activity in activities:
        if not isinstance(activity, dict):
            raise ValueError("Mastodon activity must be a JSON object")
        activity_type = activity.get("type")
        published_value = activity.get("published")
        obj = activity.get("object")
        if not isinstance(published_value, str):
            raise ValueError("Mastodon activity has no publication timestamp")

        if activity_type == "Create" and isinstance(obj, dict):
            if obj.get("type") != "Note":
                continue
            external_url = obj.get("url") or obj.get("id")
            content = obj.get("content", "")
            if not isinstance(external_url, str) or not isinstance(content, str):
                raise ValueError("Mastodon Note has invalid URL or content")
            attachments = obj.get("attachment", [])
            if not isinstance(attachments, list):
                raise ValueError(f"Post {external_url} has invalid attachments")
            audiences = obj.get("to", [])
            posts.append(
                Post(
                    activity_type="Create",
                    identifier=status_identifier(external_url),
                    published=parse_timestamp(published_value),
                    external_url=external_url,
                    content=html_to_markdown(content),
                    summary=(
                        html_to_markdown(obj["summary"])
                        if isinstance(obj.get("summary"), str)
                        else None
                    ),
                    in_reply_to=(
                        obj.get("inReplyTo")
                        if isinstance(obj.get("inReplyTo"), str)
                        else None
                    ),
                    attachments=tuple(
                        attachment
                        for attachment in attachments
                        if isinstance(attachment, dict)
                    ),
                    public=isinstance(audiences, list)
                    and PUBLIC_AUDIENCE in audiences,
                )
            )
    return sorted(posts, key=lambda post: post.published, reverse=True)


def load_instance(archive: zipfile.ZipFile) -> str:
    try:
        actor = json.loads(archive.read("actor.json"))
    except KeyError as error:
        raise ValueError("The ZIP does not contain actor.json") from error
    except json.JSONDecodeError as error:
        raise ValueError("actor.json is not valid JSON") from error

    if not isinstance(actor, dict):
        raise ValueError("actor.json must contain a JSON object")
    actor_url = actor.get("url") or actor.get("id")
    if not isinstance(actor_url, str):
        raise ValueError("actor.json does not contain an actor URL")
    instance = urlparse(actor_url).hostname
    if not instance or not re.fullmatch(r"[A-Za-z0-9.-]+", instance):
        raise ValueError(f"Cannot determine a safe instance name from: {actor_url}")
    return instance.lower()


def archive_member_name(url: str) -> str:
    path = PurePosixPath(urlparse(url).path.lstrip("/"))
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe attachment path: {url}")
    return path.as_posix()


def copy_attachment(
    archive: zipfile.ZipFile,
    attachment: dict[str, object],
    post: Post,
    assets_dir: Path,
) -> tuple[str, str, str]:
    source_url = attachment.get("url")
    if not isinstance(source_url, str):
        raise ValueError(f"Post {post.external_url} has an attachment without a URL")
    source_name = archive_member_name(source_url)
    filename = f"{post.identifier}-{posixpath.basename(source_name)}"
    destination = assets_dir / filename
    try:
        source = archive.open(source_name)
    except KeyError as error:
        raise ValueError(
            f"Attachment {source_name} referenced by {post.external_url} is missing"
        ) from error
    assets_dir.mkdir(parents=True, exist_ok=True)
    with source, destination.open("wb") as output:
        shutil.copyfileobj(source, output)

    caption = attachment.get("name")
    caption_text = caption.strip() if isinstance(caption, str) else ""
    media_type = attachment.get("mediaType")
    return filename, caption_text, media_type if isinstance(media_type, str) else ""


def format_date(timestamp: datetime) -> str:
    weekdays = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    months = (
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    )
    return (
        f"{weekdays[timestamp.weekday()]} {months[timestamp.month - 1]} "
        f"{timestamp.day:02d} {timestamp:%H:%M:%S %Y}"
    )


def render_media(
    filename: str, caption: str, media_type: str, assets_url: str
) -> str:
    url = f"{assets_url.rstrip('/')}/{filename}"
    if media_type.startswith("image/"):
        return f"![{escape_link_text(caption)}]({url})"
    elif media_type.startswith("video/"):
        fallback = "Your browser does not support the video tag."
        media = f'<video controls><source src="{url}" type="{media_type}">{fallback}</video>'
    elif media_type.startswith("audio/"):
        fallback = "Your browser does not support the audio tag."
        media = f'<audio controls src="{url}">{fallback}</audio>'
    else:
        media = f"[Download attachment]({url})"
    return media


def render_page(
    archive: zipfile.ZipFile,
    posts: list[Post],
    assets_dir: Path,
    assets_url: str,
) -> str:
    entries: list[str] = []
    for post in posts:
        anchor = f"mastodon-{post.identifier}"
        sections = [f'<span id="{anchor}"></span>']
        if post.summary:
            sections.append(f"**Content warning:** {post.summary}")
        if post.in_reply_to:
            sections.append(f"Replying to [a Mastodon post]({post.in_reply_to})")
        sections.append(post.content)
        for attachment in post.attachments:
            filename, caption, media_type = copy_attachment(
                archive, attachment, post, assets_dir
            )
            sections.append(render_media(filename, caption, media_type, assets_url))
        if not post.public:
            sections.append("*Originally published to a limited audience.*")
        date = format_date(post.published)
        sections.append(
            f"[{date}]({post.external_url}) "
            f'[#](#{anchor} "Permalink to this post")'
        )
        entries.append("\n\n".join(section for section in sections if section))
    return "\n\n---\n\n".join(entries) + "\n"


def parse_args(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a Mastodon archive ZIP into a Jekyll Markdown page."
    )
    parser.add_argument("archive", type=Path, help="path to the Mastodon archive ZIP")
    parser.add_argument(
        "--output",
        type=Path,
        help="generated Markdown page (default: dated filename using the instance)",
    )
    parser.add_argument(
        "--assets-dir",
        type=Path,
        help="directory for extracted media (default: docs/img/<instance>)",
    )
    parser.add_argument(
        "--assets-url",
        help="URL prefix used in Markdown (default: /img/<instance>)",
    )
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    args = parse_args(arguments if arguments is not None else sys.argv[1:])
    if not args.archive.is_file():
        print(f"error: archive not found: {args.archive}", file=sys.stderr)
        return 2

    try:
        with zipfile.ZipFile(args.archive) as archive:
            instance = load_instance(archive)
            output = args.output or default_output(instance)
            assets_dir = args.assets_dir or default_assets_dir(instance)
            assets_url = args.assets_url or default_assets_url(instance)
            posts = load_archive(archive)
            if not posts:
                raise ValueError("The archive contains no supported posts")
            page = render_page(archive, posts, assets_dir, assets_url)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(page, encoding="utf-8")
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(
        f"Wrote {len(posts)} posts to {output} "
        f"and media assets to {assets_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
