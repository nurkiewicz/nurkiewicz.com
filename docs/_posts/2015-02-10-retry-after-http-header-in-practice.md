---
layout: post
title: Retry-After HTTP header in practice
date: '2015-02-10T00:00:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- Hystrix
- HTTP
modified_time: '2015-02-10T00:00:19.834+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4499131840297645259
blogger_orig_url: https://www.nurkiewicz.com/2015/02/retry-after-http-header-in-practice.html
---

`Retry-After` is a lesser known HTTP response header.
Let me quote relevant part of [RFC 2616 (HTTP 1.1 spec)](http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html):

> ### 14.37 Retry-After
>
> The `Retry-After` response-header field can be used with a `503` (*Service Unavailable*) response to indicate how long the service is expected to be unavailable to the requesting client.
> This field MAY also be used with any 3xx (Redirection) response to indicate the minimum time the user-agent is asked wait before issuing the redirected request.
> The value of this field can be either an HTTP-date or an integer number of seconds (in decimal) after the time of the response.
>
> ``` text
>    Retry-After  = "Retry-After" ":" ( HTTP-date | delta-seconds )
> ```
>
> Two examples of its use are
>
> ``` text
>    Retry-After: Fri, 31 Dec 1999 23:59:59 GMT
>    Retry-After: 120
> ```
>
> In the latter example, the delay is 2 minutes.

Although the use case with 3xx response is interesting, especially in eventually consistent systems ("*your resource will be available under this link within 2 seconds*), we will focus on error handling.
By adding `Retry-After` to response server can give a hint to the client when it will become available again.
One might argue that the server hardly ever knows when it will be back on-line, but there are several valid use cases when such knowledge can be somehow inferred:

- Planned maintenance - this one is obvious, if your server is down within scheduled maintenance window, you can send `Retry-After` from proxy with precise information when to call back.
  Clients won't bother retrying earlier, of course IF they understand and honour this header
- Queue/thread pool full - if your request must be handled by a thread pool and it's full, you can estimate when next request can be handled.
  This requires bound queue (see: [*ExecutorService - 10 tips and tricks*](http://www.nurkiewicz.com/2014/11/executorservice-10-tips-and-tricks.html), point 6.)
  and rough estimate how long it takes for one task to be handled.
  Having this knowledge you can estimate when next client can be served without queueing.
- Circuit breaker open - in Hystrix you can query
- Next available token/resource/whatever

Let's focus on one non-trivial use case.
Imagine your web service is backed by Hystrix command:

```java
private static final HystrixCommand.Setter CMD_KEY = HystrixCommand.Setter
    .withGroupKey(HystrixCommandGroupKey.Factory.asKey("REST"))
    .andCommandKey(HystrixCommandKey.Factory.asKey("fetch"));

@RequestMapping(value = "/", method = GET)
public String fetch() {
    return fetchCommand().execute();
}

private HystrixCommand<String> fetchCommand() {
    return new HystrixCommand<String>(CMD_KEY) {
        @Override
        protected String run() throws Exception {
            //...
        }
    };
}
```

This works as expected, if command fails, times out or circuit breaker is open, client will receive 503.
However in case of circuit breaker we can at least estimate how long would it take for circuit to close again.
Unfortunately there is no public API telling for how long exactly circuit will remain open in case of catastrophic failures.
But we know for how long by default circuit breaker remains open, which is a good max estimate.
Of course circuit may remain open if underlying command keeps failing.
But `Retry-After` doesn't guarantee that a server will operate upon given time, it's just a hint for the client to stop trying beforehand.
The following implementation is simple, but broken:

```java
@RequestMapping(value = "/", method = GET)
public ResponseEntity<String> fetch() {
    final HystrixCommand<String> command = fetchCommand();
    if (command.isCircuitBreakerOpen()) {
        return handleOpenCircuit(command);
    }
    return new ResponseEntity<>(command.execute(), HttpStatus.OK);
}

private ResponseEntity<String> handleOpenCircuit(HystrixCommand<String> command) {
    final HttpHeaders headers = new HttpHeaders();
    final Integer retryAfterMillis = command.getProperties()
            .circuitBreakerSleepWindowInMilliseconds().get();
    headers.set(HttpHeaders.RETRY_AFTER, Integer.toString(retryAfterMillis / 1000));
    return new ResponseEntity<>(headers, HttpStatus.SERVICE_UNAVAILABLE);
}
```

As you can see we can ask any command whether its circuit breaker is open or not.
If it's open, we set `Retry-After` header with `circuitBreakerSleepWindowInMilliseconds` value.
This solution has a subtle but disastrous bug: if circuit becomes open one day, we never run command again because we eagerly return 503.
This means Hystrix will never re-try executing it and circuit will remain open forever.
We must attempt to call command every single time and catch appropriate exception:

```java
@RequestMapping(value = "/", method = GET)
public ResponseEntity<String> fetch() {
    final HystrixCommand<String> command = fetchCommand();
    try {
        return new ResponseEntity<>(command.execute(), OK);
    } catch (HystrixRuntimeException e) {
        log.warn("Error", e);
        return handleHystrixException(command);
    }
}

private ResponseEntity<String> handleHystrixException(HystrixCommand<String> command) {
    final HttpHeaders headers = new HttpHeaders();
    if (command.isCircuitBreakerOpen()) {
        final Integer retryAfterMillis = command.getProperties()
            .circuitBreakerSleepWindowInMilliseconds().get();
        headers.set(HttpHeaders.RETRY_AFTER, Integer.toString(retryAfterMillis / 1000));
    }
    return new ResponseEntity<>(headers, SERVICE_UNAVAILABLE);
}
```

This one works well.
If command throws an exception and associated circuit is open, we set appropriate header.
In all examples we take milliseconds and normalize to seconds.
I wouldn't recommend it, but if for some reason you prefer absolute dates rather than relative timeouts in `Retry-After` header, HTTP date formatting is finally part of Java (since JDK 8):

```java
import java.time.format.DateTimeFormatter;

//...

final ZonedDateTime after5seconds = ZonedDateTime.now().plusSeconds(5);
final String httpDate = DateTimeFormatter.RFC_1123_DATE_TIME.format(after5seconds);
```

# A note about auto-DDoS

You have to be careful with `Retry-After` header if you send the same timestamp to a lot of unique clients.
Imagine it's 15:30 and you send `Retry-After: Thu, 10 Feb 2015 15:40:00 GMT` to everyone around - just because you somehow estimated that service will be up at 15:40.
The longer you keep sending the same timestamp, the bigger DDoS "attack" you can expect from clients respecting `Retry-After`.
Basically everyone will schedule retry precisely at 15:40 (obviously clocks are not perfectly aligned and network latency varies, but still), flooding your system with requests.
If your system is properly designed, you might survive it.
However chances are you will mitigate this "attack" by sending another fixed `Retry-After` header, essentially re-scheduling attack later.

That being said avoid fixed, absolute timestamps sent to multiple unique clients.
Even if you know precisely when your system will become available, spread `Retry-After` values along some time period.
Actually you should gradually let in more and more clients, so experiment with different probability distributions.

# Summary

`Retry-After` HTTP response header is neither universally known nor often applicable.
But in rather rare cases when downtime can be anticipated, consider implementing it on the server side.
If clients are aware of it as well, you can significantly reduce network traffic while improving system throughput and response times.
