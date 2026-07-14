---
layout: post
title: Generating backpressure-aware streams with Flowable.generate() - RxJava FAQ
date: '2017-08-17T22:57:00.001+02:00'
author: Tomasz Nurkiewicz
tags:
- backpressure
- rxjava
modified_time: '2017-08-17T22:58:55.070+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1716158098842612685
blogger_orig_url: https://www.nurkiewicz.com/2017/08/generating-backpressure-aware-streams.html
image:
  path: /assets/img/generating-backpressure-aware-streams/hero.jpg
  alt: "Babia Góra, Poland"
---

RxJava is missing a factory to create an infinite stream of natural numbers.
Such a stream is useful e.g. when you want to assign unique sequence numbers to possibly infinite stream of events by zipping both of them:

```java
Flowable<Long> naturalNumbers = //???

Flowable<Event> someInfiniteEventStream = //...
Flowable<Pair<Long, Event>> sequenced = Flowable.zip(
        naturalNumbers,
        someInfiniteEventStream,
        Pair::of
);
```

Implementing `naturalNumbers` is surprisingly complex.
In RxJava 1.x you could briefly get away with `Observable` that does not respect backpressure:

```java
import rx.Observable;  //RxJava 1.x

Observable<Long> naturalNumbers = Observable.create(subscriber -> {
    long state = 0;
    //poor solution :-(
    while (!subscriber.isUnsubscribed()) {
        subscriber.onNext(state++);
    }
});
```

What does it mean that such stream is not backpressure-aware?
Well, basically the stream produces events (ever-incrementing `state` variable) as fast as the CPU core permits, millions per second, easily.
However when consumers can't consume events so fast, growing backlog of unprocessed events starts to appear:

```java
naturalNumbers
//      .observeOn(Schedulers.io())
        .subscribe(
                x -> {
                    //slooow, 1 millisecond
                }
        );
```

The program above (with `observeOn()` operator commented out) runs just fine because it has *accidental* backpressure.
By default everything is single threaded in RxJava, thus producer and consumer work within the same thread.
Invoking `subscriber.onNext()` actually blocks, so the `while` loop throttles itself automatically.
But try uncommenting `observeOn()` and disaster happens a few milliseconds later.
The subscription callback is single-threaded by design.
For every element it needs at least 1 millisecond, therefore this stream can process not more than 1000 events per second.
We are somewhat lucky.
RxJava quickly discovers this disastrous condition and fails fast with `MissingBackpressureException`

