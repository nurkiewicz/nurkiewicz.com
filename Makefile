SHELL = /bin/bash
RUBY_HOME = /opt/homebrew/opt/ruby@3.3
GEM_BIN = /opt/homebrew/lib/ruby/gems/3.3.0/bin
export PATH := $(RUBY_HOME)/bin:$(GEM_BIN):$(PATH)

serve:
	cd docs && \
		bundle install && \
		bundle exec jekyll serve --drafts --incremental
