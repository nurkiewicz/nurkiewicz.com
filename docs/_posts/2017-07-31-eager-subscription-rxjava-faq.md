---
layout: post
title: Eager subscription - RxJava FAQ
date: '2017-07-31T20:22:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- rxjava
modified_time: '2017-07-31T21:06:44.103+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-6661917617402010710
blogger_orig_url: https://www.nurkiewicz.com/2017/07/eager-subscription-rxjava-faq.html
image:
  path: /assets/img/eager-subscription-rxjava-faq/hero.jpg
  alt: "Warsaw center from&nbsp;Park Szczęśliwicki"
---

While teaching and mentoring RxJava, as well as after [authoring a book](http://shop.oreilly.com/product/0636920042228.do), I noticed some areas are especially problematic.
I decided to publish a bunch of short tips that address most common pitfalls.
This is the first part.
`Observable`s and `Flowable`s are lazy by nature.
This means no matter how heavy or long-running logic you place inside your `Flowable`, it will get evaluated only when someone subscribes.
And also as many times as someone subscribes.
This is illustrated by the following code snippet:

```java
private static String slow() throws InterruptedException {
    logger.info("Running");
    TimeUnit.SECONDS.sleep(1);
    return "abc";
}

//...

Flowable<String> flo = Flowable.fromCallable(this::slow);
logger.info("Created");
flo.subscribe();
flo.subscribe();
logger.info("Done");
```

Such `Observable` or `Flowable` will inevitably print:

```java
19:37:57.368 [main] - Created
19:37:57.379 [main] - Running
19:37:58.383 [main] - Running
19:37:59.388 [main] - Done
```

Notice that you pay the price of `sleep()` twice (double subscription).
Moreover all logic runs in client (`main`) thread, there is no implicit threading in RxJava unless requested with `subscribeOn()` or implicitly available with asynchronous streams.
The question is: can we force running subscription logic eagerly so that whenever someone subscribes the stream is already precomputed or at least the computation started?

## Totally eager evaluation

The most obvious, but flawed solution is to eagerly compute whatever the stream returns and simply wrap it with a fixed `Flowable`:

```java
Flowable<String> eager() {
    final String slow = slow();
    return Flowable.just(slow);
}
```

Unfortunately this substantially defeats the purpose of RxJava.
First of all operators like `subscribeOn()` no longer work and it becomes impossible to off-load computation to a different thread.
Even worse, even though `eager()` returns a `Flowable` it will always, by definition, block client thread.
It is harder to reason, compose and manage such streams.
You should generally avoid such pattern and prefer lazy-loading even when eager evaluation is necessary.

## Using `cache()` operator

The next example does just that with `cache()` operator:

```java
Flowable<String> eager3() throws InterruptedException {
    final Flowable<String> cached =
        Flowable
            .fromCallable(this::slow)
            .cache();
    cached.subscribe();
    return cached;
}
```

The idea is simple: wrap computation with lazy `Flowable` and make it cached.
What `cache()` operator does is it remembers all emitted events upon first subscription so that when second `Subscriber` appears, it will receive the same *cached* sequence of events.
However `cache()` operator (like most others) is lazy so we must forcibly subscribe for the first time.
Calling `subscribe()` will prepopulate cache, moreover if second subscriber appears before `slow()` computation finishes, it will wait for it as well rather than starting it for the second time.

This solution works but keep in mind that `subscribe()` will actually block because no `Scheduler` was involved.
If you want to prepopulate your `Flowable` in background, try `subscribeOn()`:

```java
Flowable<String> eager3() throws InterruptedException {
    final Flowable<String> cached =
        Flowable
            .fromCallable(this::slow)
            .subscribeOn(justDontAlwaysUse_Schedulers.io())
            .cache();
    cached.subscribe();
    return cached;
}
```

Yes, using `Schedulers.io()` is problematic and hard to maintain on production systems so please avoid it in favor of custom thread pools.

## Error handling

Sadly it's surprisingly easy to swallow exceptions in RxJava.
That's what can happen in our last example if `slow()` method fails.
The exception isn't swallowed entirely, but by default, if no-one was interested, it's stack trace is printed on `System.err`.
Also unhandled exception is wrapped with `OnErrorNotImplementedException`.
Not very convenient and most likely lost if you are doing any form of centralized logging.
You can use `doOnError()` operator for logging but it still passes exception downstream and RxJava considers it unhandled as well, one more time wrapping with `OnErrorNotImplementedException`.
So let's implement `onError` callback in `subscribe()`:

```java
Flowable<String> eager3() throws InterruptedException {
    final Flowable<String> cached =
        Flowable
            .fromCallable(this::slow)
            .cache();
    cached.subscribe(
            x -> {/* ignore */},
            e -> logger.error("Prepopulation error", e));
    return cached;
}
```

We don't want to handle actual events, just errors in `subscribe()`.
At this point you can safely return such `Flowable`.
It's eager and chances are that whenever yuo subscribe to it, data will already be available.
Notice that for example `observe()` method from Hystrix is eager as well, as opposed to `toObservable()`, which is lazy.
The choice is yours.
