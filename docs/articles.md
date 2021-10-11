<ul>
  {% for post in site.posts %}
    {% if post.url and post.category != "podcast" %}
        <li>{{ post.date | date: '%B %Y' }} <a href="{{ post.url }}">{{ post.title }}</a></li>
    {% endif %}
  {% endfor %}
</ul>

