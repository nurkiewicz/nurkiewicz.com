---
layout: post
title: java.util.concurrent.Future basics
date: '2013-02-16T19:42:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- multithreading
- performance
- spring
modified_time: '2013-02-21T18:07:30.137+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4481490202345464375
blogger_orig_url: https://www.nurkiewicz.com/2013/02/javautilconcurrentfuture-basics.html
image:
  path: /assets/img/javautilconcurrentfuture-basics/hero.jpg
  alt: "Bygdøy during winter"
---

Hereby I am starting a series of articles about *future* concept in programming languages (also known as [*promises* or *delays*](http://en.wikipedia.org/wiki/Futures_and_promises)) with a working title: [*Back to the Future*](http://www.imdb.com/title/tt0088763/).
*Futures* are very important abstraction, even more these day than ever due to growing demand for asynchronous, event-driven, parallel and scalable systems.
In the first article we'll discover most basic [`java.util.concurrent.Future<T>`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Future.html) interface.
Later on we will jump into other frameworks, libraries or even languages.
`Future<T>` is pretty limited, but essential to understand, *ekhm*, future parts.

In a single-threaded application when you call a method it returns only when the computations are done ([`IOUtils.toString()`](http://commons.apache.org/io/apidocs/org/apache/commons/io/IOUtils.html#toString(java.io.InputStream,%20java.nio.charset.Charset)) comes from [Apache Commons IO](http://commons.apache.org/io/)):

```java
public String downloadContents(URL url) throws IOException {
    try(InputStream input = url.openStream()) {
        return IOUtils.toString(input, StandardCharsets.UTF_8);
    }
}

//...

final String contents = downloadContents(new URL("http://www.example.com"));
```

`downloadContents()` looks harmless<sup>1</sup>, but it can take even arbitrary long time to complete.
Moreover in order to reduce latency you might want to do other, independent processing in the meantime, while waiting for results.
In the old days you would start a new `Thread` and somehow wait for results (shared memory, locks, dreadful `wait()`/`notify()` pair, etc.)
With `Future<T>` it's much more pleasant:

```java
public static Future<String> startDownloading(URL url) {
    //...
}

final Future<String> contentsFuture = startDownloading(new URL("http://www.example.com"));
//other computation
final String contents = contentsFuture.get();
```

We will implement `startDownloading()` soon.
For now it's important that you understand the principles.
`startDownloading()` does **not** block, waiting for external website.
Instead it returns immediately, returning a lightweight `Future<String>` object.
This object is a *promise* that `String` will be available in the future.
Don't know when, but keep this reference and once it's there, you'll be able to retrieve it using `Future.get()`.
In other words `Future` is a proxy or a wrapper around an object that is not yet there.
Once the asynchronous computation is done, you can extract it.
So what API does `Future` provide?

[`Future.get()`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Future.html#get()) is the most important method.
It blocks and waits until promised result is available (*resolved*).
So if we really need that `String`, just call `get()` and wait.
There is an [overloaded version](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Future.html#get(long,%20java.util.concurrent.TimeUnit)) that accepts timeout so you won't wait forever if something goes wild.
`TimeoutException` is thrown if waiting for too long.

In some use cases you might want to peek on the `Future` and continue if result is not yet available.
This is possible with [`isDone()`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Future.html#isDone()).
Imagine a situation where your user waits for some asynchronous computation and you'd like to let him know that we are still waiting and do some computation in the meantime:

```java
final Future<String> contentsFuture = startDownloading(new URL("http://www.example.com"));
while (!contentsFuture.isDone()) {
    askUserToWait();
    doSomeComputationInTheMeantime();
}
contentsFuture.get();
```

The last call to `contentsFuture.get()` is guaranteed to return immediately and not block because `Future.isDone()` returned `true`.
If you follow the pattern above make sure you are not busy waiting, calling `isDone()` millions of time per second.

Cancelling futures is the last aspect we have not covered yet.
Imagine you started some asynchronous job and you can only wait for it given amount of time.
If it's not there after, say, 2 seconds, we give up and either propagate error or work around it.
However if you are a good citizen, you should somehow tell this future object: I no longer need you, forget about it.
You save processing resources by not running obsolete tasks.
The syntax is simple:

```java
contentsFuture.cancel(true);    //meh...
```

We all love cryptic, boolean parameters, aren't we?
Cancelling comes in two flavours.
By passing `false` to `mayInterruptIfRunning` parameter we only cancel tasks that didn't yet started, when the `Future` represents results of computation that did not even began.
But if our `Callable.call()` is already in the middle, we let it finish.
However if we pass `true`, `Future.cancel()` will be more aggressive, trying to interrupt already running jobs as well.
How?
Think about all these methods that throw infamous [`InterruptedException`](http://docs.oracle.com/javase/7/docs/api/java/lang/InterruptedException.html), namely [`Thread.sleep()`](http://docs.oracle.com/javase/7/docs/api/java/lang/Thread.html#sleep(long)), [`Object.wait()`](http://docs.oracle.com/javase/7/docs/api/java/lang/Object.html#wait()), [`Condition.await()`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/locks/Condition.html#await()), and many others (including [`Future.get()`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Future.html#get())).
If you are blocking on any of such methods and someone decided to cancel your `Callable`, they will actually throw `InterruptedException`, signalling that someone is trying to interrupt currently running task.

------------------------------------------------------------------------

So we now understand what `Future<T>` is - a place-holder for something, that you will get in the future.
It's like keys to a car that was not yet manufactured.
But how do you actually obtain an instance of `Future<T>` in your application?
Two most common sources are thread pools and asynchronous methods (backed by thread pools for you).
Thus our `startDownloading()` method can be rewritten to:

```java
private final ExecutorService pool = Executors.newFixedThreadPool(10);

public Future<String> startDownloading(final URL url) throws IOException {
    return pool.submit(new Callable<String>() {
        @Override
        public String call() throws Exception {
            try (InputStream input = url.openStream()) {
                return IOUtils.toString(input, StandardCharsets.UTF_8);
            }
        }
    });
}
```

A lot of syntax boilerplate, but the basic idea is simple: wrap long-running computations in `Callable<String>` and `submit()` them to a thread pool of 10 threads.
Submitting returns some implementation of `Future<String>`, most likely somehow linked to your task and thread pool.
Obviously your task is not executed immediately.
Instead it is placed in a queue which is later (maybe even much later) polled by thread from a pool.
Now it should be clear what these two flavours of `cancel()` mean - you can always cancel task that still resides in that queue.
But cancelling already running task is a bit more complex.

Another place where you can meet `Future` is Spring and EJB.
For example in Spring framework you can simply [annotate your method with `@Async`](http://static.springsource.org/spring/docs/3.2.x/spring-framework-reference/html/scheduling.html#scheduling-annotation-support-async):

```java
@Async
public Future<String> startDownloading(final URL url) throws IOException {
    try (InputStream input = url.openStream()) {
        return new AsyncResult<>(
                IOUtils.toString(input, StandardCharsets.UTF_8)
        );
    }
}
```

Notice that we simply wrap our result in [`AsyncResult`](http://static.springsource.org/spring/docs/3.1.x/javadoc-api/org/springframework/scheduling/annotation/AsyncResult.html) implementing `Future`.
But the method itself does not deal with thread pool or asynchronous processing.
Later on Spring will proxy all calls to `startDownloading()` and run them in a thread pool.
The exact same feature is available through [`@Asynchronous` annotation in EJB](http://docs.oracle.com/javaee/6/tutorial/doc/gkkqg.html).

So we learned a lot about `java.util.concurrent.Future`.
Now it's time to admit - this interface is quite limited, especially when compared to other languages.
More on that later.

<sup>1</sup> - are you unfamiliar with *try-with-resources* feature of Java 7?
You'll better switch to Java 7 **now**.
Java 6 will no longer be maintained [in two weeks](http://www.oracle.com/technetwork/java/eol-135779.html).
