SHELL = /bin/bash
RUBY_HOME = /opt/homebrew/opt/ruby@3.3
export PATH := $(RUBY_HOME)/bin:$(PATH)

serve:
	cd docs && \
		bundle install && \
		bundle exec jekyll serve --drafts --incremental

build:
	cd docs && bundle exec jekyll build

test:
	cd docs && bundle exec jekyll build
