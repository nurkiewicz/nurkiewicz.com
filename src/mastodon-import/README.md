# Mastodon archive importer

Converts a Mastodon archive ZIP into a Jekyll Markdown page matching the
structure of the site's Twitter archive. It derives the instance hostname from
`actor.json`, preserves media captions, and adds both local permalinks and
links to the original Mastodon posts.

Run from any directory:

```bash
src/mastodon-import/run.sh ~/Downloads/mastodon-archive.zip
```

`run.sh` creates and uses `src/mastodon-import/.venv`. The importer only uses
Python's standard library, so no package installation is required.

By default an archive from `mastodon.social` produces
`docs/_posts/YYYY-MM-DD-mastodon.social-archive.md` and copies media to
`docs/img/mastodon.social`. Use `--output`, `--assets-dir`, and `--assets-url`
to override the generated paths.
