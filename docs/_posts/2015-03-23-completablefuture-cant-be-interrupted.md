---
layout: post
title: CompletableFuture can't be interrupted
date: '2015-03-23T19:10:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- CompletableFuture
- java 8
- concurrency
modified_time: '2015-11-29T23:37:49.463+01:00'
thumbnail: /assets/img/completablefuture-cant-be-interrupted/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1434818069057087430
blogger_orig_url: https://www.nurkiewicz.com/2015/03/completablefuture-cant-be-interrupted.html
---

I wrote a lot about [*InterruptedException and interrupting threads*](http://www.nurkiewicz.com/2014/05/interruptedexception-and-interrupting.html) already.
In short if you call `Future.cancel()` not inly given `Future` will terminate pending `get()`, but also it will try to interrupt underlying thread.
This is a pretty important feature that enables better thread pool utilization.
I also wrote to always prefer [*`CompletableFuture` over standard `Future`*](http://www.nurkiewicz.com/2014/11/executorservice-10-tips-and-tricks.html).
It turns out the more powerful younger brother of `Future` doesn't handle `cancel()` so elegantly.
Consider the following task, which we'll use later throughout the tests:

```java
class InterruptibleTask implements Runnable {

    private final CountDownLatch started = new CountDownLatch(1)
    private final CountDownLatch interrupted = new CountDownLatch(1)

    @Override
    void run() {
        started.countDown()
        try {
            Thread.sleep(10_000)
        } catch (InterruptedException ignored) {
            interrupted.countDown()
        }
    }

    void blockUntilStarted() {
        started.await()
    }

    void blockUntilInterrupted() {
        assert interrupted.await(1, TimeUnit.SECONDS)
    }

}
```

Client threads can examine `InterruptibleTask` to see whether it has started or was interrupted.
First let's see how `InterruptibleTask` reacts to `cancel()` from outside:

```java
def "Future is cancelled without exception"() {
    given:
        def task = new InterruptibleTask()
        def future = myThreadPool.submit(task)
        task.blockUntilStarted()
    and:
        future.cancel(true)
    when:
        future.get()
    then:
        thrown(CancellationException)
}

def "CompletableFuture is cancelled via CancellationException"() {
    given:
        def task = new InterruptibleTask()
        def future = CompletableFuture.supplyAsync({task.run()} as Supplier, myThreadPool)
        task.blockUntilStarted()
    and:
        future.cancel(true)
    when:
        future.get()
    then:
        thrown(CancellationException)
}
```

So far so good.
Clearly both `Future` and `CompletableFuture` work pretty much the same way - retrieving result after it was canceled throws `CancellationException`.
But what about thread in `myThreadPool`?
I thought it will be interrupted and thus recycled by the pool, how wrong was I!

```java
def "should cancel Future"() {
    given:
        def task = new InterruptibleTask()
        def future = myThreadPool.submit(task)
        task.blockUntilStarted()
    when:
        future.cancel(true)
    then:
        task.blockUntilInterrupted()
}

@Ignore("Fails with CompletableFuture")
def "should cancel CompletableFuture"() {
    given:
        def task = new InterruptibleTask()
        def future = CompletableFuture.supplyAsync({task.run()} as Supplier, myThreadPool)
        task.blockUntilStarted()
    when:
        future.cancel(true)
    then:
        task.blockUntilInterrupted()
}
```

First test submits ordinary `Runnable` to `ExecutorService` and waits until it's started.
Later we cancel `Future` and wait until `InterruptedException` is observed.
`blockUntilInterrupted()` will return when underlying thread is interrupted.
Second test, however, fails.
`CompletableFuture.cancel()` will never interrupt underlying thread, so despite `Future` looking as if it was cancelled, backing thread is still running and no `InterruptedException` is thrown from `sleep()`.
Bug or a feature?
[It's documented](http://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CompletableFuture.html#cancel-boolean-), so unfortunately a feature:

> **Parameters:**`mayInterruptIfRunning` - this value has no effect in this implementation because interrupts are not used to control processing.

RTFM, you say, but why `CompletableFuture` works this way?
First let's examine how "old" `Future` implementations differ from `CompletableFuture`.
`FutureTask`, returned from `ExecutorService.submit()` has the following `cancel()` implementation (I removed `Unsafe` with similar non-thread safe Java code, so treat it as pseudo code only):

```java
public boolean cancel(boolean mayInterruptIfRunning) {
    if (state != NEW)
        return false;
    state = mayInterruptIfRunning ? INTERRUPTING : CANCELLED;
    try {
        if (mayInterruptIfRunning) {
            try {
                Thread t = runner;
                if (t != null)
                    t.interrupt();
            } finally { // final state
                state = INTERRUPTED;
            }
        }
    } finally {
        finishCompletion();
    }
    return true;
}
```

`FutureTask` has a `state` variable that follows this state diagram:

[![](/assets/img/completablefuture-cant-be-interrupted/1.png)](/assets/img/completablefuture-cant-be-interrupted/1.png)

In case of `cancel()` we can either enter `CANCELLED` state or go to `INTERRUPTED` through `INTERRUPTING`.
The core part is where we take `runner` thread (if exists, i.e. if task is currently being executed) and we try to interrupt it.
This branch takes care of eager and forced interruption of already running thread.
In the end we must notify all threads blocked on `Future.get()` in `finishCompletion()` (irrelevant here).
So it's pretty obvious how old `Future` cancels already running tasks.
What about `CompletableFuture`?
Pseudo-code of `cancel()`:

```java
public boolean cancel(boolean mayInterruptIfRunning) {
    boolean cancelled = false;
    if (result == null) {
        result = new AltResult(new CancellationException());
        cancelled = true;
    }
    postComplete();
    return cancelled || isCancelled();
}
```

Quite disappointing, we barely set `result` to `CancellationException`, ignoring `mayInterruptIfRunning` flag.
`postComplete()` has a similar role to `finishCompletion()` - notifies all pending callbacks registered on that future.
Its implementation is rather unpleasant (using non-blocking [Treiber stack](http://people.csail.mit.edu/shanir/publications/Lock_Free.pdf)) but it definitely doesn't interrupt any underlying thread.

# Reasons and implications

Limited `cancel()` in case of `CompletableFuture` is not a bug, but a design decision.
`CompletableFuture` is not inherently bound to any thread, while `Future` almost always represents background task.
It's perfectly fine to create `CompletableFuture` from scratch (`new CompletableFuture<>()`) where there is simply no underlying thread to cancel.
Still I can't help the feeling that majority of `CompletableFuture`s *will* have an associated task and background thread.
In that case malfunctioning `cancel()` is a potential problem.
I no longer advice blindly replacing `Future` with `CompletableFuture` as it might change the behavior of applications relying on `cancel()`.
This means `CompletableFuture` intentionally breaks [Liskov substitution principle](http://en.wikipedia.org/wiki/Liskov_substitution_principle) - and this is a serious implication to consider.
