---
title: "#21: SEE and WebSockets"
permalink: /21
tags: sse websocket http EventSource
description: >
    HTTP is historically request-response-driven.
    This means a server is idle as long as no-one asks it to do something.
    Typically fetching data or accepting some form.
    In reality, we'd often like to receive data from the server without any request.
    Typically to subscribe for some server-side updates.
    For example displaying a current price on the stock exchange that changes many times per second.
    Or when waiting for some asynchronous process to complete.
    Traditionally this could be achieved with a few hacks.
    The most obvious and the worst one is busy-waiting.
    You simply keep asking the server over and over again periodically.
    More frequent requests result in a lot of excessive network traffic.
    Less frequent requests increase latency, so it's no longer real-time communication.
---

{% include player.html episode_id="4Aj3diNw4Xd7VifYsDU0GS" %}

{{ page.description }}

<!--
A slightly smarter approach is long-polling.
In this implementation you periodically ask the server whether there is some new data.
To avoid excessive round-trips, the server doesn't respond until some update is available.
Or, after a timeout, it sends back an empty response and the loop continues.

Now Server-sent events try to clean things up.
SSE standardizes push technology by defining the protocol and JavaScript API.
First of all, the browser sends an HTTP request to SSE endpoint.
In return, the server returns a response with no content length.
Not a surprise, from now on the server keeps sending chunks of data in a never-ending response body.
Each chunk is prepended with `data` prefix and can contain arbitrary text data.
Typically JSON.
The JavaScript API called `EventSource` is notified every time the server decided to push some data.

SSE is quite simple and lightweight.
One disadvantage is it's one-directional.
You just make a single HTTP GET request and receive a stream of updates.
If you need something more sophisticated, WebSockets are needed.
WebSocket is essentially a bi-directional, binary stream of data.
...Implemented inside HTTP protocol.
...That itself is implemented on top of bi-directional, binary TCP/IP protocol.
Go figure!
Anyway, with WebSockets you start with an ordinary HTTP connection over port 80 or 443.
However, the browser sends a special upgrade request header.
If the server understands that header, it responds with `HTTP 101 Switching Protocols` header.
From now on the HTTP connection becomes fully-fledged, message-oriented, bi-directional, binary channel.

Why all the hassle, rather than using, you know, TCP/IP sockets?
Well, HTTP is ubiquitous in browsers, servers and proxies.
Tunneling WebSockets over HTTP means you can bypass firewalls and proxies that only speak HTTP.
Also, for security reasons, browsers aren't allowed to open arbitrary TCP/IP connections.
But once we have WebSocket connection upgraded, for the price of a tiny packet envelope, we get a full-blown connection.
At this point both the browser and the server are free to send data to each other.
WebSockets are great to implement bi-directional communication.
This includes chats, real-time collaboration tools and online games.

To be honest, there's one more technology.
The creators of HTTP/2 realized that when we rarely ask for HTML alone.
Most of the time the browser, after parsing HTML, will request various scripts, stylesheets and images found there.
This extra network round-trip is unnecessary.
If we know in advance that the browser will make subsequent requests, let's be proactive!
This is called HTTP/2 server push.
The server eagerly pushes resources to the client that it knows will be needed anyway.
This greatly reduces the perceived latency.
If you want to know more, I covered the history of HTTP protocol in episode 10.

That's it, thanks for listening, bye!


-->

# More materials

* [Busy waiting](https://en.wikipedia.org/wiki/Busy_waiting)
* [Push technology](https://en.wikipedia.org/wiki/Push_technology)
* [Server-sent events](https://en.wikipedia.org/wiki/Server-sent_events)
* [Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
* [Websockets 101](https://lucumr.pocoo.org/2012/9/24/websockets-101/)
* [emojitracker](http://emojitracker.com/) - a showcase of SSE in action
* [HTTP/2 Server Push](https://en.wikipedia.org/wiki/HTTP/2_Server_Push)


{% include newsletter-input.md %}
