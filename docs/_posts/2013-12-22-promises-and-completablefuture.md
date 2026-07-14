---
layout: post
title: Promises and CompletableFuture
date: '2013-12-22T20:21:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- CompletableFuture
- multithreading
- concurrency
modified_time: '2015-11-29T23:38:27.987+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3500733017634612654
blogger_orig_url: https://www.nurkiewicz.com/2013/12/promises-and-completablefuture.html
image:
  path: /assets/img/promises-and-completablefuture/hero.jpg
  alt: "From meetup.com"
---

During [my talk](http://www.youtube.com/watch?v=S7gCcgTWSPs) at Warsaw Java Users Group about functional reactive programming in Java a few interesting questions came up regarding [`CompletableFuture`](http://download.java.net/jdk8/docs/api/java/util/concurrent/CompletableFuture.html) capabilities.
One person was interested whether it's possible to wait for the first completed future that is passing a given predicate rather than just the first one (like [`CompletableFuture.anyOf()`](http://download.java.net/jdk8/docs/api/java/util/concurrent/CompletableFuture.html#anyOf-java.util.concurrent.CompletableFuture...-)).
This is similar requirement to [`Future.find()`](http://www.scala-lang.org/api/current/index.html#scala.concurrent.Future$) in Scala.
It's not built into `CompletableFuture` but quite easy to implement using the concept of *promises*.

Our custom implementation will take two parameters: a list of homogeneous futures and a predicate.
The first future to complete that matches given predicate wins.
If no future matched resulting future never ends (rather easy to change that behaviour).
We will use a thread-safe and lightweight `AtomicBoolean completed` flag because callbacks will be invoked from multiple threads.

```java
public static <T> CompletableFuture<T> firstMatching(Predicate<T> predicate, CompletableFuture<T>... futures) {
    final AtomicBoolean completed = new AtomicBoolean();
    final CompletableFuture<T> promise = new CompletableFuture<>();
    for (CompletableFuture<T> future : futures) {
        future.thenAccept(result -> {
            if (predicate.test(result) && completed.compareAndSet(false, true))
                promise.complete(result);
        });
    }
    return promise;
}
```

As you can see *promise* is like a `Future` detached from a thread pool.
Rather than waiting for an asynchronous computation to complete we simply assign a value to it at arbitrary point in time.
See also: [*Implementing custom Future*](http://nurkiewicz.com/2013/02/implementing-custom-future.html).

------------------------------------------------------------------------

Second question was about [`CompletableFuture.anyOf()`](http://download.java.net/jdk8/docs/api/java/util/concurrent/CompletableFuture.html#anyOf-java.util.concurrent.CompletableFuture...-) - whether it automatically cancels all tasks except the first one.
As you may remember [`anyOf()` will complete when the very first of underlying futures complete](http://nurkiewicz.com/2013/05/java-8-definitive-guide-to.html), discarding all remaining futures.
It turns out that `CompletableFuture` forgets about them without any special treatment.
We could expect that it should immediately call `cancel()` on all slower tasks but this doesn't happen (!)
and we will see soon why.

Luckily we can easily build our own instances of `CompletableFuture` and resolve them at any time, thus it's relatively easy to build more abstract transformations on top of futures.
Our implementation will asynchronously wait for completion of all underlying futures and once the first one completes it will attempt to cancel all the remaining ones - since they are no longer needed:

```java
public static <T> CompletableFuture<T> cancellingAnyOf(CompletableFuture<T>... futures) {
    final AtomicBoolean completed = new AtomicBoolean();
    final CompletableFuture<T> promise = new CompletableFuture<>();
    for (CompletableFuture<T> future : futures) {
        future.whenComplete((result, ex) -> {
            if (completed.compareAndSet(false, true)) {
                Arrays.asList(futures).stream().
                        filter(f -> f != future).
                        forEach(f -> f.cancel(true));
                if (ex != null)
                    promise.completeExceptionally(ex);
                else
                    promise.complete(result);
            }
        });
    }
    return promise;
}
```

The implementation is slightly complex because `whenComplete()` callbacks are executed from multiple threads so we must synchronize this method properly.
That's the rationale behind lightweight `AtomicBoolean completed` flag.
When the very first `whenComplete()` callback is executed it passes the value to our custom `CompletableFuture` (called *promise*) and attempts to cancel all the remaining tasks.
OK, so the implementation looks fine but it somehow fails to interrupt running tasks, e.g. blocked on `Thread.sleep()`.
In essence all these methods that declare throwing `InterruptedException` should be interrupted but aren't.
Why?
Well, *I failed* to read the [documentation of `CompletableFuture`](http://download.java.net/jdk8/docs/api/java/util/concurrent/CompletableFuture.html):

> Since \[...\]
> this class has no direct control over the computation that causes it to be completed, cancellation is treated as just another form of exceptional completion.
> Method `cancel` has the same effect as `completeExceptionally(new CancellationException())`.

And in [`CompletableFuture.cancel(mayInterruptIfRunning)`](http://download.java.net/jdk8/docs/api/java/util/concurrent/CompletableFuture.html#cancel-boolean-):

> `mayInterruptIfRunning` - this value has no effect in this implementation because interrupts are not used to control processing.

This means that **`CompletableFuture.cancel()` does not interrupt underlying thread**.
When you call `Future.cancel()` it tries to call `Thread.interrupt()`, eagerly stopping already running task.
This is virtually impossible with `CompletableFuture`.
All it does is resolving a future with `CancellationException` but does not care about computation running.
Very disappointing but worth knowing.

I hope by now you are more familiar with the concept of *promises* and how they can be implemented using `CompletableFuture`.
Other scenarios are relatively easy to glue together.
