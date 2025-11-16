---
title: Slides
permalink: /slides/
---

{% assign current_slides = site.static_files | where: "extname", ".html" | where_exp: "file", "file.path contains '/slides/'" | where_exp: "file", "file.name != 'index.html'" %}

{% assign old_slides = site.static_files | where: "extname", ".html" | where_exp: "file", "file.path contains '/slides-old/'" | where_exp: "file", "file.name == 'index.html' or file.name == 'english.html' or file.name == 'en.html'" | where_exp: "file", "file.path contains '/plugin/' == false and file.path contains '/test/' == false" %}

{% assign all_slides = current_slides | concat: old_slides | sort: "name" %}

<ul>
{% for slide in all_slides %}
  <li>
    <a href="{{ slide.path | relative_url }}">{{ slide.name }}</a>
  </li>
{% endfor %}
</ul>
