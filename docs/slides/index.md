---
title: Slides
permalink: /slides/
---

{% assign current_slides = site.static_files | where: "extname", ".html" | where_exp: "file", "file.path contains '/slides/'" | where_exp: "file", "file.name != 'index.html'" %}

{% assign old_slides_temp = site.static_files | where: "extname", ".html" | where_exp: "file", "file.path contains '/slides-old/'" %}

{% assign old_slides = "" | split: "" %}
{% for slide in old_slides_temp %}
  {% unless slide.path contains '/plugin/' or slide.path contains '/test/' %}
    {% if slide.name == 'index.html' or slide.name == 'english.html' or slide.name == 'en.html' %}
      {% assign old_slides = old_slides | push: slide %}
    {% endif %}
  {% endunless %}
{% endfor %}

{% assign all_slides = current_slides | concat: old_slides | sort: "name" %}

<ul>
{% for slide in all_slides %}
  {% if slide.path contains '/slides-old/' %}
    {% assign display_path = slide.path | remove_first: '/slides-old/' %}
  {% else %}
    {% assign display_path = slide.name %}
  {% endif %}
  <li>
    <a href="{{ slide.path | relative_url }}">{{ display_path }}</a>
  </li>
{% endfor %}
</ul>
