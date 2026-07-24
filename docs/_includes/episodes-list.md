<a href="https://podcasts.apple.com/us/podcast/around-it-in-256-seconds/id1510899104?itsct=podcast_box_badge&amp;itscg=30200&amp;ls=1">
    <img src="img/US_UK_Apple_Podcasts_Listen_Badge_RGB.svg" alt="Listen on Apple Podcasts">
</a>
<a href="https://podcasts.google.com/feed/aHR0cHM6Ly9hbmNob3IuZm0vcy8xNTVlNzEzNC9wb2RjYXN0L3Jzcw">
    <img src="img/EN_Google_Podcasts_Badge.svg" alt="Listen on Google Podcasts">
</a>
<a href="https://open.spotify.com/show/2WTzG4ef4L5GDSBf7IB2tJ">
    <img src="img/spotify-podcast-badge-wht-grn-165x40.svg" alt="Listen on Spotify">
</a>
<a href="https://www.amazon.com/Around-IT-in-256-seconds/dp/B08K4TRK71">
    <img src="img/US_ListenOn_AmazonMusic_button_white_RGB_5X.png" alt="Listen on Amazon Music">
</a>
<a href="https://anchor.fm/s/155e7134/podcast/rss">
  <img src="img/rss-icon.png" alt="RSS icon"/>
</a>


<ul>
    {% for post in site.categories.podcast %}
      {% if post.url %}
        <li>
          <a href="{{ post.url }}">{{ post.title }}</a>
        </li>
      {% endif %}
    {% endfor %}
  </ul>
