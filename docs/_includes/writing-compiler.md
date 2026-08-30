## Write yourself a compiler series

{% assign articles = site.categories.writing-compiler | sort: "date" %}
<ol>
  {% for article in articles %}
    {% assign article_title = article.title | split: ": Write yourself a compiler" | first %}
    <li>
      {% if article.url == page.url %}
        <strong><a href="{{ article.url | relative_url }}">{{ article_title }}</a></strong>
      {% else %}
        <a href="{{ article.url | relative_url }}">{{ article_title }}</a>
      {% endif %}
    </li>
  {% endfor %}
</ol>
