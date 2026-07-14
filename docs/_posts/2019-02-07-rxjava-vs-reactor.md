---
layout: post
title: RxJava vs Reactor
date: '2019-02-07T23:42:00.001+01:00'
author: Tomasz Nurkiewicz
tags:
- reactor
- rxjava
modified_time: '2019-02-25T23:32:39.252+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4352522775714419983
blogger_orig_url: https://www.nurkiewicz.com/2019/02/rxjava-vs-reactor.html
image: /assets/img/rxjava-vs-reactor/hero.jpg
---

# 

|     |
|:---:|
|     |
|     |

# Summary:

- Stick to whichever library you already have on your CLASSPATH.
- If you get a choice, Reactor is preferable, RxJava 2.x is still a good alternative
- In case you’re on Android, then RxJava 2.x is your *only* choice

------------------------------------------------------------------------

# Table of contents:

1.  API
2.  Type-safety
3.  Checked exceptions
4.  Testing
5.  Debugging
6.  Spring support
7.  Android development
8.  Maturity
9.  Summary

------------------------------------------------------------------------

Many people ask me, which library to use in their new projects (if any).
Some are concerned that they learned RxJava 1.x and then 2.x came along, and the Reactor.
Which one should they use?
And some also wonder, what’s with this new [`java.util.concurrent.Flow`](https://docs.oracle.com/javase/9/docs/api/java/util/concurrent/Flow.html)?
Let me clarify a few things.
First of all, both versions of RxJava and Reactor are quite similar from a functional perspective.
If you know 1.x or 2.x, Reactor will be very familiar, though you still have to learn about the differences.
Secondly, `Flow` class (a set of interfaces, to be precise) is part of a [reactive streams](http://www.reactive-streams.org/) specification, bundled into JDK.
This specification dictates that various reactive libraries should behave politely and interact with each other cleanly.
However the specification was born before Java 9 and introduction of `Flow`, therefore libraries are based on external `reactive-streams.jar`, rather than JDK.

When it comes to RxJava/Reactor comparison, there are quite a few perspectives.
Let me quickly go through some of the differences.
I assume you have some familiarity with both of these libraries.

# API

`Flowable` and `Flux` have very similar API.
Obviously, they both support basic operators like `map()`, `filter()`, `flatMap()`, as well as more advanced ones.
The main difference is the target Java version.
RxJava 2.x must still support Java 6 as it is widely used on Android (read later on).
Reactor, on the other hand, targets Java 8+.
Therefore Reactor can take advantage of modern (-ish, Java 8 is 5 years old, at the time of writing) APIs like `java.time` and `java.util.function`.
It’s so much safer to type:

```java
import java.time.Duration;
...
flux.window(Duration.ofSeconds(1));
```

as opposed to:

```java
import java.util.concurrent.TimeUnit;
...
flowable.window(1, TimeUnit.SECONDS);
```

Passing around a single `Duration` instance is easier and safer than an integer.
Also Reactor has a direct conversion from `CompletableFuture`, `Optional`, `java.util.stream.Stream`, etc. **+1 for Reactor**.

# Type-safety

But talking about type-safety, I truly miss fine-grained types introduced in RxJava 1/2.
HTML `table` is worth a thousand `div`s:

|  |  |  |
|----|----|----|
| RxJava 2 | Reactor | Purpose |
| [`Completable`](http://reactivex.io/RxJava/javadoc/io/reactivex/Completable.html) | N/A | Completes successfully or with failure, without emitting any value. Like `CompletableFuture<Void>` |
| [`Maybe<T>`](http://reactivex.io/RxJava/javadoc/io/reactivex/Maybe.html) | [`Mono<T>`](https://projectreactor.io/docs/core/release/api/reactor/core/publisher/Mono.html) | Completes successfully or with failure, may or may not emit a single value. Like an asynchronous `Optional<T>` |
| [`Single<T>`](http://reactivex.io/RxJava/javadoc/io/reactivex/Single.html) | N/A | Either complete successfully emitting exactly one item or fails. |
| [`Observable<T>`](http://reactivex.io/RxJava/javadoc/io/reactivex/Observable.html) | N/A | Emits an indefinite number of events (zero to infinite), optionally completes successfully or with failure. Does not support backpressure due to the nature of the source of events it represents. |
| [`Flowable<T>`](http://reactivex.io/RxJava/javadoc/io/reactivex/Flowable.html) | [`Flux<T>`](https://projectreactor.io/docs/core/release/api/reactor/core/publisher/Flux.html) | Emits an indefinite number of events (zero to infinite), optionally completes successfully or with failure. Support backpressure (the source can be slowed down when the consumer cannot keep up) |

The lack of some types in Reactor doesn’t mean it doesn’t support some use cases.
If you need `Completable`, you use awkward `Mono<Void>` (like `Mono.then()` operator).
You know that some operation must emit a value?
Bad luck, you are stuck with `Mono<T>` and people get confused - does it *always* emit that value?
For example [`Flux.count()`](https://projectreactor.io/docs/core/release/api/reactor/core/publisher/Flux.html#count--)).
Or maybe your `Flux` doesn’t really support backpressure?
Too bad, you must use the same abstraction.
The distinction between `Observable` and `Flowable` gives you a hint, what kind of flow-control you should expect.

I believe that the compiler always beats the unit test, and the latter always beats documentation.
(You may not agree with the previous statement.)
For example, [`Flux.next()`](https://projectreactor.io/docs/core/release/api/reactor/core/publisher/Flux.html#next--): “*Emit only the first item emitted*” - according to the documentation.
What happens if `Flux` is empty?
Will I get an empty `Mono` or a `Mono` with `NoSuchElementException`?
Both are valid and sane behaviours… In RxJava 2 I have `firstElement()` returning `Maybe` and `firstOrError()` returning `Single`.
Quite straightforward, not to mention naming is less confusing.
`Flux.next()`, what does it even mean?

RxJava 2 also separated `Observable` and `Flowable` types.
If the source is inherently uncontrollable, we can express that in type-safe `Observable`.
Some operators make no sense or are impossible to implement on `Observable`.
That’s OK.
On the other hand `Flowable` has full backpressure support, meaning it can slow down.
I can easily convert from `Flowable` to `Observable`, converting the other way around requires me to think.
What should I do when the consumer cannot keep up with the producer, but the producer cannot be slowed down?
Drop extra messages?
Buffer them for a while?
In Reactor both types of streams are represented by `Flux` (like in RxJava 1.x) so you may always expect an error due to missing backpressure.
In RxJava 2 this became a little bit less common due to clear guarantees.

**+1 for RxJava**, for safer API.

# Checked exceptions

Reactor uses standard functional types from JDK, like [`Function`](https://docs.oracle.com/javase/8/docs/api/java/util/function/Function.html) in its API.
That’s great.
But a tiny side-effect of that choice is an awkward handling of checked exceptions inside transformations.
Consider the following code, that does **not** compile:

```java
Flux
    .just("java.math.BigDecimal", "java.time.Instant")
    .map(Class::forName)
```

`Class.forName()` throws checked `ClassNotFoundException`, unfortunately, you are not allowed to throw checked exceptions from `java.util.function.Function`.
In RxJava, on the other hand, [`io.reactivex.functions.Function`](http://reactivex.io/RxJava/javadoc/io/reactivex/functions/Function.html) is free from such constraints and the similar code would compile just fine.
Whether you like checked exceptions or not, once you have to deal with them, RxJava makes the experience more enjoyable.
**+1 for RxJava**, although I don’t consider this to be a major advantage.

# Testing

The presence of schedulers in both libraries not only allow fine-grained control of concurrency.
Schedulers also play an important role in unit testing.
In both Reactor and RxJava you can replace scheduler based on wall-clock with the one based on an artificial, virtual clock.
This is very handy when you are testing how your streams behave when time passes by.
Periodic events, timeouts, delays - all of these can be unit tested reliably.
So +1 to both?
Not really, Reactor goes one step further.
In RxJava you must externalize configuration of every single scheduler so that you can replace it in unit test.
Not bad per se, you should have them externalized anyway.
However, it quickly becomes messy when you need to pass [`TestScheduler`](http://reactivex.io/RxJava/javadoc/io/reactivex/schedulers/TestScheduler.html) to dozens of places in your production code.
In Reactor, on the other hand, it’s enough to surround code under test and all underlying schedulers are auto-magically replaced with virtual ones:

```java
StepVerifier
    .withVirtualTime(() ->
        Flux
            .never()
            .timeout(ofMillis(100))
    )
    .expectSubscription()
    .expectNoEvent(ofMillis(99))
    .thenAwait(ofMillis(1))
    .expectError(TimeoutException.class)
    .verify(ofSeconds(1));
```

This particular test makes sure timeout works as expected.
The test is very precise<sup>\*</sup> and 100% predictable.
There is no sleeping or busy-waiting for the result.
The advantage over RxJava is that non matter how complex your flow is, all schedulers are stubbed.
In RxJava you can write similar test, but you must make sure all schedulers in code under test are replace with `TestScheduler`.
Reactor conveniently injects virtual clock through all the layers.
**+1 for Reactor**

# Debugging

Reactor adds a wonderful debugging gem:

```java
Hooks.onOperatorDebug();
```

This tiny line placed at the beginning of your application will track how signals are flowing through your stream.
Let’s take a practical example.
Imagine the following stream:

```java
import reactor.core.publisher.Flux;
import reactor.core.publisher.Hooks;
import reactor.core.publisher.Mono;

import java.io.File;

public class StackTest {

    public static void main(String[] args) {

        Mono<Long> totalTxtSize = Flux
                .just("/tmp", "/home", "/404")
                .map(File::new)
                .concatMap(file -> Flux.just(file.listFiles()))
                .filter(File::isFile)
                .filter(file -> file.getName().endsWith(".txt"))
                .map(File::length)
                .reduce(0L, Math::addExact);


        totalTxtSize.subscribe(System.out::println);
    }

}
```

It finds all `.txt` files under `/tmp`, `/home` and `/404` directories and calculates the total size of all of them.
The program fails at runtime with cryptic, mile-long stack-trace:

```text
java.lang.NullPointerException
    at reactor.core.publisher.Flux.fromArray(Flux.java:953)
    at reactor.core.publisher.Flux.just(Flux.java:1161)
    at com.nurkiewicz.StackTest.lambda$main$0(StackTest.java:16)
    at reactor.core.publisher.FluxConcatMap$ConcatMapImmediate.drain(FluxConcatMap.java:368)
    at reactor.core.publisher.FluxConcatMap$ConcatMapImmediate.onNext(FluxConcatMap.java:244)
    at reactor.core.publisher.FluxMapFuseable$MapFuseableSubscriber.onNext(FluxMapFuseable.java:121)
    at reactor.core.publisher.FluxArray$ArraySubscription.slowPath(FluxArray.java:126)
    at reactor.core.publisher.FluxArray$ArraySubscription.request(FluxArray.java:99)
    at reactor.core.publisher.FluxMapFuseable$MapFuseableSubscriber.request(FluxMapFuseable.java:162)
    at reactor.core.publisher.FluxConcatMap$ConcatMapImmediate.onSubscribe(FluxConcatMap.java:229)
    at reactor.core.publisher.FluxMapFuseable$MapFuseableSubscriber.onSubscribe(FluxMapFuseable.java:90)
    at reactor.core.publisher.FluxArray.subscribe(FluxArray.java:53)
    at reactor.core.publisher.FluxArray.subscribe(FluxArray.java:59)
    at reactor.core.publisher.FluxMapFuseable.subscribe(FluxMapFuseable.java:63)
    at reactor.core.publisher.FluxConcatMap.subscribe(FluxConcatMap.java:121)
    at reactor.core.publisher.FluxFilter.subscribe(FluxFilter.java:49)
    at reactor.core.publisher.FluxFilter.subscribe(FluxFilter.java:53)
    at reactor.core.publisher.FluxMap.subscribe(FluxMap.java:62)
    at reactor.core.publisher.MonoReduceSeed.subscribe(MonoReduceSeed.java:65)
    at reactor.core.publisher.Mono.subscribe(Mono.java:3695)
    at reactor.core.publisher.Mono.subscribeWith(Mono.java:3801)
    at reactor.core.publisher.Mono.subscribe(Mono.java:3689)
    at reactor.core.publisher.Mono.subscribe(Mono.java:3656)
    at reactor.core.publisher.Mono.subscribe(Mono.java:3603)
    at com.nurkiewicz.StackTest.main(StackTest.java:23)
```

If you clean up the stack a little bit you may get a sense which operators saw the infamous `NullPointerException`:

```text
at ...Flux.fromArray()
at ...Flux.just()
at com.nurkiewicz.StackTest.lambda$main$0(StackTest.java:16)
   ...
at ...FluxArray.subscribe()
at ...FluxMapFuseable.subscribe()
at ...FluxConcatMap.subscribe()
at ...FluxFilter.subscribe()
at ...FluxFilter.subscribe()
at ...FluxMap.subscribe()
at ...MonoReduceSeed.subscribe()
   ...
at com.nurkiewicz.StackTest.main(StackTest.java:23)
```

But it doesn’t help much and most of the stack trace points to Reactor source code (you don’t want to go there).
It’s much more convenient to see where said operators are declared in our own code.
This is what `Hooks.onOperatorDebug()` shows next to the aforementioned stack trace:

```text
Assembly trace from producer [reactor.core.publisher.FluxConcatMap] :
  reactor.core.publisher.Flux.concatMap(Flux.java:3425)
  com.nurkiewicz.StackTest.main(StackTest.java:17)
Error has been observed by the following operator(s):
  |_  Flux.concatMap ⇢ com.nurkiewicz.StackTest.main(StackTest.java:17)
  |_  Flux.filter ⇢ com.nurkiewicz.StackTest.main(StackTest.java:18)
  |_  Flux.filter ⇢ com.nurkiewicz.StackTest.main(StackTest.java:19)
  |_  Flux.map ⇢ com.nurkiewicz.StackTest.main(StackTest.java:20)
  |_  Flux.reduce ⇢ com.nurkiewicz.StackTest.main(StackTest.java:21)
```

Paradoxically, we are not interested where the exception was thrown at runtime.
The answer is almost always: in the very guts of Reactor.
We much rather see how the faulty stream was constructed.
Reactor is unbeatable here.
Debugging reactive programs is hard, really hard.
This operator makes it a little bit easier.
By the way do you know what’s the source of `NullPointerException`?
From the [JavaDoc of `File.listFiles()`](https://docs.oracle.com/en/java/javase/11/docs/api/java.base/java/io/File.html#listFiles()):

*Returns null if \[…\] an I/O error occurs.*

Returns… null… if… error… occurs.
In the XXI century.

Never mind, clear **+1 for Reactor**.

# Spring support

You are free to use Reactor without Spring framework.
You can also use Spring framework without Reactor.
But it just so happens that they integrate very tightly and Spring WebFlux (mind the name) uses `Mono` and `Flux` extensively.
For example, you can return `Mono` directly from your controller and it behaves like good ’ol `DeferredResult`.
Once you place RxJava on your CLASSPATH, Spring integrates with it as well.
Both reactive web framework and reactive Spring Data.
However, why would you add another dependency if Reactor is already there?
It doesn’t seem like Spring discriminates RxJava in any way.
It’s just that Reactor seems more natural and built-in.
**+1 for Reactor**.

# Android development

RxJava is immensely popular among Android developers.
It solves two problems very cleanly:

- avoid callback hell by modelling UI events as streams
- easily switching back and forth between threads, especially making sure I/O doesn’t happen on UI thread

That’s one of the reasons why RxJava still targets older Java version.
This may change in the future but at the time of writing, RxJava is the only choice for Android developers.
And it’s a solid library so I don’t think they’ll miss much from Reactor.
**+1 for RxJava**

# Maturity

RxJava is much more mature and well established in the market (see: Android).
Also, there are many independent projects that chose RxJava as their API, for example, official [Couchbase driver](https://docs.couchbase.com/java-sdk/2.2/rxjava.html).
That was also the case for MongoDB, but they moved from RcJava driver to more general [reactive streams driver](http://mongodb.github.io/mongo-java-driver-reactivestreams/1.11/) that is compatible with both RxJava and Reactor.
The same applies to [RxNetty](https://github.com/ReactiveX/RxNetty) its younger brother [reactor-netty](https://github.com/reactor/reactor-netty).
The number of RxJava books also greatly exceeds the ones on Reactor.
So, for the time being, **+1 for RxJava**, but this will most likely change in the coming months.

# Summary

I didn’t anticipate that, but it turns out we have a tie.
However, looking forward, Reactor is definitely more promising.
Its [performance seems better](https://github.com/akarnokd/akarnokd-misc/issues/7), development is more active and backed by a bigger player (Pivotal).
These libraries are quite similar (at least from an API perspective) but if you get a choice, Reactor will probably serve you better.

<sup>\*</sup> for some reason this test fails when I change the `timeout(100)` to 98 or 101.
But still succeeds for 99 (?)
