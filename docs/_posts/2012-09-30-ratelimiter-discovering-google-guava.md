---
layout: post
title: RateLimiter - discovering Google Guava
date: '2012-09-30T23:35:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- guava
- servlets
- performance
modified_time: '2012-10-03T09:40:15.809+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-9215184737593243408
blogger_orig_url: https://www.nurkiewicz.com/2012/09/ratelimiter-discovering-google-guava.html
image:
  path: /assets/img/ratelimiter-discovering-google-guava/hero.jpg
  alt: "Bogstadvannet, golf course"
---

[`RateLimiter`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/util/concurrent/RateLimiter.html) class was recently added to [Guava libraries](https://code.google.com/p/guava-libraries/) (since 13.0) and it is already among my favourite tools.
Have a look what the JavaDoc says:

> \[...\]
> rate limiter distributes permits at a configurable rate.
> Each `acquire()` blocks if necessary until a permit is available \[...\]
> Rate limiters are often used to restrict the rate at which some physical or logical resource is accessed

Basically this small utility class can be used e.g. to limit the number of requests per second your API wishes to handle or to throttle your own client code, avoiding [denial of service](http://en.wikipedia.org/wiki/Denial-of-service_attack) of someone else's API if we are hitting it too often.
Let's start from a simple example.
Say we have a long running process that needs to broadcast its progress to supplied listener:

```scala
def longRunning(listener: Listener) {
    var processed = 0
    for(item <- items) {
        //..do work...
        processed += 1
        listener.progressChanged(100.0 * processed / items.size)
    }
}

trait Listener {
    def progressChanged(percentProgress: Double)
}
```

Please forgive me the imperative style of this Scala code, but that's not the point.
The problem I want to highlight becomes obvious once we start our application with some concrete listener:

```scala
class ConsoleListener extends Listener {
    def progressChanged(percentProgress: Double) {
        println("Progress: " + percentProgress)
    }
}

longRunning(new ConsoleListener)
```

Imagine that `longRunning()` method processes millions of `items` but each iteration takes just a split of a second.
The amount of logging messages is just insane, not to mention console output is probably taking much more time than processing itself.
You've probably faced such a problem several times and have a simple workaround:

```scala
if(processed % 100 == 0) {
    listener.progressChanged(100.0 * processed / items.size)
}
```

*There, I Fixed It!*
We only print progress every 100th iteration.
However this approach has several drawbacks:

- code is polluted with unrelated logic
- there is no guarantee that every 100th iteration is slow enough...
- ...
  or maybe it's too slow?

What we really want to achieve is to limit the frequency of progress updates (say: two times per second).
OK, going deeper into the rabbit hole:

```scala
def longRunning(listener: Listener) {
    var processed = 0
    var lastUpdateTimestamp = 0L
    for(item <- items) {
        //..do work...
        processed += 1
        if(System.currentTimeMillis() - lastUpdateTimestamp > 500) {
            listener.progressChanged(100.0 * processed / items.size)
            lastUpdateTimestamp = System.currentTimeMillis()
        }
    }
}
```

Do you also have a feeling that we are going in the wrong direction?
Ladies and gentlemen, I give you `RateLimiter`:

```scala
var processed = 0
val limiter = RateLimiter.create(2)
for (item <- items) {
    //..do work...
    processed += 1
    if (limiter.tryAcquire()) {
        listener.progressChanged(100.0 * processed / items.size)
    }
}
```

Getting better?
If the API is not clear: we are first creating a `RateLimiter` with 2 permits per second.
This means we can *acquire* up to two permits during one second and if we try to do it more often `tryAcquire()` will return `false` (or thread will block if `acquire()` is used instead<sup>1</sup>).
So the code above guarantees that the listener won't be called more that two times per second.
As a bonus, if you want to completely get rid of unrelated throttling code from the business logic, [*decorator* pattern](http://en.wikipedia.org/wiki/Decorator_pattern) to the rescue.
First let's create a listener that wraps another (concrete) listener and delegates to it only at a given rate:

```scala
class RateLimitedListener(target: Listener) extends Listener {

    val limiter = RateLimiter.create(2)

    def progressChanged(percentProgress: Double) {
        if (limiter.tryAcquire()) {
            target.progressChanged(percentProgress)
        }
    }
}
```

What's best about the *decorator* pattern is that both the code using the listener and the concrete implementation are not aware of the decorator.
Also the client code became much simpler (essentially we came back to original):

```scala
def longRunning(listener: Listener) {
    var processed = 0
    for (item <- items) {
        //..do work...
        processed += 1
        listener.progressChanged(100.0 * processed / items.size)
    }
}

longRunning(new RateLimitedListener(new ConsoleListener))
```

But we've only scratched the surface of where `RateLimiter` can be used!
Say we want to avoid aforementioned denial of service attack or slow down automated clients of our API.
It's very simple with `RateLimiter` and servlet filter:

```scala
@WebFilter(urlPatterns=Array("/*"))
class RateLimiterFilter extends Filter {

    val limiter = RateLimiter.create(100)

    def init(filterConfig: FilterConfig) {}

    def doFilter(request: ServletRequest, response: ServletResponse, chain: FilterChain) {
        if(limiter.tryAcquire()) {
            chain.doFilter(request, response)
        } else {
            response.asInstanceOf[HttpServletResponse].sendError(SC_TOO_MANY_REQUESTS)
        }
    }

    def destroy() {}
}
```

Another self-descriptive sample.
This time we limit our API to handle not more than 100 requests per second (of course `RateLimiter` is thread safe).
All HTTP requests that come through our filter are subject to rate limiting.
If we cannot handle incoming request, we send [HTTP 429 - Too Many Requests](http://en.wikipedia.org/wiki/List_of_HTTP_status_codes#429) error code (not yet available in servlet spec).
Alternatively you may wish to block the client for a while instead of eagerly rejecting it.
That's fairly straightforward as well:

```scala
def doFilter(request: ServletRequest, response: ServletResponse, chain: FilterChain) {
    limiter.acquire()
    chain.doFilter(request, response)
}
```

`limiter.acquire()` will block as long as it's needed to keep desired 100 requests per second limit.
Yet another alternative is to use `tryAcquire()` with timeout (blocking up to given amount of time).
Blocking approach is better if you want to avoid sending errors to the client.
However under high load it's easy to imagine almost all HTTP threads blocked waiting for `RateLimiter`, eventually causing servlet container to reject connections.
So dropping of clients can be only partially avoided.
This filter is a good starting point to build more sophisticated solutions.
Map of rate limiters by IP or user name are good examples.

------------------------------------------------------------------------

What we haven't covered yet is acquiring more than one permit at a time.
It turns out `RateLimiter` can also be used e.g. to limit network bandwidth or the amount of data being sent/received.
Imagine you create a search servlet and you want to impose that no more than 1000 results are returned per second.
In each request user decides how many results she wants to receive per response: it can be 500 requests each containing 2 results or 1 huge request asking for 1000 results at once.
But never more than 1000 results within a second on average.
Users are free to use their quota as they wish:

```scala
@WebFilter(urlPatterns = Array ("/search"))
class SearchServlet extends HttpServlet {

    val limiter = RateLimiter.create(1000)

    override def doGet(req: HttpServletRequest, resp: HttpServletResponse) {
        val resultsCount = req.getParameter("results").toInt
        limiter.acquire(resultsCount)
        //process and return results...
    }
}
```

By default we `acquire()` one permit per invocation.
Non-blocking servlet would call `limiter.tryAcquire(resultsCount)` and check the results, you know that by now.
If you are interested in rate limiting of network traffic, don't forget to check out my [*Tenfold increase in server throughput with Servlet 3.0 asynchronous processing*](http://nurkiewicz.blogspot.no/2011/03/tenfold-increase-in-server-throughput.html).
`RateLimiter`, due to a blocking nature, is not very well suited to write scalable upload/download servers with throttling.

------------------------------------------------------------------------

The last example I would like to share with you is throttling client code to avoid overloading the server we are talking to.
Imagine a batch import/export process that calls some server thousands of times exchanging data.
If we don't throttle the client and there is no rate limiting on the server side, server might get overloaded and crash.
`RateLimiter` is once again very helpful:

```scala
val limiter = RateLimiter.create(20)

def longRunning() {
    for (item <- items) {
        limiter.acquire()
        server.sync(item)
    }
}
```

This sample is very similar to the first one.
Difference being that this time we block instead of discard missing permits.
Thanks to blocking, external call to `server.sync(item)` won't overload the 3rd-party server, calling it at most 20 times per second.
Of course if you have several threads interacting with the server, they can all share the same `RateLimiter`.

------------------------------------------------------------------------

To wrap-up:

- `RateLimiter` allows you to perform certain actions not more often than with a given frequency
- It's a small and lightweight class (no threads involved!)
  You can create thousands of rate limiters (per client?)
  or share one among several threads
- We haven't covered *warm-up* functionality - if `RateLimiter` was completely idle for a long time, it will gradually increase allowed frequency over configured time up to configured maximum value instead of allowing maximum frequency from the very beginning

I have a feeling that we'll go back to this class soon.
I hope you'll find it useful in your next project!

<sup>1</sup> - I am using Guava 14.0-SNAPSHOT.
If 14.0 stable is not available by the time you are reading this, you must use more verbose `tryAcquire(1, 0, TimeUnit.MICROSECONDS)` instead of `tryAcquire()` and `acquire(1)` instead of `acquire()`.
