---
layout: post
title: Thread pool self-induced deadlocks
date: '2018-09-10T08:10:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- deadlock
- reactor
- concurrency
modified_time: '2018-09-10T08:11:11.975+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-6291934536059331561
blogger_orig_url: https://www.nurkiewicz.com/2018/09/thread-pool-self-induced-deadlocks.html
image: /assets/img/thread-pool-self-induced-deadlocks/hero.jpg
---

### Summary

- Deadlocks are caused by many threads locking the same resources
- Deadlocks can also occur if thread pool is used inside a task running in that pool
- Modern libraries like RxJava/Reactor are also susceptible

A deadlock is a situation where two or more threads are waiting for resources acquired by each other.
For example thread A waits for `lock1` locked by thread B, whereas thread B waits for `lock2`, locked by thread A.
In worst case scenario, the application freezes for an indefinite amount of time.
Let me show you a concrete example.
Imagine there is a `Lumberjack` class that holds references to two accessory locks:

```java
import com.google.common.collect.ImmutableList;
import lombok.RequiredArgsConstructor;

import java.util.concurrent.locks.Lock;

@RequiredArgsConstructor
class Lumberjack {

    private final String name;
    private final Lock accessoryOne;
    private final Lock accessoryTwo;

    void cut(Runnable work) {
        try {
            accessoryOne.lock();
            try {
                accessoryTwo.lock();
                work.run();
            } finally {
                accessoryTwo.unlock();
            }
        } finally {
            accessoryOne.unlock();
        }
    }
}
```

Every lumberjack needs two accessories: a *helmet* and a *chainsaw*.
Before he approaches any `work`, he must hold exclusive lock to both of these.
We create lumberjacks as follows:

```java
import lombok.RequiredArgsConstructor;

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

@RequiredArgsConstructor
class Logging {

    private final Names names;

    private final Lock helmet = new ReentrantLock();
    private final Lock chainsaw = new ReentrantLock();

    Lumberjack careful() {
        return new Lumberjack(names.getRandomName(), helmet, chainsaw);
    }

    Lumberjack yolo() {
        return new Lumberjack(names.getRandomName(), chainsaw, helmet);
    }

}
```

As you can see there are two kinds of lumberjacks: those who first take a helmet and then a chainsaw and vice versa.
Careful lumberjacks try to obtain a helmet first and then wait for a chainsaw.
YOLO-type of lumberjacks first take a chainsaw and then look for a helmet.
Let’s generate some lumberjacks and run them concurrently:

```java
private List<Lumberjack> generate(int count, Supplier<Lumberjack> factory) {
    return IntStream
            .range(0, count)
            .mapToObj(x -> factory.get())
            .collect(toList());
}
```

`generate()` is a simple method that creates a collection of lumberjacks of a given type.
Then we generate a bunch of careful and yolo lumberjacks:

```java
private final Logging logging;

//...

List<Lumberjack> lumberjacks = new CopyOnWriteArrayList<>();
lumberjacks.addAll(generate(carefulLumberjacks, logging::careful));
lumberjacks.addAll(generate(yoloLumberjacks, logging::yolo));
```

Finally let’s put these lumberjacks to work:

```java
IntStream
        .range(0, howManyTrees)
        .forEach(x -> {
            Lumberjack roundRobinJack = lumberjacks.get(x % lumberjacks.size());
            pool.submit(() -> {
                log.debug("{} cuts down tree, {} left", roundRobinJack, latch.getCount());
                roundRobinJack.cut(/* ... */);
            });
        });
```

This loop takes lumberjacks one after another in a round-robin fashion and asks them to cut a tree.
Essentially we are submitting `howManyTrees` number of tasks to a thread `pool` (`ExecutorService`).
In order to figure out when the job was done we use a `CountDownLatch`:

```java
CountDownLatch latch = new CountDownLatch(howManyTrees);
IntStream
        .range(0, howManyTrees)
        .forEach(x -> {
            pool.submit(() -> {
                //...
                roundRobinJack.cut(latch::countDown);
            });
        });
if (!latch.await(10, TimeUnit.SECONDS)) {
    throw new TimeoutException("Cutting forest for too long");
}
```

