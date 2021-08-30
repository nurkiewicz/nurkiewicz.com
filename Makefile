SHELL = /bin/bash

serve:
	cd docs && bundle exec jekyll serve --drafts --incremental
