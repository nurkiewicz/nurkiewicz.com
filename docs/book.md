---
layout: page
title: My book
permalink: /book
---

{% include book.md %}

## Community feedback

{% assign feedback = site.pages | where: "path", "rxjava.md" | first %}
{{ feedback.content }}
