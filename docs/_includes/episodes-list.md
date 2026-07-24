[Apple Podcasts](https://podcasts.apple.com/us/podcast/around-it-in-256-seconds/id1510899104?itsct=podcast_box_badge&amp;itscg=30200&amp;ls=1) | 
[Google Podcasts](https://podcasts.google.com/feed/aHR0cHM6Ly9hbmNob3IuZm0vcy8xNTVlNzEzNC9wb2RjYXN0L3Jzcw) | 
[Spotify](https://open.spotify.com/show/2WTzG4ef4L5GDSBf7IB2tJ) | 
[Amazon Music](https://www.amazon.com/Around-IT-in-256-seconds/dp/B08K4TRK71) | 
[RSS"](https://anchor.fm/s/155e7134/podcast/rss) 

<ul>
    {% for post in site.categories.podcast %}
      {% if post.url %}
        <li>
          <a href="{{ post.url }}">{{ post.title }}</a>
        </li>
      {% endif %}
    {% endfor %}
  </ul>
