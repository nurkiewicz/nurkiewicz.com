<ul>
  {% for post in site.posts %}
    {% if post.url and post.category != "podcast" %}
        <li><a href="{{ post.url }}">{{ post.title }}</a></li>
    {% endif %}
  {% endfor %}
</ul>

# Tags

{% assign tags = site.tags | sort %}
<dl>
{% for tag in tags %}
  <dt>{{ tag[0] }}</dt>
  {% for post in tag[1] %}
    <dd><a href="{{ post.url }}">{{ post.title }}</a></dd>
  {% endfor %}
{% endfor %}
</dl>
