---
layout: post
title: Detecting and testing stalled streams - RxJava FAQ
date: '2017-09-11T09:00:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- rxjava
modified_time: '2017-09-11T09:29:57.200+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-132278296001058002
blogger_orig_url: https://www.nurkiewicz.com/2017/09/detecting-and-testing-stalled-stream.html
image:
  path: /assets/img/detecting-and-testing-stalled-stream/hero.jpg
  alt: "Topiło Lake, Białowieża Forest"
---

Imagine you have a stream that publishes events with unpredictable frequency.
Sometimes you can expect dozens of messages per second, but occasionally no events can be seen for several seconds.
This can be an issue if your stream is transmitted over web socket, SSE or any other network protocol.
Silent period taking too long (stall) can be interpreted as network issue.
Therefore we often send artificial events (*pings*) once in a while just to make sure:

- clients are still alive
- let clients know *we* are still alive

A more concrete example, imagine we have a `Flowable<String>` stream that produces some events.
When there is no event for more than one second, we should send a placeholder `"PING"` message.
When the silence is even longer, there should be a `"PING"` message every second.
How can we implement such a requirement in RxJava?
The most obvious, but incorrect solution is to merge original stream with *pings*:

```java
Flowable<String> events = //...
Flowable<String> pings = Flowable
            .interval(1, SECONDS)
            .map(x -> "PING");

Flowable<String> eventsWithPings = events.mergeWith(pings);
```

`mergeWith()` operator is crucial: it takes genuine `events` and combines them with a constant stream of pings.
Surely, when no genuine events are presents, `"PING"` messages will appear.
Unfortunately they are entirely unrelated to original stream.
This means we keep sending pings even when there are plenty of normal events.
Moreover when the silence begins we do not send `"PING"` precisely after one second.
If you are OK with such mechanism, you may stop reading here.

# `debounce()` operator

A more sophisticated approach requires discovering silence that lasts for more than 1 second.
We can use `timeout()` operator for that.
Unfortunately it yields `TimeoutException` and unsubscribes from upstream - way too aggressive behaviour.
We just want to get some sort of notification.
Turns out `debounce()` operator can be used for that.
Normally this operator postpones emission of new events just in case new events arrive, overriding the old ones.
So if I say:

```java
Flowable<String> events = //...
Flowable<String> delayed = events.debounce(1, SECONDS);
```

This means `delayed` stream will only emit an event if it was *not* followed by another event within 1 second.
Technically `delayed` may never emit anything if `events` stream keeps producing events fast enough.
We will use the `delayed` stream to discover silence in the following way:

```java
Flowable<String> events = //...
Flowable<String> delayed = events.debounce(1, SECONDS);
Flowable<String> pings = delayed.map(ev -> "PING");
Flowable<String> eventsWithPings = Flowable.merge(events, pings);
```

Keep in mind that there is no difference between `mergeWith()` and its `static` `merge()` counterpart.
So we are getting somewhere.
If the stream is busy, `delayed` stream never receives any events, therefore no `"PING"` messages are sent.
However when original stream does not send any event for more than 1 second, `delayed` receives the last seen event, ignores it and transforms into `"PING"`.
Clever, but broken.
This implementation only sends one `"PING"` after discovering stall, as opposed to sending periodic pings every second.
Fairly easy to fix!
Rather than transforming the last seen event into single `"PING"` we can transform it into a sequence of periodic *pings*:

```java
Flowable<String> events = //...
Flowable<String> delayed = events.debounce(1, SECONDS);
Flowable<String> pings = delayed
        .flatMap(x -> Flowable
                .interval(0, 1, SECONDS)
                .map(e -> "PING")
        );
Flowable<String> eventsWithPings = Flowable.merge(events, pings);
```

Can you see where the flaw is?
Every time a bit of silence appears in the original stream, we start emitting *pings* every second.
However we should stop doing so once some genuine events appear.
We don't.
Every stall in the upstream causes new infinite stream of pings to appear on the final merged stream.
We must somehow tell the the `pings` stream that it should stop emitting *pings* because the original stream emitted genuine event.
Guess what, there is `takeUntil()` operator that does just that!

```java
    Flowable<String> events = //...
    Flowable<String> delayed = events.debounce(1, SECONDS);
    Flowable<String> pings = delayed
            .flatMap(x -> Flowable
                    .interval(0, 1, SECONDS)
                    .map(e -> "PING")
                    .takeUntil(events)
            );
    Flowable<String> eventsWithPings = Flowable.merge(events, pings);
```

Take a moment to fully grasp the above code snippet.
`delayed` stream emits an event every time nothing happens on the original stream for more than 1 second.
`pings` stream emits a sequence of `"PING"` events every second for each event emitted from `delayed`.
However `pings` stream is terminated the moment an event appears on the `events` stream.
You can even define all of this as a single expression:

