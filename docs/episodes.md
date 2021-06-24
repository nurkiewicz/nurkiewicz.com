{% include episodes-list.md %}

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

