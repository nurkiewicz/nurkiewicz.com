---
layout: post
title: 'Idiomatic concurrency: flatMap() vs. parallel() - RxJava FAQ'
date: '2017-09-14T10:10:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- concurrency
- rxjava
modified_time: '2017-09-14T12:56:14.751+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8066220601726729227
blogger_orig_url: https://www.nurkiewicz.com/2017/09/idiomatic-concurrency-flatmap-vs.html
image:
  path: /assets/img/idiomatic-concurrency-flatmap-vs/hero.jpg
  alt: "Bieszczady mountains"
---

Simple, effective and safe concurrency was one of the design principles of RxJava.
Yet, ironically, it's probably one of the most misunderstood aspects of this library.
Let's take a simple example: imagine we have a bunch of `UUID`s and for each one of them we must perform a set of tasks.
The first problem is to perform I/O intensive operation per each `UUID`, for example loading an object from a database:

```java
Flowable<UUID> ids = Flowable
        .fromCallable(UUID::randomUUID)
        .repeat()
        .take(100);

ids.subscribe(id -> slowLoadBy(id));
```

First I'm generating 100 random `UUID`s just for the sake of testing.
Then for each `UUID` I'd like to load a record using the following method:

```java
Person slowLoadBy(UUID id) {
    //...
}
```

The implementation of `slowLoadBy()` is irrelevant, just keep in mind it's slow and blocking.
Using `subscribe()` to invoke `slowLoadBy()` has many disadvantages:

- `subscribe()` is single-threaded by design and there is no way around it.
  Each `UUID` is loaded sequentially
- when you call `subscribe()` you can not transform `Person` object further.
  It's a terminal operation

A more robust, and even more broken, approach is to `map()` each `UUID`:

```java
Flowable<Person> people = ids
        .map(id -> slowLoadBy(id));  //BROKEN
```

This is very readable but unfortunately broken.
Operators, just like subscribers, are single-threaded.
This means at any given time only one `UUID` can be mapped, no concurrency is allowed here as well.
To make matters worse, we are inheriting thread/worker from upstream.
This has several drawbacks.
If the upstream produces events using some dedicated scheduler, we will hijack threads from that scheduler.
For example many operators, like `interval()`, use `Schedulers.computation()` thread pool transparently.
We suddenly start to perform I/O intensive operations on a pool that is totally not suitable for that.
Moreover, we slow down the whole pipeline with this one blocking, sequential step.
Very, very bad.

You might have heard about this `subscribeOn()` operator and how it enables concurrency.
Indeed, but you have to be very careful when applying it.
The following sample is (again) *wrong*:

```java
import io.reactivex.schedulers.Schedulers;


Flowable<Person> people = ids
        .subscribeOn(Schedulers.io())
        .map(id -> slowLoadBy(id)); //BROKEN
```

The code snippet above is still broken.
`subscribeOn()` (and `observeOn()` for that matter) barely switch execution to a different worker (thread) without introducing any concurrency.
The stream still sequentially processes all events, but on a different thread.
In other words - rather than consuming events sequentially on a thread inherited from upstream, we now consume them sequentially on `io()` thread.
So what about this mythical `flatMap()` operator?

# `flatMap()` operator to the rescue

`flatMap()` operator enables concurrency by splitting a stream of events into a stream of substreams.
But first, one more broken example:

```java
Flowable<Person> asyncLoadBy(UUID id) {
    return Flowable.fromCallable(() -> slowLoadBy(id));
}

Flowable<Person> people = ids
        .subscribeOn(Schedulers.io())
        .flatMap(id -> asyncLoadBy(id)); //BROKEN
```

Oh gosh, this is still *broken*!
`flatMap()` operator logically does two things:

- applying the transformation (`id -> asyncLoadBy(id)`) on each upstream event - this produces `Flowable<Flowable<Person>>`.
  This makes sense, for each upstream `UUID` we get a `Flowable<Person>` so we end up with a stream of streams of `Person` objects
- then `flatMap()` tries to subscribe to *all* of these inner sub-streams at once.
  Whenever any of the substreams emit a `Person` event, it is transparently passed as an outcome of outer `Flowable`.

Technically, `flatMap()` only creates and subscribes to the first 128 (by default, optional `maxConcurrency` parameter) substreams.
Also when the last substream completes, outer stream of `Person` completes as well.
Now, why on earth is this broken?
RxJava doesn't introduce any thread pool unless explicitly asked for.
For example this piece of code is still blocking:

```java
log.info("Setup");
Flowable<String> blocking = Flowable
        .fromCallable(() -> {
            log.info("Starting");
            TimeUnit.SECONDS.sleep(1);
            log.info("Done");
            return "Hello, world!";
        });
log.info("Created");
blocking.subscribe(s -> log.info("Received {}", s));
log.info("Done");
```

Look at the output carefully, especially on the order of events and threads involved:

```java
19:57:28.847 | INFO  | main | Setup
19:57:28.943 | INFO  | main | Created
19:57:28.949 | INFO  | main | Starting
19:57:29.954 | INFO  | main | Done
19:57:29.955 | INFO  | main | Received Hello, world!
19:57:29.957 | INFO  | main | Done
```

No concurrency whatsoever, no extra threads.
Merely wrapping blocking code in a `Flowable` doesn't magically add concurrency.
You have to explicitly use...
`subscribeOn()`:

```java
log.info("Setup");
Flowable<String> blocking = Flowable
        .fromCallable(() -> {
            log.info("Starting");
            TimeUnit.SECONDS.sleep(1);
            log.info("Done");
            return "Hello, world!";
        })
        .subscribeOn(Schedulers.io());
log.info("Created");
blocking.subscribe(s -> log.info("Received {}", s));
log.info("Done");
```

