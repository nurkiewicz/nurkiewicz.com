---
layout: post
title: Which thread executes CompletableFuture's tasks and callbacks?
date: '2015-11-30T08:58:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- CompletableFuture
- multithreading
modified_time: '2015-11-30T08:58:03.979+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1594946357632027800
blogger_orig_url: https://www.nurkiewicz.com/2015/11/which-thread-executes.html
---

[`CompletableFuture`](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CompletableFuture.html) is still a relatively fresh concept, despite being introduced almost two years ago (!)
in March 2014 with Java 8.
But maybe it's good that this class is not so well known since it can be easily abused, especially with regards to threads and thread pools that are involved along the way.
This article aims to describe how threads are used with `CompletableFuture`.

## Running tasks

This is the fundamental part of the API.
There is a convenient `supplyAsync()` method that is similar to `ExecutorService.submit()`, but returning `CompletableFuture`:

```java
CompletableFuture<String> future =
        CompletableFuture.supplyAsync(() -> {
            try (InputStream is = new URL("http://www.nurkiewicz.com").openStream()) {
                log.info("Downloading");
                return IOUtils.toString(is, StandardCharsets.UTF_8);
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        });
```

The problem is, `supplyAsync()` by default uses `ForkJoinPool.commonPool()`, thread pool shared between all `CompletableFuture`s, all parallel streams and all applications deployed on the same JVM (if you are unfortunate to still use application server with many deployed artifacts).
This hard-coded, unconfigurable thread pool is completely outside of our control, hard to monitor and scale.
Therefore you should always specify your own `Executor`, like here (and have a look at my [few tips how to create one](http://www.nurkiewicz.com/2014/11/executorservice-10-tips-and-tricks.html)):

```java
ExecutorService pool = Executors.newFixedThreadPool(10);

final CompletableFuture<String> future =
        CompletableFuture.supplyAsync(() -> {
            //...
        }, pool);
```

But that is just the beginning...

## Callbacks and transformations

Suppose you want to transform given `CompletableFuture`, e.g. extract the length of the `String`:

```java
CompletableFuture<Integer> intFuture =
    future.thenApply(s -> s.length());
```

Who, exactly, invokes the `s.length()` code?
Frankly, my dear developers, we don't give a damn <sup>[\[1\]](https://en.wikipedia.org/wiki/Frankly,_my_dear,_I_don%27t_give_a_damn)</sup>.
As long as the lambda expression inside all of the operators like `thenApply` is cheap, we don't really care who calls it.
But what if this expression takes a little bit of CPU time to complete or makes a blocking network call?

First of all what happens by default?
Think about it: we have a background task of type `String` and we want to apply some specific transformation asynchronously when that value completes.
The easiest way to implement that is by wrapping the original task (returning `String`) and intercepting it when it completes.
When the inner task finishes, our callback kicks in, applies the transformation and returns modified value.
It's like an aspect that sits between our code and original computation result.
That being said it should be fairly obvious that `s.length()` transformation will be executed in the same thread as the original task, huh?
Not quite!

```java
CompletableFuture<String> future =
        CompletableFuture.supplyAsync(() -> {
            sleepSeconds(2);
            return "ABC";
        }, pool);

future.thenApply(s -> {
    log.info("First transformation");
    return s.length();
});

future.get();
pool.shutdownNow();
pool.awaitTermination(1, TimeUnit.MINUTES);

future.thenApply(s -> {
    log.info("Second transformation");
    return s.length();
});
```

The first transformation in `thenApply()` is registered while the task is still running.
Thus it will be executed immediately after task completion in the same thread as the task.
However before registering second transformation we wait until the task actually completes.
Even worse, we shutdown the thread pool entirely, to make sure no other code can ever be executed there.
So which thread will run second transformation?
We know it must happen immediately since the `future` we register callback on already completed.
It turns out that by default client thread (!)
is used!
The output is as follows:

pool-1-thread-1 \| First transformation main \| Second transformation

Second transformation, when registered, realizes that the `CompletableFuture` already finished, so it executes the transformation immediately.
There is no other thread around so `thenApply()` is invoked in the context of current `main` thread.
The biggest reason why this behavior is error prone shows up when the actual transformation is costly.
Imagine lambda expression inside `thenApply()` doing some heavy computation or blocking network call.
Suddenly our asynchronous `CompletableFuture` blocks calling thread!

## Controlling callback's thread pool

There are two techniques to control which thread executes our callbacks and transformations.
Notice that these solutions are only needed if your transformations are costly.
Otherwise the difference is negligible.
So first of all we can choose the `*Async` versions of operators, e.g.:

```java
future.thenApplyAsync(s -> {
    log.info("Second transformation");
    return s.length();
});
```

This time the second transformation was automatically off-loaded to our friend, `ForkJoinPool.commonPool()`:

```java
pool-1-thread-1                  | First transformation
ForkJoinPool.commonPool-worker-1 | Second transformation
```

But we don't like `commonPool` so we supply our own:

```java
future.thenApplyAsync(s -> {
    log.info("Second transformation");
    return s.length();
}, pool2);
```

Notice that different thread pool was used (`pool-1` vs. `pool-2`):

```java
pool-1-thread-1 | First transformation
pool-2-thread-1 | Second transformation
```

## Treating callback like another computation step

But I believe that if you are having troubles with long-running callbacks and transformations (remember that this article applies to almost all other methods on `CompletableFuture`), you should simply use another explicit `CompletableFuture`, like here:

```java
//Imagine this is slow and costly
CompletableFuture<Integer> strLen(String s) {
    return CompletableFuture.supplyAsync(
            () -> s.length(),
            pool2);
}

//...

CompletableFuture<Integer> intFuture = 
        future.thenCompose(s -> strLen(s));
```

This approach is more explicit.
Knowing that our transformation has significant cost we don't risk running it on some arbitrary or uncontrolled thread.
Instead we explicitly model it as asynchronous operation from `String` to `CompletableFuture<Integer>`.
However we must replace `thenApply()` with `thenCompose()`, otherwise we'll end up with `CompletableFuture<CompletableFuture<Integer>>`.

But what if our transformation does not have a version that plays well with nested `CompletableFuture`, e.g. `applyToEither()` that waits for the first `Future` to complete and applies a transformation?

```java
CompletableFuture<CompletableFuture<Integer>> poor = 
        future1.applyToEither(future2, s -> strLen(s));
```

There is a handy trick for "unwrapping" such obscure data structure called `flatten`, easily implemented using `flatMap(identity)` (or `flatMap(x -> x)`).
In our case `flatMap()` is called `thenCompose` (*duh!*):

```java
CompletableFuture<Integer> good = 
        poor.thenCompose(x -> x);
```

I leave it up to you how and why it works.
I hope this article made it more clear how threads are involved in `CompletableFuture`.