Our biggest mistake was producing events without taking into account how slow the consumer is.
By the way this is the core idea behind [reactive streams](http://www.reactive-streams.org/): producer is not allowed to emit more events than requested by consumer.
In RxJava 1.x implementing even the simplest stream that was respecting backpressure from scratch was a non-trivial task.
RxJava 2.x brought several convenient operators that built on top of experience from previous versions.
First of all RxJava 2.x does not allow you to implement `Flowable` (backpressure-aware) the same way as you can with `Observable`.
It's not possible to create `Flowable` that overloads the consumer with messages:

```java
Flowable<Long> naturalNumbers = Flowable.create(subscriber -> {
    long state = 0;
    while (!subscriber.isCancelled()) {
        subscriber.onNext(state++);
    }
}, BackpressureStrategy.DROP);
```

Did you spot this extra `DROP` parameter?
Before we explain it, let's see the output when we subscribe with slow consumer:

```java
0
1
2
3
//...continuous numbers...
126
127
101811682
//...where did my 100M events go?!?
101811683
101811684
101811685
//...continuous numbers...
101811776
//...17M events disappeared again...
101811777
//...
```

Your mileage may vary.
What happens?
The `observeOn()` operator switches between schedulers (thread pools).
A pool of threads that are hydrated from a queue of pending events.
This queue is finite and has capacity of 128 elements.
`observeOn()` operator, knowing about this limitation, only requests 128 elements from upstream (our custom `Flowable`).
At this point it lets our subscriber process the events, 1 per millisecond.
So after around 100 milliseconds `observeOn()` discovers its internal queue is almost empty and asks for more.
Does it get 128, 129, 130...?
No!
Our `Flowable` was producing events like crazy during this 0.1 second period and it (astonishingly) managed to generate more than **100 million** numbers in that time frame.
Where did they go?
Well, `observeOn()` was not asking for them so the `DROP` strategy (a mandatory parameter) simply discarded unwanted events.

## `BackpressureStrategy`

That doesn't sound right, are there any other strategies?
Yes, many:

- `BackpressureStrategy.BUFFER`: If upstream produces too many events, they are buffered in an unbounded queue.
  No events are lost, but your whole application most likely is.
  If you are lucky, `OutOfMemoryError` will save you.
  I got stuck on 5+ second long GC pauses.
- `BackpressureStrategy.ERROR`: If over-production of events is discovered, `MissingBackpressureException` will be thrown.
  It's a sane (and safe) strategy.
- `BackpressureStrategy.LATEST`: Similar to `DROP`, but remembers last dropped event.
  Just in case request for more data comes in but we just dropped everything - we at least have the last seen value.
- `BackpressureStrategy.MISSING`: No safety measures, deal with it.
  Most likely one of the downstream operators (like `observeOn()`) will throw `MissingBackpressureException`.
- `BackpressureStrategy.DROP`: drops events that were not requested.

By the way when you are turning an `Observable` to `Flowable` you must also provide `BackpressureStrategy`.
RxJava must know how to limit over-producing `Observable`.
OK, so what is the correct implementation of such a simple stream of sequential natural numbers?

## Meet `Flowable.generate()`

The difference between `create()` and `generate()` lies in responsibility.
`Flowable.create()` is suppose to generate the stream in its entirety with no respect to backpressure.
It simply produces events whenever it wishes to do so.
`Flowable.generate()` on the other hand is only allowed to generate one event at a time (or complete a stream).
Backpressure mechanism transparently figures out how many events it needs at the moment.
`generate()` is called appropriate number of times, for example 128 times in case of `observeOn()`.

Because this operator produces events one at a time, typically it needs some sort of state to figure out where it was the last time<sup>1</sup>.
This is what `generate()` is: a holder for (im)mutable state and a function that generates next event based on it:

```java
Flowable<Long> naturalNumbers =
    Flowable.generate(() -> 0L, (state, emitter) -> {
        emitter.onNext(state);
        return state + 1;
    });
```

The first argument to `generate()` is an initial state (factory), `0L` in our case.
Now every time a subscriber or any downstream operator asks for some number of events, the lambda expression is invoked.
Its responsibility is to call `onNext()` at most once (emit at most one event) somehow based on supplied state.
When lambda is invoked for the first time the `state` is equal to initial value `0L`.
However we are allowed to modify the state and return its new value.
In this example we increment `long` so that subsequent invocation of lambda expression receives `state = 1L`.
Obviously this goes on and on, producing consecutive natural numbers.

Such a programming model is obviously harder than a `while` loop.
It also fundamentally changes the way you implement your sources of events.
Rather than pushing events whenever you feel like it you are only passively waiting for requests.
Downstream operators and subscribers are *pulling* data from your stream.
This shift enables backpressure at all levels of your pipeline.

`generate()` has a few flavors.
First of all if your state is a mutable object you can use an overloaded version that does not require returning new state value.
Despite being less *functional* mutable state tends to produce way less garbage.
This assumes your state is constantly mutated and the same state object instance is passed every time.
For example you can easily turn an `Iterator` (also pull-based!)
into a stream with all wonders of backpressure:

```java
Iterator<Integer> iter = //...

Flowable<String> strings = Flowable.generate(() -> iter, (iterator, emitter) -> {
    if (iterator.hasNext()) {
        emitter.onNext(iterator.next().toString());
    } else {
        emitter.onComplete();
    }
}); 
```

Notice that the type of stream (`<String>`) doesn't have to be the same as the type of state (`Iterator<Integer>`).
Of course if you have a Java `Collection` and want to turn it into a stream, you don't have to create an iterator first.
It's enough to use `Flowable.fromIterable()`.
Even simpler version of `generate()` assumes you have no state at all.
For example stream of random numbers:

```java
Flowable<Double> randoms = Flowable
        .generate(emitter -> emitter.onNext(Math.random()));
```

But honestly, you will probably need an instance of `Random` after all:

```java
Flowable.generate(Random::new, (random, emitter) -> {
    emitter.onNext(random.nextBoolean());
});
```

## Summary

As you can see `Observable.create()` in RxJava 1.x and `Flowable.create()` have some shortcomings.
If you really care about scalability and health of your heavily concurrent system (and otherwise you wouldn't be reading this!)
you must be aware of backpressure.
If you really need to create streams from scratch, as opposed to using `from*()` family of methods or various libraries that do the heavy lifting - familiarize yourself with `generate()`.
In essence you must learn how to model certain types of data sources as fancy iterators.
Expect more articles explaining how to implement more real-life streams.

<sup></sup> This is similar to stateless HTTP protocol that uses small pieces of state called session\* on the server to keep track of past requests.