```java
Flowable<String> events = //...
Flowable<String> eventsWithPings = events
        .mergeWith(
                events
                        .debounce(1, SECONDS)
                        .flatMap(x1 -> Flowable
                                .interval(0, 1, SECONDS)
                                .map(e -> "PING")
                                .takeUntil(events)
                        ));
```

# Testability

All right, we wrote all of this, but how are we suppose to test this triple-nested blob of event-driven code?
How do we make sure that *pings* appear at the right moment and stop when silence is over?
How to simulate various time-related scenarios?
RxJava has many killer features but testing how time passes through is probably the biggest one.
First of all let's make our pinging code a little bit more testable and generic:

```java
<T> Flowable<T> withPings(Flowable<T> events, Scheduler clock, T ping) {
    return events
            .mergeWith(
                    events
                            .debounce(1, SECONDS, clock)
                            .flatMap(x1 -> Flowable
                                    .interval(0, 1, SECONDS, clock)
                                    .map(e -> ping)
                                    .takeUntil(events)
                            ));

}
```

This utility method takes arbitrary stream of `T` and adds *pings* in case the stream doesn't produce any events for a longer period of time.
We use it like this in our test:

```java
PublishProcessor<String> events = PublishProcessor.create();
TestScheduler clock = new TestScheduler();
Flowable<String> eventsWithPings = withPings(events, clock, "PING");
```

Oh boy, `PublishProcessor`, `TestScheduler`?
`PublishProcessor` is an interesting class that is a subtype of `Flowable` (so we can use it as an ordinary stream).
On the other hand we can imperatively emit events using its `onNext()` method:

```java
events.onNext("A");
```

If someone listens to `events` stream, he will receive `"A"` event straight away.
And what's with this `clock` thing?
Every single operator in RxJava that deals with time in any way (e.g.
`debounce()`, `interval()`, `timeout()`, `window()`) can take an optional `Scheduler` argument.
It serves as an external source of time.
Special `TestScheduler` is an artificial source of time which we have full control of.
I.e. time stands still as long as we don't call `advanceTimeBy()` explicitly:

```java
clock.advanceTimeBy(999, MILLISECONDS);
```

999 milliseconds is not a coincidence.
*Pings* start to appear precisely after 1 second so they should not be visible after 999 milliseconds.
Now it's about time to reveal full test case:

```java
@Test
public void shouldAddPings() throws Exception {
    PublishProcessor<String> events = PublishProcessor.create();
    final TestScheduler clock = new TestScheduler();
    final Flowable<String> eventsWithPings = withPings(events, clock, "PING");

    final TestSubscriber<String> test = eventsWithPings.test();
    events.onNext("A");
    test.assertValues("A");

    clock.advanceTimeBy(999, MILLISECONDS);
    events.onNext("B");
    test.assertValues("A", "B");
    clock.advanceTimeBy(999, MILLISECONDS);
    test.assertValues("A", "B");

    clock.advanceTimeBy(1, MILLISECONDS);
    test.assertValues("A", "B", "PING");
    clock.advanceTimeBy(999, MILLISECONDS);
    test.assertValues("A", "B", "PING");

    events.onNext("C");
    test.assertValues("A", "B", "PING", "C");

    clock.advanceTimeBy(1000, MILLISECONDS);
    test.assertValues("A", "B", "PING", "C", "PING");
    clock.advanceTimeBy(999, MILLISECONDS);
    test.assertValues("A", "B", "PING", "C", "PING");

    clock.advanceTimeBy(1, MILLISECONDS);
    test.assertValues("A", "B", "PING", "C", "PING", "PING");
    clock.advanceTimeBy(999, MILLISECONDS);
    test.assertValues("A", "B", "PING", "C", "PING", "PING");

    events.onNext("D");
    test.assertValues("A", "B", "PING", "C", "PING", "PING", "D");

    clock.advanceTimeBy(999, MILLISECONDS);
    events.onNext("E");
    test.assertValues("A", "B", "PING", "C", "PING", "PING", "D", "E");
    clock.advanceTimeBy(999, MILLISECONDS);
    test.assertValues("A", "B", "PING", "C", "PING", "PING", "D", "E");

    clock.advanceTimeBy(1, MILLISECONDS);
    test.assertValues("A", "B", "PING", "C", "PING", "PING", "D", "E", "PING");

    clock.advanceTimeBy(3_000, MILLISECONDS);
    test.assertValues("A", "B", "PING", "C", "PING", "PING", "D", "E", "PING", "PING", "PING", "PING");
}
```

Looks like a wall of text but it's actually a complete testing scenario of our logic.
It makes sure *pings* appear precisely after 1000 milliseconds, are repeated when silence is very long and quite down when genuine events appear.
But the most important part: the test is 100% predictable and blazingly fast.
No [Awaitility](https://github.com/awaitility/awaitility), busy waiting, polling, intermittent test failures and slowness.
Artificial clock that we have full control of makes sure all these combined streams work exactly as expected.
