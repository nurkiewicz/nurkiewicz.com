SHELL = /bin/bash

serve:
	cd docs && \
		bundle install && \
		bundle exec jekyll serve --drafts --incremental
