ls -1U *.md | tail -n1 | xargs -I '{}' cp {} `date +'%Y-%m-%d-new.md'`