The idea is simple - let a bunch of lumberjacks compete over a helmet and a chainsaw across multiple threads.
The complete source code follows:

```java
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.function.Supplier;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

@RequiredArgsConstructor
class Forest implements AutoCloseable {
    private static final Logger log = LoggerFactory.getLogger(Forest.class);

    private final ExecutorService pool;
    private final Logging logging;

    void cutTrees(int howManyTrees, int carefulLumberjacks, int yoloLumberjacks) throws InterruptedException, TimeoutException {
        CountDownLatch latch = new CountDownLatch(howManyTrees);
        List<Lumberjack> lumberjacks = new ArrayList<>();
        lumberjacks.addAll(generate(carefulLumberjacks, logging::careful));
        lumberjacks.addAll(generate(yoloLumberjacks, logging::yolo));
        IntStream
                .range(0, howManyTrees)
                .forEach(x -> {
                    Lumberjack roundRobinJack = lumberjacks.get(x % lumberjacks.size());
                    pool.submit(() -> {
                        log.debug("{} cuts down tree, {} left", roundRobinJack, latch.getCount());
                        roundRobinJack.cut(latch::countDown);
                    });
                });
        if (!latch.await(10, TimeUnit.SECONDS)) {
            throw new TimeoutException("Cutting forest for too long");
        }
        log.debug("Cut all trees");
    }

    private List<Lumberjack> generate(int count, Supplier<Lumberjack> factory) {
        return IntStream
                .range(0, count)
                .mapToObj(x -> factory.get())
                .collect(Collectors.toList());
    }

    @Override
    public void close() {
        pool.shutdownNow();
    }
}
```

Now the interesting part.
If you only create `careful` lumberjacks, the application completes almost immediately, e.g.:

```java
ExecutorService pool = Executors.newFixedThreadPool(10);
Logging logging = new Logging(new Names());
try (Forest forest = new Forest(pool, logging)) {
    forest.cutTrees(10_000, 10, 0);
} catch (TimeoutException e) {
    log.warn("Working for too long", e);
}
```

However, if you play a bit with the number of lumberjacks, e.g. 10 careful and one yolo, the system quite often fails.
What happened?
Everyone in the careful team tries to pick up a helmet first.
If one of the lumberjacks picked up a helmet, everyone else just waits.
Then the lucky guy picks up a chainsaw, which must be available.
Why?
Everyone else is waiting for the helmet before they pick up a chainsaw.
So far so good.
But what if there is one yolo lumberjack in the team?
While everyone competes for a helmet, he sneakily grabs a chainsaw.
But there’s a problem.
One of the careful lumberjacks gets his safety helmet.
However, he can’t pick up a chainsaw, because it’s already taken by someone else.
To make matters worse, the current owner of the chainsaw (the yolo guy) will not release his chainsaw until he gets a helmet.
There are no timeouts here.
Careful guy waits infinitely with his helmet, unable to get a chainsaw.
The yolo guy sits idle forever because he can not obtain a helmet.
A deadlock.

Now, what would happen if all lumberjacks were yolo, i.e. they all tried to pick the chainsaw first?
Turns out the easiest way to avoid deadlocks is to obtain and release locks always in the same order.
For example, you can sort your resources based on some arbitrary criteria.
If one thread obtains lock A followed B, whereas the second thread obtains B first, it’s a recipe for a deadlock.

# Thread pool self-induced deadlocks

This was an example of a deadlock, rather simple one.
But it turns out a single thread pool can cause a deadlock when used incorrectly.
Imagine you have an `ExecutorService` (just like in the previous example) that you use like so:

```java
ExecutorService pool = Executors.newFixedThreadPool(10);
pool.submit(() -> {
    try {
        log.info("First");
        pool.submit(() -> log.info("Second")).get();
        log.info("Third");
    } catch (InterruptedException | ExecutionException e) {
        log.error("Error", e);
    }
});
```

This looks fine, all messages appear on the screen as expected:

```text
INFO [pool-1-thread-1]: First
INFO [pool-1-thread-2]: Second
INFO [pool-1-thread-1]: Third
```

