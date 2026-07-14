---
layout: post
title: Converting between Completablefuture and Observable
date: '2014-11-24T22:39:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- CompletableFuture
- java 8
- rxjava
modified_time: '2015-11-29T23:38:06.730+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5439683187518411638
blogger_orig_url: https://www.nurkiewicz.com/2014/11/converting-between-completablefuture.html
---

[`CompletableFuture<T>` from Java 8](http://www.nurkiewicz.com/2013/05/java-8-definitive-guide-to.html) is an advanced abstraction over a promise that value of type `T` will be available in the *future*.
[`Observable<T>`](https://github.com/ReactiveX/RxJava/wiki/Observable) is quite similar, but it promises arbitrary number of items in the future, from 0 to infinity.
These two representations of asynchronous results are quite similar to the point where `Observable` with just one item can be used instead of `CompletableFuture` and vice-versa.
On the other hand `CompletableFuture` is more specialized and because it's now part of JDK, should become prevalent quite soon.
Let's celebrate RxJava 1.0 release with a short article showing how to convert between the two, without loosing asynchronous and event-driven nature of them.

# From `CompletableFuture<T>` to `Observable<T>`

`CompletableFuture` represents one value in the future, so turning it into `Observable` is rather simple.
When `Future` completes with some value, `Observable` will emit that value as well immediately and close stream:

```groovy
class FuturesTest extends Specification {

    public static final String MSG = "Don't panic"

    def 'should convert completed Future to completed Observable'() {
        given:
            CompletableFuture<String> future = CompletableFuture.completedFuture("Abc")

        when:
            Observable<String> observable = Futures.toObservable(future)

        then:
            observable.toBlocking().toIterable().toList() == ["Abc"]
    }

    def 'should convert failed Future into Observable with failure'() {
        given:
            CompletableFuture<String> future = failedFuture(new IllegalStateException(MSG))

        when:
            Observable<String> observable = Futures.toObservable(future)

        then:
            observable
                    .onErrorReturn({ th -> th.message } as Func1)
                    .toBlocking()
                    .toIterable()
                    .toList() == [MSG]
    }  

    CompletableFuture failedFuture(Exception error) {
        CompletableFuture future = new CompletableFuture()
        future.completeExceptionally(error)
        return future
    }

}
```

First test of *not-yet-implemented* `Futures.toObservable()` converts `Future` into `Observable` and makes sure value is propagated correctly.
Second test created failed `Future`, replaces failure with exception's message and makes sure exception was propagated.
The implementation is much shorter:

```java
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
```

NB: [`Observable.fromFuture()`](https://github.com/ReactiveX/RxJava/wiki/Phantom-Operators#fromfuture) exists, however we want to take full advantage of `ComplatableFuture`'s asynchronous operators.

# From `Observable<T>` to `CompletableFuture<List<T>>`

There are actually two ways to convert `Observable` to `Future` - creating `CompletableFuture<List<T>>` or `CompletableFuture<T>` (if we assume `Observable` has just one item).
Let's start from the former case, described with the following test cases:

```groovy
def 'should convert Observable with many items to Future of list'() {
    given:
        Observable<Integer> observable = Observable.just(1, 2, 3)

    when:
        CompletableFuture<List<Integer>> future = Futures.fromObservable(observable)

    then:
        future.get() == [1, 2, 3]
}

def 'should return failed Future when after few items exception was emitted'() {
    given:
        Observable<Integer> observable = Observable.just(1, 2, 3)
                .concatWith(Observable.error(new IllegalStateException(MSG)))

    when:
        Futures.fromObservable(observable)

    then:
        def e = thrown(Exception)
        e.message == MSG
}
```

Obviously `Future` doesn't complete until source `Observable` signals end of stream.
Thus `Observable.never()` would never complete wrapping `Future`, rather then completing it with empty list.
The implementation is much shorter and sweeter:

```java
public static <T> CompletableFuture<List<T>> fromObservable(Observable<T> observable) {
    final CompletableFuture<List<T>> future = new CompletableFuture<>();
    observable
            .doOnError(future::completeExceptionally)
            .toList()
            .forEach(future::complete);
    return future;
}
```

The key is `Observable.toList()` that conveniently converts from `Observable<T>` and `Observable<List<T>>`.
The latter emits one item of `List<T>` type when source `Observable<T>` finishes.

# From `Observable<T>` to `CompletableFuture<T>`

Special case of the previous transformation happens when we know that `CompletableFuture<T>` will return exactly one item.
In that case we can convert it directly to `CompletableFuture<T>`, rather than `CompletableFuture<List<T>>` with one item only.
Tests first:

```groovy
def 'should convert Observable with single item to Future'() {
    given:
        Observable<Integer> observable = Observable.just(1)

    when:
        CompletableFuture<Integer> future = Futures.fromSingleObservable(observable)

    then:
        future.get() == 1
}

def 'should create failed Future when Observable fails'() {
    given:
        Observable<String> observable = Observable.<String> error(new IllegalStateException(MSG))

    when:
        Futures.fromSingleObservable(observable)

    then:
        def e = thrown(Exception)
        e.message == MSG
}

def 'should fail when single Observable produces too many items'() {
    given:
        Observable<Integer> observable = Observable.just(1, 2)

    when:
        Futures.fromSingleObservable(observable)

    then:
        def e = thrown(Exception)
        e.message.contains("too many elements")
}
```

Again the implementation is quite straightforward and almost identical:

```java
public static <T> CompletableFuture<T> fromSingleObservable(Observable<T> observable) {
    final CompletableFuture<T> future = new CompletableFuture<>();
    observable
        .doOnError(future::completeExceptionally)
        .single()
        .forEach(future::complete);
    return future;
}
```

Helpers methods above aren't fully robust yet, but if you ever need to convert between JDK 8 and RxJava style of asynchronous computing, this article should be enough to get you started.