The output this time is more promising:

```java
19:59:10.547 | INFO  | main | Setup
19:59:10.653 | INFO  | main | Created
19:59:10.662 | INFO  | main | Done
19:59:10.664 | INFO  | RxCachedThreadScheduler-1 | Starting
19:59:11.668 | INFO  | RxCachedThreadScheduler-1 | Done
19:59:11.669 | INFO  | RxCachedThreadScheduler-1 | Received Hello, world!
```

But we *did* use `subscribeOn()` last time, what's going on?
Well, `subscribeOn()` on the outer stream level basically said that all events should be processed sequentially, within this stream, on a different thread.
We didn't say that there should many sub-streams running concurrently.
And because all sub-streams are blocking, when RxJava tries to subscribe to all of them, it effectively subscribes sequentially to one after another.
`asyncLoadBy()` is not really *async*, thus it blocks when `flatMap()` operator tries to subscribe to it.
The fix is easy.
Normally you would put `subscribeOn()` inside `asyncLoadBy()` but for educational purposes I'll place it directly in the main pipeline:

```java
Flowable<Person> people = ids
    .flatMap(id -> asyncLoadBy(id).subscribeOn(Schedulers.io()));
```

Now it works like a charm!
By default RxJava will take first 128 upstream events (`UUID`s), turn them into sub-streams and subscribe to all of them.
If sub-streams are asynchronous and highly parallelizable (e.g.
network calls), we get 128 concurrent invocations of `asyncLoadBy()`.
The concurrency level (128) is configurable via `maxConcurrency` parameter:

```java
Flowable<Person> people = ids
    .flatMap(id ->
                asyncLoadBy(id).subscribeOn(Schedulers.io()),
                10  //maxConcurrency
    );
```

That was a lot of work, don't you think?
Shouldn't concurrency be even more declarative?
We no longer deal with `Executor`s and futures, but still, it seems this approach is too error prone.
Can't it be as simple as `parallel()` in Java 8 streams?

# Enter `ParallelFlowable`

Let's first look again at our example and make it even more complex by adding `filter()`:

```java
Flowable<Person> people = ids
        .map(this::slowLoadBy)     //BROKEN
        .filter(this::hasLowRisk); //BROKEN
```

where `hasLowRisk()` is a *slow* predicate:

```java
boolean hasLowRisk(Person p) {
    //slow...
}
```

We already know that idiomatic approach to this problem is by using `flatMap()`, twice:

```java
Flowable<Person> people = ids
        .flatMap(id -> asyncLoadBy(id).subscribeOn(io()))
        .flatMap(p -> asyncHasLowRisk(p).subscribeOn(io()));
```

`asyncHasLowRisk()` is rather obscure - it either returns a single-element stream when predicate passes or an empty stream when it fails.
This is how you emulate `filter()` using `flatMap()`.
Can we do better?
Since RxJava 2.0.5 there is a new operator called...
`parallel()`!
It's quite surprising because operator with the same name [was removed](https://github.com/ReactiveX/RxJava/issues/1673) before RxJava became 1.0 due to many misconceptions and being misused.
`parallel()` in 2.x seems to finally address the problem of idiomatic concurrency in a safe and declarative way.
First, let's see some beautiful code!

```java
Flowable<Person> people = ids
        .parallel(10)
        .runOn(Schedulers.io())
        .map(this::slowLoadBy)
        .filter(this::hasLowRisk)
        .sequential();
```

Just like that!
A block of code between `parallel()` and `sequential()` runs...
in parallel.
What do we have here?
First of all the new `parallel()` operator turns `Flowable<UUID>` into `ParallelFlowable<UUID>` which has a much smaller API than Flowable.
You'll see in a second why.
The optional `int` parameter (`10` in our case) defines concurrency, or (as the documentation puts it) how many concurrent "rails" are created.
So for us we split single `Flowable<Person>` into 10 concurrent, independent rails (think: *threads*).
Events from original stream of `UUID`s are split (`modulo 10`) into different rails, sub-streams that are independent from each other.
Think of them as sending upstream events into 10 separate threads.
But first we have to define where these threads come from - using handy `runOn()` operator.
This is so much better than `parallel()` on Java 8 streams where you have no control over concurrency level.

At this point we have a `ParallelFlowable`.
When an event appears in upstream (`UUID`) it is delegated to one of 10 "rails", concurrent, independent pipelines.
Pipeline provides a limited subset of operators that are safe to run concurrently, e.g. `map()` and `filter()`, but also `reduce()`.
There is no `buffer()`, `take()` etc. as their semantics are unclear when invoked on many sub-streams at once.
Our blocking `slowLoadBy()` as well as `hasLowRisk()` are still invoked sequentially, but only within single "rail".
Because we now have 10 concurrent "rails", we effectively parallelized them without much effort.

When events reach the end of sub-stream ("rail") they encounter `sequential()` operator.
This operator turns `ParallelFlowable` back into `Flowable`.
As long as our mappers and filters are thread-safe, `parallel()`/`sequential()` pair provides very easy way of parallelizing streams.
One small caveat - you will inevitably get messages reordered.
Sequential `map()` and `filter()` always preserve order (like most operators).
But once you run them within `parallel()` block, the order is lost.
This allows for greater concurrency, but you have to keep that in mind.

Should you use `parallel()` rather than nested `flatMap()` to parallelize your code?
It's up to you, but `parallel()` seems to be much easier to read and grasp.
