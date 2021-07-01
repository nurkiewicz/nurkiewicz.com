<ul>
    {% for post in site.categories.podcast %}
      {% if post.url %}
        <li>
          <a href="{{ post.url }}">{{ post.title }}</a>
        </li>
      {% endif %}
    {% endfor %}
  </ul>