Notice that we block (see `get()`) waiting for the inner `Runnable` to complete before we display `"Third"`.
It’s a trap!
Waiting for the inner task to complete means it must acquire a thread from a thread `pool` in order to proceed.
However we already acquired one thread, therefore inner will block until it can get the second.
Our thread pool is large enough at the moment, so it works fine.
Let’s change our code a little bit, shrinking the thread pool to just one thread.
Also, we’ll remove `get()`, which is crucial:

```java
ExecutorService pool = Executors.newSingleThreadExecutor();
pool.submit(() -> {
    log.info("First");
    pool.submit(() -> log.info("Second"));
    log.info("Third");
});
```

Code works fine, but with a twist:

```text
INFO [pool-1-thread-1]: First
INFO [pool-1-thread-1]: Third
INFO [pool-1-thread-1]: Second
```

Two things to notice:

- everything runs in a single thread (unsurprisingly)
- the `"Third"` message appears before `"Second"`

Change of order is entirely predictable and does not come from some race condition between threads (in fact, we have just one).
Watch closely what happens: we submit a new task to a thread pool (the one printing `"Second"`).
However, this time we don’t wait for the completion of that task.
Great, because the very single thread in a thread pool is already occupied by the task printing `"First"` and `"Third"`.
Therefore the outer task continues, printing `"Second"`.
When this task finishes, it releases the single thread back to a thread pool.
Inner task can finally begin execution, printing `"Second"`.
Now where’s the deadlock?
Try adding blocking `get()` to inner task:

```java
ExecutorService pool = Executors.newSingleThreadExecutor();
pool.submit(() -> {
    try {
        log.info("First");
        pool.submit(() -> log.info("Second")).get();
        log.info("Third");
    } catch (InterruptedException | ExecutionException e) {
        log.error("Error", e);
    }
});
```

Deadlock!
Step by step:

- Task printing `"First"` is submitted to an idle single-threaded pool
- This task begins execution and prints `"First"`
- We submit an inner task printing `"Second"` to a thread pool
- The inner task lands in a pending task queue - no threads are available since the only one is currently being occupied
- We block waiting for the result of the inner task.
  Unfortunately while waiting for the inner task we hold the only available thread
- `get()` will wait forever, unable to acquire thread
- deadlock

Does it mean having a single-thread pool is bad?
Not really.
The same problem could occur with a thread pool of any size.
But in that case a deadlock may occur only under high load, which is much worse from a maintenance perspective.
You could technically have an unbounded thread pool, but that’s even worse.

# Reactor/RxJava

Notice that this problem can occur with higher-level libraries like Reactor:

```java
Scheduler pool = Schedulers.fromExecutor(Executors.newFixedThreadPool(10));
Mono
    .fromRunnable(() -> {
        log.info("First");
        Mono
                .fromRunnable(() -> log.info("Second"))
                .subscribeOn(pool)
                .block();  //VERY, VERY BAD!
        log.info("Third");
    })
    .subscribeOn(pool);
```

Once you subscribe, this seems to work, but is terribly non-idiomatic.
The basic problem is the same.
Outer `Runnable` acquires one thread from a `pool` (`subscribeOn()` in the last line) and at the same time inner `Runnable` tries to obtain thread as well.
Replace underlying thread pool with single-thread pool and this produces a deadlock.
At least with RxJava/Reactor the cure is simple - just compose asynchronous operations rather than blocking inside each other:

```java
Mono
    .fromRunnable(() -> {
        log.info("First");
        log.info("Third");
    })
    .then(Mono
            .fromRunnable(() -> log.info("Second"))
            .subscribeOn(pool))
    .subscribeOn(pool)
```

# Prevention

There is no 100% way of preventing deadlocks.
One technique is to avoid situations that may lead to deadlocks like sharing resources or locking exclusively.
If that’s not possible (or deadlocks are not obvious, like with thread pools), consider proper code hygiene.
Monitor thread pools and avoid blocking indefinitely.
I can hardly imagine a situation when you are willing to wait an indefinite amount of time for a completion.
And that’s how `get()` or `block()` without timeout are working.
