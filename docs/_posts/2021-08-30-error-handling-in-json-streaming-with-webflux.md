---
title: "JSON streaming and error handling with Spring WebFlux"
tags: Reactor FAQ JSON streaming HTTP SSE TTFB
description: How different techniques of JSON streaming in WebFlux affect TTFB and error handling?
layout: post
---

[In the previous article]({% post_url 2021-08-29-json-streaming-in-webflux %}) we discussed three ways to return a `Flux<T>` from an endpoint.
To recap:

* Returning one large JSON array as individual document
* [Server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) pushing individual items as events
* Streaming individual events separated by lines (_status quo_ [seems to be](https://github.com/spring-projects/spring-framework/issues/21283) `application/x-ndjson` as `Content-Type`)

We saw how the response differs depending on which technique we used.
However, there are two other aspects that we need to discuss.

## [Time to first byte](https://developer.mozilla.org/en-US/docs/Glossary/time_to_first_byte) (TTFB)

This important client-side metric tells how much time elapsed between sending a request and receiving the very first byte of the response.
Notice that TTFB is smaller than:

* time to response (how much time it took to receive the complete body)
* time to receive all headers
* time to receive the first byte of the body

Our [source of data](https://github.com/nurkiewicz/json-streaming/blob/master/src/main/java/com/nurkiewicz/jsonstreaming/StreamingController.java) returns 5 items, the first one after 1 second, the last one after 5 seconds:

```java
private Flux<Data> source() {
    return Flux.interval(Duration.ofSeconds(1))
            .take(5)
            .map(i -> new Data(i, Instant.now()));
}
```

In the case of SSE and NDJSON, TTFB is 1 second.
I expected WebFlux to return 200 OK immediately, but it's good anyway.
Both SSE and NDJSON keep pushing new items once per second.

Imagine the source `Flux` was coming from a database that gradually produces more and more results over time.
These two endpoints will stream the data on the fly, so that client can consume the results even before the query completion.
This is big, it improves responsiveness and fault-tolerance, as we'll see in a second.

Sadly, standard `application/json` doesn't work this way.
Instead, WebFlux first [waits for everything](https://github.com/spring-projects/spring-framework/blob/v5.3.9/spring-web/src/main/java/org/springframework/http/codec/json/AbstractJackson2Encoder.java#L187) by invoking `collectList()` on your `Flux`.
Once the source `Flux<Data>` is completed successfully, only then we'll receive some data.

So TTFB is 5 seconds, the amount of time it takes to produce all data.
Moreover, SSE and NDJSON support infinite streams.
Of course `application/json` does not.
But even worse, we must buffer the whole response buffer we can send it to the client.

## Error handling

TTFB is not the only problem.
What if our stream fails after emitting a few values?
For SSE and NDJSON this is rather typical.
The HTTP response terminates unexpectedly after pushing a few events.
No hard feelings, we sent some data, the client consumed it, and then we failed.
Maybe after retrying we can continue where we left of last time?

Imagine a database query that managed to produce 99% of the results, but then the network failed.
99% of data was already transferred from the database, through the backend, to the client.

OK, it's somewhat misleading to receive 200 OK and a response interrupted half-way.
So it's probably a good idea to indicate an error with some special events.

But the situation is much worse when returning an ordinary JSON.
Spring WebFlux must wait for the whole stream to complete.
And if it fails after receiving 99% of the data, we must discard all this work.
The client gets HTTP 5xx as if everything failed.

One might think that standard JSON is the only approach where we actually know how much data to expect.
If the connection is terminated half-way, JSON is invalid and the client is aware of it.
That's true, but for some reason WebFlux doesn't return `Content-Length` for `Flux<Data>`.
This is perfectly understandable for SSE/NDJSON where we don't know the size of output in advance by definition.
But here?

## Which technique to choose?

* Use standard JSON if you care about compatibility and ease of use.
Other techniques are less common (especially NDJSON) and not supported so well.
Also, JSON is the only reliable approach if you want to be sure that all data from the server was received (!)

* Use SSE if you believe your source can produce a lot of data over a long period of time.
SSE is especially useful for updating the progress of long-running processes or producing never-ending updates.

* NDJSON is relatively new, I can't find many advantages of it over SSE.
Maybe with some low-level HTTP clients it's easier to parse newline-separated output, as opposed to slightly more complex SSE?
