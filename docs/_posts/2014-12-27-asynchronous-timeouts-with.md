---
layout: post
title: Asynchronous timeouts with CompletableFuture
date: '2014-12-27T22:24:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- CompletableFuture
- java8
- multithreading
modified_time: '2015-11-29T23:37:40.369+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-141775687551418776
blogger_orig_url: https://www.nurkiewicz.com/2014/12/asynchronous-timeouts-with.html
---

One day I was rewriting poorly implemented multi-threaded code that was blocking at some point on `Future.get()`:

```java
public void serve() throws InterruptedException, ExecutionException, TimeoutException {
    final Future<Response> responseFuture = asyncCode();
    final Response response = responseFuture.get(1, SECONDS);
    send(response);
}

private void send(Response response) {
    //...
}
```

This was actually an Akka application written in Java with a thread pool of 1000 threads (sic!)
- all of them blocked on this `get()` call.
Otherwise system couldn't keep up with the number of concurrent requests.
After refactoring we got rid of all these threads and introduced just one, significantly reducing memory footprint.
Let's simplify a bit and show examples in Java 8.
The first step is to introduce `CompletableFuture` instead of plain `Future` (see: [tip 9](http://www.nurkiewicz.com/2014/11/executorservice-10-tips-and-tricks.html)).
It's simple if:

- you control how tasks are submitted to `ExecutorService`: just use `CompletableFuture.supplyAsync(..., executorService)` instead of `executorService.submit(...)`
- you deal with callback-based API: use promises

Otherwise (if you have blocking API or `Future<T>` already) there will be some thread blocked.
That's why there are so many asynchronous APIs being born right now.
So let's say we somehow rewritten our code to receive `CompletableFuture`:

```java
public void serve() throws InterruptedException, ExecutionException, TimeoutException {
    final CompletableFuture<Response> responseFuture = asyncCode();
    final Response response = responseFuture.get(1, SECONDS);
    send(response);
}
```

Obviously that doesn't fix anything, we have to take advantage of new reactive style of programming:

```java
public void serve() {
    final CompletableFuture<Response> responseFuture = asyncCode();
    responseFuture.thenAccept(this::send);
}
```

This is functionally equivalent, but now `serve()` should run in no-time (no blocking or waiting).
Just remember that `this::send` will be executed in the same thread that completed `responseFuture`.
If you don't want to overload some arbitrary thread pool somewhere or `send()` is expensive, consider separate thread pool for that: `thenAcceptAsync(this::send, sendPool)`.
Great, but we lost two important properties: error propagation and timeout.
Error propagation is hard because we changed API.
When `serve()` method exits, asynchronous operations is probably not yet finished.
If you care about exceptions, consider either returning `responseFuture` or some alternative mechanism.
At minimum, log exception because otherwise it will be swallowed:

```java
final CompletableFuture<Response> responseFuture = asyncCode();
responseFuture.exceptionally(throwable -> {
    log.error("Unrecoverable error", throwable);
    return null;
});
responseFuture.thenAccept(this::send);
```

Be careful with the code above: `exceptionally()` tries to *recover* from failure, returning alternative result.
It works here but if you chain `exceptionally()` with `thenAccept()` it will `send()` will be called even in case of failure, but with `null` argument (or whatever we return from `exceptionally()`:

```java
final CompletableFuture<Response> responseFuture = asyncCode();
responseFuture
    .exceptionally(throwable -> {
        log.error("Unrecoverable error", throwable);
        return null;
    })
    .thenAccept(this::send);  //probably not what you think
```

Problem with lost 1 second timeout is subtle.
Our original code was waiting (blocking) for at most 1 second until `Future` finishes.
Otherwise `TimeoutException` was thrown.
We lost this functionality, even worse unit tests for timeouts are inconvenient and often skipped.
In order to port timeouts without sacrificing event-driven spirit we need one extra building block: a future that always fails after a given time:

```java
public static <T> CompletableFuture<T> failAfter(Duration duration) {
    final CompletableFuture<T> promise = new CompletableFuture<>();
    scheduler.schedule(() -> {
        final TimeoutException ex = new TimeoutException("Timeout after " + duration);
        return promise.completeExceptionally(ex);
    }, duration.toMillis(), MILLISECONDS);
    return promise;
}

private static final ScheduledExecutorService scheduler =
        Executors.newScheduledThreadPool(
                1,
                new ThreadFactoryBuilder()
                        .setDaemon(true)
                        .setNameFormat("failAfter-%d")
                        .build());
```

That's simple: we create a *promise* (future without underlying task or thread pool) and complete it with `TimeoutException` after a given `java.time.Duration`.
If you `get()` such future somewhere, `TimeoutException` will be thrown after blocking for at least that much time.
Actually, it will be `ExecutionException` wrapping `TimeoutException`, no way around that.
Notice that I use fixed `scheduler` thread pool with just one thread.
It's not only for educational purposes: "*1 thread ought to be enough for anybody*" <sup>[\[1\]](http://en.wikiquote.org/wiki/Bill_Gates)</sup> in this scenario.
`failAfter()` on its own is rather useless, but combine it with our `responseFuture` and we have a solution!

```java
final CompletableFuture<Response> responseFuture = asyncCode();
final CompletableFuture<Response> oneSecondTimeout = failAfter(Duration.ofSeconds(1));
responseFuture
        .acceptEither(oneSecondTimeout, this::send)
        .exceptionally(throwable -> {
            log.error("Problem", throwable);
            return null;
        });
```

A lot is going on here.
After receiving `responseFuture` with our background task we also create "synthetic" `oneSecondTimeout` future that will never complete successfully but always fails after 1 second.
Now we combine the two by calling `acceptEither`.
This operator will execute block of code against first completed future, either `responseFuture` or `oneSecondTimeout` and simply ignore outcome of the slower one.
If `asyncCode()` completes within 1 second `this::send` will be invoked and exception from `oneSecondTimeout` will get ignored.
However!
If `asyncCode()` is really slow, `oneSecondTimeout` kicks in first.
But since it fails with an exception, `exceptionally` error handler is invoked instead of `this::send`.
You can take for granted that either `send()` or `exceptionally` will be called, not both.
Of course if we had two "ordinary" futures completing normally, `send()` would be called with a response from the first one, discarding the latter.

This wasn't the cleanest solution.
Cleaner one would wrap original future and make sure it finishes within given time.
Such operator is available in [`com.twitter.util.Future`](https://twitter.github.io/util/docs/#com.twitter.util.Future) (Scala; called `within()`), however is missing in [`scala.concurrent.Future`](http://www.scala-lang.org/files/archive/nightly/docs/library/index.html#scala.concurrent.Future) (supposedly inspired by the former).
Let's leave Scala behind and implement similar operator for `CompletableFuture`.
It takes one future as input and returns a future that completes when underlying one is completed.
However if it takes too long to complete the underlying future, exception is thrown:

```java
public static <T> CompletableFuture<T> within(CompletableFuture<T> future, Duration duration) {
    final CompletableFuture<T> timeout = failAfter(duration);
    return future.applyToEither(timeout, Function.identity());
}
```

This leads to final, clean and flexible solution:

```java
final CompletableFuture<Response> responseFuture = within(
        asyncCode(), Duration.ofSeconds(1));
responseFuture
        .thenAccept(this::send)
        .exceptionally(throwable -> {
            log.error("Unrecoverable error", throwable);
            return null;
        });
```

Hope you enjoyed this article, as you can see reactive programming in Java is no longer a thing of the *future* (no pun intended).
