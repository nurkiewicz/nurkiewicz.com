---
category: podcast
title: "#38: HTTP cookies: from saving shopping cart to online tracking"
permalink: /38
tags: cookie http javascript ssh ftp real-time-bidding
description: >
    Before we fully appreciate how important HTTP cookies are, let's imagine the web without them.
    HTTP is inherently stateless.
    This means that the HTTP server is not allowed and not capable of storing any context between requests.
    It has no memory of prior questions from the same client.
    Contrary to stateful protocols like FTP or SSH.
    They have a concept of long-running session.
    If you change the working directory during a session, subsequent commands take that into account.
    This is not the case for HTTP.
    For example, imagine you just logged in to GMail to see the list of unread e-mails.
    Now you click the most important one, from the [Nigerian prince](https://www.cnbc.com/2019/04/18/nigerian-prince-scams-still-rake-in-over-700000-dollars-a-year.html).
    Sadly, the server has no idea you are the person who just logged in.
    You must log in again.
    And again.
    This is where cookies help tremendously.
---

{% include player.html episode_id="7htJlw269oihrtZ61M6Jaw" %}

{{ page.description }}

<!--
When the server wants to keep some information in between requests, it uses cookies.
Cookies are just a tiny piece of information stored on the client.
That's right, in the browser, not the server!
The server remains stateless.
It's one of the reasons why HTTP is so prevalent.
No state means no problems with scaling, replicating, consistency.
Each web server in the cluster is identical and can be easily replaced.
In order to remember something in between requests, the server asks the browser to save arbitrary name-value pairs.
The cookie.
The browser is obligated to store such a cookie, together with the domain that set it.
When the browser makes subsequent requests to the same domain, it should send all previously stored cookies as well.
Simplifying, cookies are stored per domain, so there's no risk of accidentally revealing your shopping cart to a third party.
Actually, stealing cookies is possible, but that's a different story.

So, how is that back-and-forth useful?
Well, the server can store temporary data inside cookies.
Like, for example, the contents of your shopping cart during online checkout.
Or your browsing preferences.
Another example is aforementioned GMail login problem.
When you login for the first time, the server sends back a cookie to your browser.
The second request sends that cookie back to GMail.
When the server notices that cookie, it knows the users already logged in and can present all the secrets.

But which user logged in?
Millions of people are browsing GMail at the same time.
Naive approach simply sends back user ID as a cookie.
However, cookies are easy to steal and spoof.
If you simply send back the cookie with a different user ID, you'll successfully impersonate another user.
In practice, the server almost always uses some random identifier, known as a session ID.
That session ID is later resolved on the server.
Meaning the HTTP server needs to have some sort of a database anyway, queried by session ID.
And it's no longer stateless.

OK, but what about these annoying cookie popups in Europe?
Well, it turns out that cookies are most commonly used to track your online behaviour.
Giants like Facebook or Google use a technique known as third-party cookies.
In short, it's a dogdy hack that notifies these giants every time you open one of the millions of websites containing their tracking script.
But online tracking and real-time bidding for ads deserve a separate episode.

That's it, thanks for listening, bye!
-->

# More materials

* [HTTP cookie](https://en.wikipedia.org/wiki/HTTP_cookie) on Wikipedia
* [JWT.io](https://jwt.io/), an alternative way to session IDs
* ["Nigerian prince" email scams still rake in over $700,000 a year—here’s how to protect yourself](https://www.cnbc.com/2019/04/18/nigerian-prince-scams-still-rake-in-over-700000-dollars-a-year.html)


