<ul>
  {% for post in site.posts %}
    {% if post.url and post.category != "podcast" %}
        <li><a href="{{ post.url }}">{{ post.title }}</a></li>
    {% endif %}
  {% endfor %}
</ul>

