---
layout: post
title: Server-sent events with RxJava and SseEmitter
date: '2015-07-29T23:59:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- sse
- CompletableFuture
- spring mvc
- multithreading
- spring
- rxjava
modified_time: '2015-11-29T23:39:16.738+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-7178811899129427795
blogger_orig_url: https://www.nurkiewicz.com/2015/07/server-sent-events-with-rxjava-and.html
---

Spring framework 4.2 GA is almost released, let's look at some new features it provides.
The one that got my attention is a simple new class [`SseEmitter`](http://docs.spring.io/spring-framework/docs/4.2.0.RC3/javadoc-api/org/springframework/web/servlet/mvc/method/annotation/SseEmitter.html) - an abstraction over [sever-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) easily used in Spring MVC controllers.
SSE is a technology that allows you to stream data from server to the browser within one HTTP connection in one direction.
It sounds like a subset of what [websockets](https://www.websocket.org/) can do.
However since it's a much simpler protocol, it may be used when full-duplex is not necessary, e.g. pushing stock price changes in real-time or showing progress of long-running process.
This is going to be our example.

Imagine we have a virtual coin miner with the following API:

```java
public interface CoinMiner {

    BigDecimal mine() {
        //...
    }
}
```

Every time we call `mine()` we have to wait few seconds and we get around 1 coin in return (on average).
If we want to mine multiple coins, we have to call this method multiple times:

```java
@RestController
public class MiningController {

    //...

    @RequestMapping("/mine/{count}")
    void mine(@PathVariable int count) {
        IntStream
                .range(0, count)
                .forEach(x -> coinMiner.mine());
    }

}
```

This works, we can request `/mine/10` and `mine()` method will be executed 10 times.
So far so good.
But mining is a CPU intensive task, it would be beneficial to spread computations over multiple cores.
Additionally even with parallelization our API endpoint is quite slow and we have to patiently wait until all work is done without any progress notifications.
Let's fix parallelism first - however since parallel streams give you no control over underlying thread pool, let's go for explicit `ExecutorService`:

```java
@Component
class CoinMiner {

    CompletableFuture<BigDecimal> mineAsync(ExecutorService executorService) {
        return CompletableFuture.supplyAsync(this::mine, executorService);
    }

    //...

}
```

Client code must supply `ExecutorService` explicitly (just a design choice):

```java
@RequestMapping("/mine/{count}")
void mine(@PathVariable int count) {
    final List<CompletableFuture<BigDecimal>> futures = IntStream
            .range(0, count)
            .mapToObj(x -> coinMiner.mineAsync(executorService))
            .collect(toList());
    futures.forEach(CompletableFuture::join);
}
```

It's insanely important to first call `mineAsync` multiple times and then (as a second stage) wait for all futures to complete with `join`.
It's tempting to write:

```java
IntStream
        .range(0, count)
        .mapToObj(x -> coinMiner.mineAsync(executorService))
        .forEach(CompletableFuture::join);
```

However due to lazy nature of streams in Java 8, that tasks will be executed sequentially!
If you don't grok laziness of streams yet, always read them from bottom to top: we ask to `join` some future so stream goes up and calls `mineAsync()` just once (lazy!), passing it to `join()`.
When this `join()` finishes, it goes up again asking for another `Future`.
By using `collect()` we force all `mineAsync()` executions, starting all asynchronous computations.
Later on we wait for each and every one of them.

# Introducing `SseEmitter`

Now it's time to be more reactive (there, I said it).
Controller can return an instance of `SseEmitter`.
Once we `return` from a handler method, container thread is released and can serve more upcoming requests.
But the connection is not closed and the client keeps waiting!
What we should do is keep a reference of `SseEmitter` instance and call its `send()` and `complete` methods later, from a different thread.
For example we can start a long-running process and keep `send()`-ing progress from arbitrary threads.
Once the process is done, we `complete()` the `SseEmitter` and finally the HTTP connection is closed (at least logically, remember about `Keep-alive`).
In example below we have a bunch of `CompletableFuture`s and when each completes, we simply send `1` to the client (`notifyProgress()`).
When all futures are done we complete the stream (`thenRun(sseEmitter::complete)`), closing the connection:

```java
@RequestMapping("/mine/{count}")
SseEmitter mine(@PathVariable int count) {
    final SseEmitter sseEmitter = new SseEmitter();
    final List<CompletableFuture<BigDecimal>> futures = mineAsync(count);
    futures.forEach(future ->
            future.thenRun(() -> notifyProgress(sseEmitter)));

    final CompletableFuture[] futuresArr = futures.toArray(new CompletableFuture[futures.size()]);
    CompletableFuture
            .allOf(futuresArr)
            .thenRun(sseEmitter::complete);

    return sseEmitter;
}

private void notifyProgress(SseEmitter sseEmitter) {
    try {
        sseEmitter.send(1);
    } catch (IOException e) {
        throw new RuntimeException(e);
    }
}

private List<CompletableFuture<BigDecimal>> mineAsync(@PathVariable int count) {
    return IntStream
            .range(0, count)
            .mapToObj(x -> coinMiner.mineAsync(executorService))
            .collect(toList());
}
```

Calling this method results with the following response (notice `Content-Type`):

```java
< HTTP/1.1 200 OK
< Content-Type: text/event-stream;charset=UTF-8
< Transfer-Encoding: chunked
< 
data:1

data:1

data:1

data:1

* Connection #0 to host localhost left intact
```

We will learn later how to interpret such response on the client side.
For the time being let's clean up the design a little bit.

# Introducing RxJava with `Observable` progress

Code above works, but looks quite messy.
What we actually have is a series of events, each representing progress of computation.
Computation finally finishes, so the stream should also signal end.
Sounds exactly like `Observable`!
We start by refactoring `CoinMiner` in order to return `Observable<BigDecimal`:

```java
Observable<BigDecimal> mineMany(int count, ExecutorService executorService) {
    final ReplaySubject<BigDecimal> subject = ReplaySubject.create();
    final List<CompletableFuture<BigDecimal>> futures = IntStream
            .range(0, count)
            .mapToObj(x -> mineAsync(executorService))
            .collect(toList());
    futures
            .forEach(future ->
                    future.thenRun(() -> subject.onNext(BigDecimal.ONE)));

    final CompletableFuture[] futuresArr = futures.toArray(new CompletableFuture[futures.size()]);
    CompletableFuture
            .allOf(futuresArr)
            .thenRun(subject::onCompleted);

    return subject;
}
```

Every time an event appears in `Observable` returned from `mineMany()`, we just mined that many coins.
When all futures are done, we complete the stream as well.
This doesn't look much better yet on the implementation side, but look how clean it is from the controller's perspective:

```java
@RequestMapping("/mine/{count}")
SseEmitter mine(@PathVariable int count) {
    final SseEmitter sseEmitter = new SseEmitter();
    coinMiner
            .mineMany(count, executorService)
            .subscribe(
                    value -> notifyProgress(sseEmitter),
                    sseEmitter::completeWithError,
                    sseEmitter::complete
            );
    return sseEmitter;
}
```

After calling `coinMiner.mineMany()` we simply subscribe to events.
Turns out `Observable` and `SseEmitter` methods match 1:1.
What happens here is pretty self-explanatory: start asynchronous computation and every time the background computation signals any progress, forward it to the client.
OK, let's go back to the implementation.
It looks messy because we mix `CompletableFuture` and `Observable`.
I already described how to [convert `CompletableFuture` into an `Observable` with just one element](http://www.nurkiewicz.com/2014/11/converting-between-completablefuture.html).
Here is a recap, including `rx.Single` abstraction found since RxJava 1.0.13 (not used here):

```java
public class Futures {

    public static <T> Observable<T> toObservable(CompletableFuture<T> future) {
        return Observable.create(subscriber ->
                future.whenComplete((result, error) -> {
                    if (error != null) {
                        subscriber.onError(error);
                    } else {
                        subscriber.onNext(result);
                        subscriber.onCompleted();
                    }
                }));
    }

    public static <T> Single<T> toSingle(CompletableFuture<T> future) {
        return Single.create(subscriber ->
                future.whenComplete((result, error) -> {
                    if (error != null) {
                        subscriber.onError(error);
                    } else {
                        subscriber.onSuccess(result);
                    }
                }));
    }

}
```

Having these utility operators somewhere we can improve implementation and avoid mixing two APIs:

```java
Observable<BigDecimal> mineMany(int count, ExecutorService executorService) {
    final List<Observable<BigDecimal>> observables = IntStream
            .range(0, count)
            .mapToObj(x -> mineAsync(executorService))
            .collect(toList());
    return Observable.merge(observables);
}

Observable<BigDecimal> mineAsync(ExecutorService executorService) {
    final CompletableFuture<BigDecimal> future = 
         CompletableFuture.supplyAsync(this::mine, executorService);
    return Futures.toObservable(future);
}
```

RxJava has a built-in operator for merging multiple `Observable`s into one, it doesn't matter that each of our underlying `Observable`s emit just one event.

# Deep-dive into RxJava operators

Let's use the power of RxJava to improve our streaming a little bit.

## `scan()`

Currently every time we mine one coin, we `send(1)` event to the client.
This means that every client has to track how many coins it already received in order to calculate total calculated amount.
Would be nice if server was always sending total amount rather than deltas.
However we don't want to change the implementation.
Turns out it's pretty straightforward with `Observable.scan()` operator:

```java
@RequestMapping("/mine/{count}")
SseEmitter mine(@PathVariable int count) {
    final SseEmitter sseEmitter = new SseEmitter();
    coinMiner
            .mineMany(count, executorService)
            .scan(BigDecimal::add)
            .subscribe(
                    value -> notifyProgress(sseEmitter, value),
                    sseEmitter::completeWithError,
                    sseEmitter::complete
            );
    return sseEmitter;
}

private void notifyProgress(SseEmitter sseEmitter, BigDecimal value) {
    try {
        sseEmitter.send(value);
    } catch (IOException e) {
        e.printStackTrace();
    }
}
```

`scan()` operator takes previous event and current one, combing them together.
By applying `BigDecimal::add` we simply add all numbers.
E.g. 1, 1 + 1, (1 + 1) + 1, and so on.
`scan()` is like `flatMap()`, but keeps intermediate values.

## Sampling with `sample()`

It might be the case that our back-end service produces way too many progress updates then we can consume.
We don't want to flood client with irrelevant updates and saturate bandwidth.
Sending an update at most twice a second sounds reasonable.
Luckily RxJava has a built-in operator for that as well:

```java
Observable<BigDecimal> obs = coinMiner.mineMany(count, executorService);
obs
        .scan(BigDecimal::add)
        .sample(500, TimeUnit.MILLISECONDS)
        .subscribe(
            //...
        );
```

`sample()` will periodically look at the underlying stream and emit the most recent item only, discarding intermediate ones.
Fortunately we aggregate items on-the-fly with `scan()` so we don't loose any updates.

## `window()` - constant emit intervals

There is one catch though.
`sample()` will not emit the same item twice if nothing new appeared within selected 500 milliseconds.
It's fine, but remember we are pushing these updates over the TCP/IP connection.
It's a good idea to periodically send an update to the client, even if nothing happened in the meantime - just to keep the connection alive, sort of a `ping`.
There are probably many ways of achieving this requirement, e.g. involving `timeout()` operator.
I chose grouping all events every 500 ms using `window()` operator:

```java
Observable<BigDecimal> obs = coinMiner.mineMany(count, executorService);
obs
        .window(500, TimeUnit.MILLISECONDS)
        .flatMap(window -> window.reduce(BigDecimal.ZERO, BigDecimal::add))
        .scan(BigDecimal::add)
        .subscribe(
            //...
        );
```

This one is tricky.
First we group all progress updates in 500 millisecond windows.
Then we calculate total (similar to `scan()`) of coins mined within this time period using `reduce`.
If no coins were mined in that period, we simply return `ZERO`.
We use `scan()` in the end to aggregate sub-totals of every window.
We no longer need `sample()` since `window()` makes sure an event is emitted every 500 ms.

# Client-side

There is a lot of examples of SSE usage in JavaScript, so just to give you a quick solution calling our controller:

```javascript
var source = new EventSource("/mine/10");
source.onmessage = function (event) {
    console.info(event);
};
```

I believe `SseEmitter` is a major improvement in Spring MVC, which will allow us to write more robust and faster web applications requiring instant one-directional updates.
