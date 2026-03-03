---
title: Slides
permalink: /slides/
---

{% assign all_slides = site.static_files | where: "extname", ".html" | where_exp: "file", "file.path contains '/slides/'" | where_exp: "file", "file.name != 'index.html'" | sort: "name" %}

<ul>
{% for slide in all_slides %}
  <li>
    <a href="{{ slide.path | relative_url }}">{{ slide.name }}</a>
  </li>
{% endfor %}
</ul>
