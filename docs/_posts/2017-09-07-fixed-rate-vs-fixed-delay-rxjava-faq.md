---
layout: post
title: Fixed-rate vs. fixed-delay - RxJava FAQ
date: '2017-09-07T10:48:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- scheduling
- rxjava
modified_time: '2017-09-07T10:48:17.781+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-7887793603846116373
blogger_orig_url: https://www.nurkiewicz.com/2017/09/fixed-rate-vs-fixed-delay-rxjava-faq.html
image:
  path: /assets/img/fixed-rate-vs-fixed-delay-rxjava-faq/hero.jpg
  alt: "Topiło lake in Białowieża Forest"
---

If you are using plain Java, since version 5 we have a handy scheduler class that allows running tasks at fixed rate or with fixed delay:

```java
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;

ScheduledExecutorService scheduler = 
        Executors.newScheduledThreadPool(10);
```

Basically it supports two types of operations:

```java
scheduler.scheduleAtFixedRate(() -> doStuff(), 2, 1, SECONDS);
scheduler.scheduleWithFixedDelay(() -> doStuff(), 2, 1, SECONDS);
```

`scheduleAtFixedRate()` will make sure `doStuff()` is invoked precisely every second with an initial delay of two seconds.
Of course garbage collection, context-switching, etc. still can affect the precision.
`scheduleWithFixedDelay()` is seemingly similar, however it takes `doStuff()` processing time into account.
For example, if `doStuff()` runs for 200ms, fixed rate will wait only 800ms until next retry.
`scheduleWithFixedDelay()` on the other hand, always waits for the same amount of time (1 second in our case) between retries.
Both behaviours are of course desirable under different circumstances.
Only remember that when `doStuff()` is slower than 1 second `scheduleAtFixedRate()` will not preserve desired frequency.
Even though our `ScheduledExecutorService` has 10 threads, `doStuff()` will never be invoked concurrently and overlap with previous execution.
Therefore, in this case, the rate will actually be smaller than configured.

# Scheduling in RxJava

Simulating `scheduleAtFixedRate()` with RxJava is very simple with `interval()` operator.
With a few caveats:

```java
Flowable
        .interval(2, 1, SECONDS)
        .subscribe(i -> doStuff());
```

If `doStuff()` is slower than 1 second, bad things happen.
First of all, we are using `Schedulers.computation()` thread pool, default one inherited from `interval()` operator.
It's a bad idea, this thread pool should only be used for CPU-intensive tasks and is shared across whole RxJava.
A better idea is to use your own scheduler (or at least `io()`):

```java
Flowable
        .interval(2, 1, SECONDS)
        .observeOn(Schedulers.io())
        .subscribe(i -> doStuff());
```

`observeOn()` switches from `computation()` scheduler used by `interval()` to `io()` scheduler.
Because `subscribe()` method is never invoked concurrently by design, `doStuff()` is never invoked concurrently, just like with `scheduleAtFixedRate()`.
However, `interval()` operator tries very hard to keep the constant frequency.
This means if `doStuff()` is slower than 1 second after a while we should expect `MissingBackpressureException`...
RxJava basically tells us that our subscriber is too slow, but `interval()` (by design) can't slow down.
If you tolerate (or even expect) overlapping concurrent executions of `doStuff()`, it's very simple to fix.
First, you must wrap blocking `doStuff()` with non-blocking `Completable`.
Technically, `Flowable` `Single` or `Maybe` would work just as well, but since `doStuff()` is `void`, `Completable` sounds fine:

```java
import io.reactivex.Completable;
import io.reactivex.schedulers.Schedulers;

Completable doStuffAsync() {
    return Completable
            .fromRunnable(this::doStuff)
            .subscribeOn(Schedulers.io())
            .doOnError(e -> log.error("Stuff failed", e))
            .onErrorComplete();
}
```

It's important to catch and swallow exceptions, otherwise a single error will cause whole `interval()` to interrupt.
`doOnError()` allows logging, but it passes the exception through downstream.
`doOnComplete()` on the other hand, simply swallows the exception.
We can now simply run this operation at each interval event:

```java
Flowable
        .interval(2, 1, SECONDS)
        .flatMapCompletable(i -> doStuffAsync())
        .subscribe();
```

If you don't `subscribe()` loop will never start - but that's RxJava 101.
Notice that if `doStuffAsync()` takes more than one second to complete we will get overlapping, concurrent executions.
There is nothing wrong with that, you just have to be aware of it.
But what if what you really need is a fixed delay?

# Fixed delays in RxJava

In some cases you need fixed delay: tasks should not overlap and we should keep some breathing time between executions.
No matter how slow periodic task is, there should always be a constant time pause.
`interval()` operator is not suitable to implement this requirement.
However if turns out the solution in RxJava is embarrassingly simple.
Think about it: you need to sleep for a while, run some task and when this task completes, repeat.
Let me tell it again:

- sleep for a while (have some sort of a `timer()`) 
- run some task and wait for it to `complete()` 
- `repeat()`

That's it!

```java
Flowable
        .timer(1, SECONDS)
        .flatMapCompletable(i -> doStuffAsync())
        .repeat()
        .subscribe();
```

`timer()` operator emits a single event (`0` of type `Long`) after a second.
We use this event to trigger `doStuffAsync()`.
When our *stuff* is done, the whole stream completes - but we would like to repeat!
Well, `repeat()` operator does just that: when it receives completion notification from upstream, it resubscribes.
Resubscription basically means: wait 1 second more, fire `doStuffAsync()` - and so on.
