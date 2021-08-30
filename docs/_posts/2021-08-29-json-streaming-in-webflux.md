---
title: "3 techniques to stream JSON in Spring WebFlux"
tags: Reactor FAQ JSON streaming HTTP SSE
layout: post
---

Returning large JSON arrays from WebFlux endpoint is a challenge.
Assume you have a `Flux<Data>` that you want to return.
We have at least three options:

* Returning one large JSON array as individual document
* [Server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) pushing individual items as events
* Streaming individual events separated by newlines (_status quo_ [seems to be](https://github.com/spring-projects/spring-framework/issues/21283) `application/x-ndjson` as `Content-Type`)

We can also use [WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API), but they seem like an overkill in this scenario.
Another challenge is error-handling.
What should we do when a stream fails after a few successful events being emitted?
Let's consider this simple endpoint for testing purposes.
The [complete source code is available on GitHub](https://github.com/nurkiewicz/json-streaming):

```java
package com.nurkiewicz.jsonstreaming;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

import java.time.Duration;
import java.time.Instant;

import static org.springframework.http.MediaType.APPLICATION_NDJSON_VALUE;
import static org.springframework.http.MediaType.TEXT_EVENT_STREAM_VALUE;

@RestController
public class StreamingController {

    @GetMapping(produces = TEXT_EVENT_STREAM_VALUE)
    Flux<Data> sse() {
        return source();
    }

    @GetMapping(produces = APPLICATION_NDJSON_VALUE)
    Flux<Data> ndjson() {
        return source();
    }

    @GetMapping
    Flux<Data> json() {
        return source();
    }

    private Flux<Data> source() {
        return Flux.interval(Duration.ofSeconds(1))
                .take(5)
                .map(i -> new Data(i, Instant.now()));
    }

}
```

Returning `Flux<String>` [behaves unexpectedly](https://github.com/spring-projects/spring-framework/issues/20807).
So I'm publishing a stream of simple `Data` classes:

```java
class Data {
    private final long seqNo;
    private final Instant timestamp;

    //...

}
```

Notice how I return the same `Flux<Data>` from multiple endpoints.
The only difference is `Content-Type` that we declare: `text/event-stream`, `application/x-ndjson`, and default `application/json`.
How do these endpoints behave?

## SSE

```bash
$ curl -v -H "Accept: text/event-stream" http://localhost:8080
> GET / HTTP/1.1
> Host: localhost:8080
> Accept: text/event-stream
>
< HTTP/1.1 200 OK
< transfer-encoding: chunked
< Content-Type: text/event-stream;charset=UTF-8
<
data:{"seqNo":0,"timestamp":"2021-08-29T18:51:25.392405Z"}

data:{"seqNo":1,"timestamp":"2021-08-29T18:51:26.392252Z"}

data:{"seqNo":2,"timestamp":"2021-08-29T18:51:27.392769Z"}

data:{"seqNo":3,"timestamp":"2021-08-29T18:51:28.391455Z"}

data:{"seqNo":4,"timestamp":"2021-08-29T18:51:29.392768Z"}
```

This is a standard SSE stream with each object from `Flux` in a separate `data:` line.
SSE can be easily consumed by the client, [including JavaScript](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events).
It's worth mentioning that SSE supports any content, not only JSON.

## [NDJSON](https://github.com/ndjson/ndjson-spec) - Newline delimited JSON

This is a fairly new approach that is not well-established yet.
It's similar to SSE, but much simpler.
Basically, rather than returning a JSON array with individual items, we return each item as a separate JSON document.
Each line of the output is a well-formatted JSON document.
There are no enclosing square brackets.
See:

```bash
$ curl -v -H "Accept: application/x-ndjson" http://localhost:8080
> GET / HTTP/1.1
> Host: localhost:8080
> Accept: application/x-ndjson
>
< HTTP/1.1 200 OK
< transfer-encoding: chunked
< Content-Type: application/x-ndjson
<
{"seqNo":0,"timestamp":"2021-08-29T18:52:29.908091Z"}
{"seqNo":1,"timestamp":"2021-08-29T18:52:30.907809Z"}
{"seqNo":2,"timestamp":"2021-08-29T18:52:31.906204Z"}
{"seqNo":3,"timestamp":"2021-08-29T18:52:32.907935Z"}
{"seqNo":4,"timestamp":"2021-08-29T18:52:33.908153Z"}
```

Look carefully!
Each line is a standalone, valid JSON.
However, the whole response body is not a valid JSON.
It's just a collection of JSON documents separated by newlines.

## "Classic" JSON

Last but not least, how does Spring WebFlux treat `Flux<Data>` when no `Content-Type` hints are given?

```bash
~ curl -v  http://localhost:8080 | jq .
> GET / HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/7.64.1
> Accept: */*
>
< transfer-encoding: chunked
< Content-Type: application/json
<
[
  {
    "seqNo": 0,
    "timestamp": "2021-08-29T18:55:40.792996Z"
  },
  {
    "seqNo": 1,
    "timestamp": "2021-08-29T18:55:41.792843Z"
  },
  {
    "seqNo": 2,
    "timestamp": "2021-08-29T18:55:42.794316Z"
  },
  {
    "seqNo": 3,
    "timestamp": "2021-08-29T18:55:43.795363Z"
  },
  {
    "seqNo": 4,
    "timestamp": "2021-08-29T18:55:44.794723Z"
  }
]
```

This is something we are most familiar with.
Spring WebFlux simply takes all items and builds an array out of them.
Internally it calls `Flux.collectList()` that turns `Flux<T>` into `Mono<List<T>>`.
Once we have all individual items collected together, we simply build a JSON array out of them.
The `collectList` has three huge side effects that we'll discuss further [in the next article]({% post_url 2021-08-30-error-handling-in-json-streaming-with-webflux %}):

* No support for infinite streams (something typical for SSE/NDJSON)
* [TTFB](https://developer.mozilla.org/en-US/docs/Glossary/time_to_first_byte) ("_time to first byte_") is worse
* Error handling is more strict