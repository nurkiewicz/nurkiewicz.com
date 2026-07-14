---
layout: post
title: '1.x to 2.x migration: Observable vs. Observable: RxJava FAQ'
date: '2017-08-14T22:40:00.001+02:00'
author: Tomasz Nurkiewicz
tags:
- rxjava
modified_time: '2017-08-14T22:40:39.785+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-7008027362643006896
blogger_orig_url: https://www.nurkiewicz.com/2017/08/1x-to-2x-migration-observable-vs.html
image:
  path: /assets/img/1x-to-2x-migration-observable-vs/hero.jpg
  alt: "View from&nbsp;Basilica of Notre-Dame de Fourvière"
---

The title is not a mistake.
`rx.Observable` from RxJava 1.x is a completely different beast than `io.reactivex.Observable` from 2.x.
Blindly upgrading `rx` dependency and renaming all imports in your project will compile (with minor changes) but does not guarantee the same behavior.
In the very early days of the project `Observable` in 1.x had no notion of backpressure but later on backpressure was included.
What does it actually mean?
Let's imagine we have a stream that produces one event every 1 millisecond but it takes 1 **second** to process one such item.
You see it can't possibly work this way in the long run:

```java
import rx.Observable;  //RxJava 1.x
import rx.schedulers.Schedulers;

Observable
        .interval(1, MILLISECONDS)
        .observeOn(Schedulers.computation())
        .subscribe(
                x -> sleep(Duration.ofSeconds(1)));
```

`MissingBackpressureException` creeps in within few hundred milliseconds.
But what does this exception mean?
Well, basically it's a safety net (or sanity check if you will) that prevents you from hurting your application.
RxJava automatically discovers that producer is overflowing the consumer and proactively terminates the stream to avoid further damage.
So what if we simply *search and replace* few imports here and there?

```java
import io.reactivex.Observable;     //RxJava 2.x
import io.reactivex.schedulers.Schedulers;

Observable
        .interval(1, MILLISECONDS)
        .observeOn(Schedulers.computation())
        .subscribe(
                x -> sleep(Duration.ofSeconds(1)));
```

The exception is gone!
So is our throughput...
The application stalls after a while, staying in an endless GC loop.
You see, `Observable` in RxJava 1.x has assertions (bounded queues, checks, etc.)
all over the place, making sure you are not overflowing anywhere.
For example `observeOn()` operator in 1.x has a queue limited to 128 elements by default.
When backpressure is properly implemented across the whole stack, `observeOn()` operator asks upstream to deliver not more than 128 elements to fill in its internal buffer.
Then separate threads (workers) from this scheduler are picking up events from this queue.
When queue becomes almost empty, `observeOn()` operator asks (`request()` method) for more.
This mechanism breaks apart when producer does not respect backpressure requests and sends more data than it was allowed, effectively overflowing the consumer.
The internal queue inside `observeOn()` operator is full, yet `interval()` operator keeps emitting new events - because that's what `interval()` is suppose to do.

`Observable` in 1.x discovers such overflow and fails fast with `MissingBackpressureException`.
It literally means: *I tried so hard to keep the system in healthy state, but my upstream is not respecting backpressure - backpressure implementation is missing*.
However `Observable` in 2.x has no such safety mechanism.
It's a vanilla stream that hopes you will be a good citizen and either have slow producers or fast consumers.
When system is healthy, both `Observable`s behave the same way.
However under load 1.x fails fast, 2.x fails slowly and painfully.

Does it mean RxJava 2.x is a step back?
Quite the contrary!
In 2.x an important distinction was made:

- `Observable` doesn't care about backpressure, which greatly simplifies its design and implementation.
  It should be used to model streams that can't support backpressure by definition, e.g. user interface events
- `Flowable` does support backpressure and has all the safety measures in place.
  In other words all steps in computation pipeline make sure you are not overflowing the consumer.

2.x makes an important distinction between streams that can support backpressure ("*can slow down if needed*" in simple words) and those that don't.
From the type system perspective it becomes clear what kind of source are we dealing with and what are its guarantees.
So how should we migrate our `interval()` example to RxJava 2.x?
Easier than you think:

```java
Flowable
        .interval(1, MILLISECONDS)
        .observeOn(Schedulers.computation())
        .subscribe(
                x -> sleep(Duration.ofSeconds(1)));
```

That simple.
You may ask yourself a question, how come `Flowable` can have `interval()` operator that, by definition, can't support backpressure?
After all `interval()` is suppose to deliver events at constant rate, it can't slow down!
Well, if you look at the declaration of `interval()` you'll notice:

```java
@BackpressureSupport(BackpressureKind.ERROR)
```

Simply put this tells us that whenever backpressure can no longer be guaranteed, RxJava will take care of it and throw `MissingBackpressureException`.
That's precisely what happens when we run `Flowable.interval()` program - it fails fast, as opposed to destabilizing whole application.

So, to wrap up, whenever you see an `Observable` from 1.x, what you probably want is `Flowable` from 2.x.
At least unless your stream by definition does not support backpressure.
Despite same name, `Observable`s in these two major releases are quite different.
But once you do a *search and replace* from `Observable` to `Flowable` you'll notice that migration isn't that straightforward.
It's not about API changes, the differences are more profound.

There is no simple `Flowable.create()` directly equivalent to `Observable.create()` in 2.x.
I made a mistake myself to overuse `Observable.create()` factory method in the past.
`create()` allows you to emit events at an arbitrary rate, entirely ignoring backpressure.
2.x has some friendly facilities to deal with backpressure requests, but they require careful design of your streams.
This will be covered in the next FAQ.
