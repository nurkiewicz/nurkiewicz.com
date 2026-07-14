---
layout: post
title: ListenableFuture in Guava
date: '2013-02-25T23:37:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- guava
- multithreading
- concurrency
modified_time: '2013-02-25T23:37:55.592+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5416992373753251613
blogger_orig_url: https://www.nurkiewicz.com/2013/02/listenablefuture-in-guava.html
image:
  path: /assets/img/listenablefuture-in-guava/hero.jpg
  alt: "Fram Museum"
---

[`ListenableFuture`](http://docs.guava-libraries.googlecode.com/git-history/release/javadoc/com/google/common/util/concurrent/ListenableFuture.html) in Guava is an attempt to define consistent API for `Future` objects to register completion callbacks.
With the ability to add callback when `Future` completes, we can asynchronously and effectively respond to incoming events.
If your application is highly concurrent with lots of future objects, I strongly recommend using `ListenableFuture` whenever you can.

Technically `ListenableFuture` extends `Future` interface by adding simple

```java
void addListener(Runnable listener, Executor executor)
```

method.
That's it.
If you get a hold of `ListenableFuture` you can register [`Runnable`](http://docs.oracle.com/javase/7/docs/api/java/lang/Runnable.html) to be executed immediately when future in question completes.
You must also supply [`Executor`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Executor.html) ([`ExecutorService`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/ExecutorService.html) extends it) that will be used to execute your listener - so that long-running listeners do not occupy your worker threads.

Let's put that into action.
We will start by refactoring our [first example of web crawler](http://nurkiewicz.blogspot.no/2013/02/javautilconcurrentfuture-basics.html) to use `ListenableFuture`.
Fortunately in case of thread pools it's just a matter of wrapping them using [`MoreExecutors.listeningDecorator()`](http://docs.guava-libraries.googlecode.com/git-history/release/javadoc/com/google/common/util/concurrent/MoreExecutors.html#listeningDecorator(java.util.concurrent.ExecutorService)):

```java
ListeningExecutorService pool = MoreExecutors.listeningDecorator(Executors.newFixedThreadPool(10));

for (final URL siteUrl : topSites) {
    final ListenableFuture<String> future = pool.submit(new Callable<String>() {
        @Override
        public String call() throws Exception {
            return IOUtils.toString(siteUrl, StandardCharsets.UTF_8);
        }
    });

    future.addListener(new Runnable() {
        @Override
        public void run() {
            try {
                final String contents = future.get();
                //...process web site contents
            } catch (InterruptedException e) {
                log.error("Interrupted", e);
            } catch (ExecutionException e) {
                log.error("Exception in task", e.getCause());
            }
        }
    }, MoreExecutors.sameThreadExecutor());
}
```

There are several interesting observations to make.
First of all notice how [`ListeningExecutorService`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/util/concurrent/ListeningExecutorService.html) wraps existing `Executor`.
This is similar to [`ExecutorCompletionService` approach](http://nurkiewicz.blogspot.no/2013/02/executorcompletionservice-in-practice.html).
Later on we register custom `Runnable` to be notified when each and every task finishes.
Secondly notice how ugly error handling becomes: we have to handle `InterruptedException` (which should technically never happen as `Future` is already resolved and `get()` will never throw it) and `ExecutionException`.
We haven't covered that yet, but `Future<T>` must somehow handle exceptions occurring during asynchronous computation.
Such exceptions are wrapped in `ExecutionException` (thus the `getCause()` invocation during logging) thrown from `get()`.

Finally notice [`MoreExecutors.sameThreadExecutor()`](http://docs.guava-libraries.googlecode.com/git-history/release/javadoc/com/google/common/util/concurrent/MoreExecutors.html#sameThreadExecutor()) being used.
It's a handy abstraction which you can use every time some API wants to use an `Executor`/`ExecutorService` (presumably thread pool) while you are fine with using *current* thread.
This is especially useful during unit testing - even if your production code uses asynchronous tasks, during tests you can run everything from the same thread.

No matter how handy it is, whole code seems a bit cluttered.
Fortunately there is a simple utility method in fantastic [`Futures`](http://docs.guava-libraries.googlecode.com/git-history/release/javadoc/com/google/common/util/concurrent/Futures.html) class:

```java
Futures.addCallback(future, new FutureCallback<String>() {
    @Override
    public void onSuccess(String contents) {
        //...process web site contents
    }

    @Override
    public void onFailure(Throwable throwable) {
        log.error("Exception in task", throwable);
    }
});
```

[`FutureCallback`](http://docs.guava-libraries.googlecode.com/git-history/release/javadoc/com/google/common/util/concurrent/FutureCallback.html) is a much simpler abstraction to work with, resolves future and does exception handling for you.
Also you can still supply custom thread pool for listeners if you want.
If you are stuck with some legacy API that still returns `Future` you may try [`JdkFutureAdapters.listenInPoolThread()`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/util/concurrent/JdkFutureAdapters.html#listenInPoolThread(java.util.concurrent.Future)) which is an adapter converting plain `Future<V>` to `ListenableFuture<V>`.
But keep in mind that once you start using `addListener()`, each such adapter will require one thread exclusively to work so this solution doesn't scale at all and you should avoid it.

```java
Future<String> future = //...
ListenableFuture<String> listenableFuture =
        JdkFutureAdapters.listenInPoolThread(future);
```

Once we understand the basics we can dive deeply into biggest strength of listening futures: **transformations and chaining**.
This is advanced stuff, you have been warned.
