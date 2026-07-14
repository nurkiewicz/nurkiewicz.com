---
layout: post
title: Non-blocking I/O - discovering Akka
date: '2012-11-06T18:42:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- akka
- scala
modified_time: '2012-11-06T22:45:47.946+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-977466812599275646
blogger_orig_url: https://www.nurkiewicz.com/2012/11/non-blocking-io-discovering-akka.html
image:
  path: /assets/img/non-blocking-io-discovering-akka/hero.jpg
  alt: "Waterfall on Akerselva"
---

Here comes the time to follow some good practices when implementing actors.
One of the most important rules we should follow is avoiding any blocking input/output operations, polling, busy waiting, sleeping, etc. Simply put, actor while handling a message should only depend on CPU and if it doesn't need CPU cycles it should immediately return from `receive` and let other actors to process.
If we follow this rule strictly, Akka can easily handle hundreds of thousands of messages per second using just a handful of threads.
It shouldn't come as a surprise that even though our application can comprise thousands of seemingly independent actors (e.g.
one actor per each HTTP connection, one player in MMO game, etc.), each actor gets only a limited CPU time within a pool of threads.
With default 10 threads handling all the actors in the system, one blocking or sleeping actor is enough to reduce the throughput by 10%.
Therefore 10 actors sleeping at the same time completely halt the system.

For that reason calling `sleep()` or actively waiting for a response from some other actor is highly discouraged within `receive`.
Unfortunately there is no mature asynchronous library equivalent to JDBC (but watch [postgresql-netty](https://github.com/mauricio/postgresql-netty), [adbcj](http://code.google.com/p/adbcj/), [async-mysql-connector](http://code.google.com/p/async-mysql-connector/) and also related: [mongodb-async-driver](http://www.allanbank.com/mongodb-async-driver/)) and using NIO is rather problematic.
But we should seek for alternatives and avoid blocking code whenever possible.
In [our sample application](http://nurkiewicz.blogspot.no/2012/11/becomeunbecome-discovering-akka.html) fetching random numbers from external web service was implemented in quite naive way:

```scala
val url = new URL("https://www.random.org/integers/?num=" + batchSize + "&min=0&max=65535&col=1&base=10&format=plain&rnd=new")
val connection = url.openConnection()
val stream = Source.fromInputStream(connection.getInputStream)
sender ! RandomOrgServerResponse(stream.getLines().map(_.toInt).toList)
stream.close()
```

This code blocks waiting for an HTTP reply for [up to one minute](http://nurkiewicz.blogspot.no/2012/10/your-first-message-discovering-akka.html).
This means our actor can't handle any other message for several seconds.
Moreover it holds one thread (by default out of ten) from Akka worker pool.
This pool is suppose to be shared among thousands of actors, so that feels a bit selfish.

Luckily mature asynchronous HTTP client libraries exist, namely [async-http-client](https://github.com/AsyncHttpClient/async-http-client) (based on [netty](https://netty.io/), with [Scala wrapper called Dispatch](http://dispatch.databinder.net/Dispatch.html)) and [Jetty HttpClient](http://wiki.eclipse.org/Jetty/Tutorial/HttpClient).
For test purposes we'll use the first one (and leave Dispatch for later).
API is quite obvious: it asks us for target URL and a callback object, which will be used when reply arrives.
Thus sending HTTP request is asynchronous and non-blocking (actor can quickly consume more incoming messages) and the response arrives asynchronously from a different thread:

```scala
implicit def block2completionHandler[T](block: Response => T) = new AsyncCompletionHandler[T]() {
  def onCompleted(response: Response) = block(response)
}

def receive = {
  case FetchFromRandomOrg(batchSize) =>
    val curSender = sender
    val url = "https://www.random.org/integers/?num=" + batchSize + "&min=0&max=65535&col=1&base=10&format=plain&rnd=new"
    client.prepareGet(url).execute {
      response: Response =>
        val numbers = response.getResponseBody.lines.map(_.toInt).toList
        curSender ! RandomOrgServerResponse(numbers)
    }
}
```

We are very close to really dangerous bug in the code above.
Notice how I make a local copy of `sender` called `curSender`.
If I wouldn't do this, the block of code executed when a response arrives would read **current** value of `sender`.
*Current*, that is if our actor was handling some other message at a time, it would point to a sender of that other message.
As a side note that's one of the reasons why variables accessed from anonymous inner classes in Java have to be `final`.
It's also a good reason to avoid arbitrary code blocks called asynchronously inside actors.
It's much better to extract them to a separate class outside of the actor to avoid accidental access to internal actor state.

Let's leave our example for a while.
Imagine how scalable our general architecture would be for a general RSS/Atom feed reader as a service.
For each feed URL we can create one actor (and we monitor thousands of feeds, thus that many actors).
Actor sends an asynchronous request to each site and waits for a response.
Theoretically using just one worker thread we can handle thousands of feeds/servers, processing the results on the fly as they come (after all each server has a different response time).
In a classic, blocking model we can only process as many feeds concurrently as many threads we can use (certainly not several thousands), not to mention each thread requires significant amount of memory.

If you see some similarities to [node.js](http://nodejs.org/) you are on the right track.
This framework is based entirely on asynchronous I/O, thus being able to handle large amount of concurrent connections using only one (!)
thread.

Source code for this article is [available on GitHub](https://github.com/nurkiewicz/learning-akka) in [`non-blocking-io` tag](https://github.com/nurkiewicz/learning-akka/tree/non-blocking-io).

> This was a translation of my article ["*Poznajemy Akka: nieblokujące I/O*"](http://scala.net.pl/poznajemy-akka-nieblokujace-io/) originally published on [scala.net.pl](http://scala.net.pl/).
