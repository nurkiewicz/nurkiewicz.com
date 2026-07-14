---
layout: post
title: 'Reactive emoji tracker with WebClient and Reactor: consuming SSE'
date: '2018-02-02T01:11:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- emojitracker
- reactor
- spring
- emoji
- webclient
modified_time: '2018-02-07T00:31:34.298+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1824214589404611048
blogger_orig_url: https://www.nurkiewicz.com/2018/02/reactive-emoji-tracker-with-webclient.html
---

In this article we will learn how to consume infinite [SSE (server-sent events)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) stream with [Spring's `WebClient`](https://docs.spring.io/spring/docs/current/spring-framework-reference/web-reactive.html#webflux-client) and [Project Reactor](https://projectreactor.io/).
`WebClient` is a new HTTP client in Spring 5, entirely asynchronous and natively supporting `Flux` and `Mono` types.
You can technically open thousands of concurrent HTTP connections with just a handful of threads.
In standard `RestTemplate` one HTTP connection always needs at least one thread.

As an example, let's connect to this cute little site called [emojitracker.com](http://emojitracker.com/).
It shows emojis being used in real-time on Twitter.
Looks quite cool!
All credits go to [Matthew Rothenberg](http://mroth.info/), the creator of that site.
It's very dynamic so there obviously has to be some push mechanism underneath.
I wore my hacker glasses and after hours of penetration testing, I discovered the following URL in Chrome DevTools: `http://emojitrack-gostreamer.herokuapp.com/subscribe/eps`.
If you connect to it, you'll get a fast stream of emoji counters:

```console
$ curl -v http://emojitrack-gostreamer.herokuapp.com/subscribe/eps
> GET /subscribe/eps HTTP/1.1
> Host: emojitrack-gostreamer.herokuapp.com
> User-Agent: curl/7.54.0
> Accept: */*
> 
< HTTP/1.1 200 OK
< Connection: keep-alive
< Content-Type: text/event-stream; charset=utf-8
< Transfer-Encoding: chunked
<
data:{"1F3C6":1,"1F440":1,"1F64F":1}

data:{"267B":1}

data:{"1F4B0":1}

data:{"267B":2}

data:{"1F49B":1,"1F612":1}

data:{"1F331":1,"1F44D":1,"1F49E":1,"1F4F9":1,"1F51E":1,"1F525":1}

data:{"1F609":1}

data:{"2764":1}

data:{"1F331":1,"267B":2}

data:{"1F498":1,"1F60A":1}
```

Dozens of data points per second, ready to be consumed via convenient [SSE](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) stream.
Each event represent the number of emojis that appeared on Twitter since last event.
For example `{"1F604":1,"267B":2}` means "😄" once and "♻" twice.
We would like to read this stream in Java efficiently and make something useful out of it.
Well, maybe not *useful* (it's emojis after all) but at least fun.
Consuming SSE stream with `WebClient` is pretty simple:

```java
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.reactive.function.client.WebClient;

public static void main(String[] args) throws InterruptedException {
    final Flux<ServerSentEvent> stream = WebClient
            .create("http://emojitrack-gostreamer.herokuapp.com")
            .get().uri("/subscribe/eps")
            .retrieve()
            .bodyToFlux(ServerSentEvent.class);
    
    stream.subscribe(sse -> log.info("Received: {}", sse));

    TimeUnit.MINUTES.sleep(10);
}
```

`sleep(10)` is important.
Otherwise the application terminates immediately because the only non-daemon thread (`main`) dies.
In web applications this is not a problem.

At this point you'll see a bunch of logs appearing on your console:

```text
Received: ServerSentEvent [... data={1F1EC-1F1E7=1, 1F614=1, 2764=1}]
Received: ServerSentEvent [... data={1F49C=1}]
Received: ServerSentEvent [... data={1F605=1, 1F60D=1, 1F60E=1, 2665=1}]
Received: ServerSentEvent [... data={267B=2}]
Received: ServerSentEvent [... data={1F1FA-1F1F8=1, 1F34B=1, 1F604=1, 1F608=1, 1F60A=1, 25B6=1}]
Received: ServerSentEvent [... data={1F525=1, 1F602=1, 25B6=1, 2705=1, 274C=1}]
Received: ServerSentEvent [... data={267B=1}]
```

Being able to connect to live SSE stream, let's apply some transformations on top of it.
First of all, we would like to parse JSON `data` inside of each message pushed from the server:

```java
final Flux<Map<String, Integer>> stream = WebClient
         //...see above for missing lines...
        .bodyToFlux(ServerSentEvent.class)
        .flatMap(e -> Mono.justOrEmpty(e.data()))
        .map(x -> (Map<String, Integer>)x);
```

There's no JSON parsing, Spring does it's magic for us!
At this point we have a stream of `Map<String, Integer>` instances, not raw `ServerSentEvent` classes.
Two caveats.
First of all we need `flatMap(e -> Mono.justOrEmpty(e.data()))` rather than just a simple `map(ServerSentEvent::data)` because `ServerSentEvent.data()` sometimes returns `null`.
Secondly `.map(x -> (Map<String, Integer>)x)` needs to be used as opposed to simple `.cast(Map.class)` because of type erasure.
Alright, our stream is a bit too complex right now.
Rather than having three-dimensional data (event contains map, map contains entries, entries contain count) we'd like to have a single event per each emoji appearence.
Easy!

```java
final Flux<Map.Entry<String, Integer>> stream = WebClient
         //...see above for missing lines...
        .flatMap(e -> Mono.justOrEmpty(e.data()))
        .map(x -> (Map<String, Integer>) x)
        .flatMapIterable(Map::entrySet);
```

We get stream of map entries (`Map.Entry<String, Integer>`), then...

```java
final Flux<String> stream = WebClient
         //...see above for missing lines...
        .map(x -> (Map<String, Integer>) x)
        .flatMapIterable(Map::entrySet)
        .flatMap(entry -> Flux.just(entry.getKey()).repeat(entry.getValue()));
```

With just few lines of code we transformed one event: `{"1F604":1,"267B":2}` into three: `"1F604"`, `"267B"`, `"267B"`.
I was feeling a bit guilty at this point, reverse-engineering the [emojitracker.com](http://emojitracker.com/).
Then I discovered that the [source code](https://github.com/mroth/emojitracker) of the website is on GitHub and the API [is documented](https://github.com/mroth/emojitrack-streamer-spec).
Moreover, there is already an endpoint that sends individual emojis, as opposed to aggregated JSON maps:

```console
$ curl -v http://emojitrack-gostreamer.herokuapp.com/subscribe/raw
> GET /subscribe/raw HTTP/1.1
> Host: emojitrack-gostreamer.herokuapp.com
> User-Agent: curl/7.54.0
> Accept: */*
> 
< HTTP/1.1 200 OK
< Connection: keep-alive
< Content-Type: text/event-stream; charset=utf-8
< Transfer-Encoding: chunked
< 
data:1F604

data:267B

data:2665

data:1F60E

...
```

You know what they say, hours of coding can save you from minutes of reading the documentation.
But we had fun!
The full source code we have so far looks as follows:

```java
final Flux<String> stream = WebClient
        .create("http://emojitrack-gostreamer.herokuapp.com")
        .get().uri("/subscribe/eps")
        .retrieve()
        .bodyToFlux(ServerSentEvent.class)
        .flatMap(e -> Mono.justOrEmpty(e.data()))
        .map(x -> (Map<String, Integer>) x)
        .flatMapIterable(Map::entrySet)
        .flatMap(entry -> Flux.just(entry.getKey()).repeat(entry.getValue()));

stream.subscribe(sse -> log.info("Received: {}", sse));

TimeUnit.SECONDS.sleep(10);
```

In the [next part](http://www.nurkiewicz.com/2018/02/reactive-emoji-tracker-with-webclient_7.html) we will parse the emoji data even further and run some aggregations on top of it.
All using `Flux`es magic.
