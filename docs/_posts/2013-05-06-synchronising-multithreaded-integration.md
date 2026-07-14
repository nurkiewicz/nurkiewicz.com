---
layout: post
title: Synchronising Multithreaded Integration Tests revisited
date: '2013-05-06T19:27:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- testing
- multithreading
- java 8
- intellij idea
modified_time: '2013-05-06T19:27:58.480+02:00'
thumbnail: /assets/img/synchronising-multithreaded-integration/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-476020086705871356
blogger_orig_url: https://www.nurkiewicz.com/2013/05/synchronising-multithreaded-integration.html
---

I recently stumbled upon an article [*Synchronising Multithreaded Integration Tests*](http://www.captaindebug.com/2013/02/synchronising-multithreaded-integration.html) on [Captain Debug's Blog](http://www.captaindebug.com/).
That post emphasizes the problem of designing integration tests involving class under test running business logic asynchronously.
This contrived example was given (I stripped some comments):

```java
public class ThreadWrapper {

    public void doWork() {

        Thread thread = new Thread() {
            @Override
            public void run() {

                System.out.println("Start of the thread");
                addDataToDB();
                System.out.println("End of the thread method");
            }

            private void addDataToDB() {
                // Dummy Code...
                try {
                    Thread.sleep(4000);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        };

        thread.start();
        System.out.println("Off and running...");
    }

}
```

This is only an example of common pattern where business logic is delegated to some asynchronous job pool we have no control over.
[Roger Hughes](http://www.blogger.com/profile/07042290171112551665) (the author) enumerates few techniques of testing such code, including:

- arbitrary ("long enough") `sleep()` in test method to make sure background logic finishes
- refactoring `doWork()` so that it accepts [`CountDownLatch`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/CountDownLatch.html) and agrees to notify it when job is done
- making the method above package private and [`@VisibleForTesting`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/annotations/VisibleForTesting.html) only
- "The" solution - refactoring `doWork()` so that it accepts arbitrary [`Runnable`](http://docs.oracle.com/javase/7/docs/api/java/lang/Runnable.html).
  In test we can wrap this `Runnable` (decorator pattern) and wait for inner `Runnable` to complete

Last solution is not bad but it changes the responsibilities of `ThreadWrapper` significantly.
Now it's up to the caller to decide what kind of job should be executed asynchronously while previously `ThreadWrapper` was encapsulating business logic completely.
I am not saying it's a bad design, but it's drastically different from original method.

# Awaitility

Can we write a test without such a massive refactoring?
First solution involves handy library called [Awaitility](https://code.google.com/p/awaitility/).
This library is not a silver bullet, it simply evaluates given condition periodically and makes sure it's fulfilled within given time.
It's the kind of code you probably wrote once or twice - wrapped in a library with well designed API.
So here is our initial approach:

```java
import static com.jayway.awaitility.Awaitility.await;
import static java.util.concurrent.TimeUnit.SECONDS;

//...

await().atMost(10, SECONDS).until(recordInserted());

//...

private Callable<Boolean> recordInserted() {
    return new Callable<Boolean>() {
        @Override
        public Boolean call() throws Exception {
            return dataExists();
        }
    };
}
```

I think there is nothing to explain here.
`dataExists()` is simply a `boolean` method that initially returns `false` but will eventually return `true` once the background task (`addDataToDB()`) is done.
In other words we assume that background task introduces some side effect and `dataExists()` can detect that side effect.
BTW I happened to have JDK 8 with Lambda support installed and IntelliJ IDEA gives me this nice tooltip:

[![](/assets/img/synchronising-multithreaded-integration/1.png)](/assets/img/synchronising-multithreaded-integration/1.png)

[
](/assets/img/synchronising-multithreaded-integration/2.png)

Suddenly I get this Java 8-compatible alternative suggested:

```java
private Callable<Boolean> recordInserted() {
    return () -> dataExists();
}
```

But there's more:

[![](/assets/img/synchronising-multithreaded-integration/2.png)](/assets/img/synchronising-multithreaded-integration/2.png)

Which transforms my code to:

```java
private Callable<Boolean> recordInserted() {
    return this::dataExists;
}
```

`this::` prefix means that `recordInsterted` is a method of current object.
Just as well we can say `someDao::dataExists`.
Simply put this syntax turns method into a function object we can pass around (this process is called [*eta expansion* in Scala](http://nurkiewicz.blogspot.no/2012/04/eta-expansion-internals-in-scala.html)).
By now `recordInsterted()` method is no longer that needed so I can inline it and remove it completely:

```java
await().atMost(10, SECONDS).until(this::dataExists);
```

I am not sure what I love more - the new lambda syntax or how IntelliJ IDEA takes pre-Java 8 code and retrofits it for me automatically (well, it's still a bit experimental, just reported [IDEA-106670](http://youtrack.jetbrains.com/issue/IDEA-106670)).
I can run this intention in IntelliJ project-wide, Lambda-enabling my whole code base in seconds.
Sweet!

But back to original problem.
Awaitility helps a lot by providing decent API and some handy features.
I use it extensively in combination with [FluentLenium](https://github.com/FluentLenium/FluentLenium).
But periodically polling for state changes feels a bit like a workaround and still introduces minimal latency.
But notice that running and synchronizing on asynchronous tasks is quite common and JDK already provides necessary facilities: [`Future` abstraction](http://nurkiewicz.blogspot.no/2013/02/javautilconcurrentfuture-basics.html)!

# `java.util.concurrent.Future`

To limit the scope of refactoring I will leave the original `new Thread()` approach for now and use [`SettableFuture<V>` from Guava](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/util/concurrent/SettableFuture.html).
It is a `Future<V>` implementation that allows triggering completion or failure at any time, from any thread (see [`DeferredResult` - asynchronous processing in Spring MVC](http://nurkiewicz.blogspot.no/2013/03/deferredresult-asynchronous-processing.html) for more advanced usage).
As you can see the changes are quite small:

```java
public class ThreadWrapper {

    public ListenableFuture<Void> doWork() {
        final SettableFuture<Void> future = SettableFuture.<Void>create();

        Thread thread = new Thread() {

            @Override
            public void run() {
                addDataToDB()
                //...

                //last instruction
                future.set(null);
            }

            private void addDataToDB() {
                // Dummy Code...
                // ...

            }

        };

        thread.start();
        return future;
    }

}
```

`doWork()` now returns [`ListenableFuture<Void>`](http://nurkiewicz.blogspot.no/2013/02/listenablefuture-in-guava.html) with lifecycle controlled inside asynchronous task.
We use `Void` but in reality you might want to return some asynchronous result instead.
`future.set(null)` invocation in the end is crucial.
It signals that future is fulfilled and all threads waiting for that future will be notified.
Once again, in practice you would use e.g. `Future<Integer>` and then instead of `null` we would say `future.set(someInteger)`.
Here `null` is just a placeholder for `Void` type.

How does this help us?
Test code can now rely on future completion:

```java
final ListenableFuture<Void> future = wrapper.doWork();
future.get(10, SECONDS);
```

`future.get()` blocks until future is done (with timeout), i.e. until we call `future.set(...)`.
BTW I use `ListenableFuture` from Guava but Java 8 introduces equivalent and standard [`CompletableFuture`](http://download.java.net/lambda/b88/docs/api/java/util/concurrent/CompletableFuture.html) - I will write about it soon.

So, we are getting somewhere.
`Future<T>` is a useful abstraction for waiting and signalling completion of background jobs.
But there is also one immense advantage of `Future` which are not taking, *ekhm*, advantage from - exception handling and propagation.
`Future.get()` will block until future is complete and return asynchronous result *or* throw an exception initially thrown from our job.
This is really useful for asynchronous tests.
Currently if `Thread.run()` throws an exception it may or may not be logged or visible to us and future will never be completed.
With Awaitility it's slightly better - it will timeout without any meaningful reason, which have to be tracked down manually in console/logs.
But with minor modification our test is much more verbose:

```java
public void run() {
    try {
        addDataToDB()
        //...
        future.set(null);
    } catch (Exception e) {
        future.setException(e);
    }
}
```

If some exception occurs in asynchronous job, it will pop-up and be shown as JUnit/TestNG failure reason.

# `(Listening)ExecutorService`

That's it.
If `addDataToDB()` throws an exception it will not be lost.
Instead our `future.get()` in test will re-throw that exception for us.
Our test won't simply timeout leaving us with no clue what went wrong.
Great, but do we really have to create this special `SettableFuture<T>` instance, can't we just use existing libraries that already give us `Future<T>` with correct underlying implementation?
Of course!
By this requires further refactoring:

```java
import com.google.common.util.concurrent.ListeningExecutorService;
import com.google.common.util.concurrent.MoreExecutors;

import java.util.concurrent.Executors;
import java.util.concurrent.Future;

public class ThreadWrapper {

    private final ListeningExecutorService executorService = 
        MoreExecutors.listeningDecorator(
            Executors.newSingleThreadExecutor()
        );

    public ListenableFuture<?> doWork() {
        Runnable job = new Runnable() {
            @Override
            public void run() {
                //...
            }
        };
        return executorService.submit(job);
    }

}
```

This is what you've all been waiting for.
Don't start new `Thread` all the time, use thread pool!
I actually went one step further by using [`ListeningExecutorService`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/util/concurrent/ListeningExecutorService.html) - an extension to `ExecutorService` that returns `ListenableFuture` instances ([see why you want that](http://nurkiewicz.blogspot.no/2013/02/listenablefuture-in-guava.html)).
But the solution doesn't require this, I just spread good practices.
As you can see `Future` instance is now created and managed for us.
The test is exactly the same but production code is cleaner and more robust.

# `MoreExecutors.sameThreadExecutor()`

The final trick I want to show you involves dependency injection.
First let's externalize the creation of a thread pool from `ThreadWrapper` class:

```java
private final ListeningExecutorService executorService;

public ThreadWrapper() {
    this(Executors.newSingleThreadExecutor());
}

public ThreadWrapper(ExecutorService executorService) {
    this.executorService = 
        MoreExecutors.listeningDecorator(executorService);
}
```

We can now optionally supply custom `ExecutorService`.
This is good for various other reasons, but for us it opens brand new testing opportunity: [`MoreExecutors.sameThreadExecutor()`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/util/concurrent/MoreExecutors.html#sameThreadExecutor()).
This time we modify our test slightly:

```java
final ThreadWrapper wrapper = new ThreadWrapper(MoreExecutors.sameThreadExecutor());
wrapper.doWork().get();
```

See how we pass custom `ExecutorService`?
It's a very special implementation that doesn't really maintain thread pool of any kind.
Every time you `submit()` some task to that "pool" it will be executed in the same thread in a blocking manner.
This means that we no longer have asynchronous test, even though the production code wasn't changed that much!
`wrapper.doWork()` will block until "background" job finishes.
The extra call to `get()` is still needed to make sure exceptions are propagated, but is guaranteed to never block (because the job is already done).

Using the same thread to execute asynchronous task instead of a thread pool might have an unexpected results if you somehow depend on thread-based properties, e.g. transactions, security, `ThreadLocal`.
However if you use standard [`ThreadPoolExecutor`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/ThreadPoolExecutor.html) with [`CallerRunsPolicy`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/ThreadPoolExecutor.CallerRunsPolicy.html), JDK already behaves this way if thread pool is overflowed.
So it's not that unusual.

# Summary

Testing asynchronous code is hard, but you have options.
Several options.
But one conclusion that strikes me is the side effect of our efforts.
We refactored original code in order to make it testable.
But the final production code is not only testable, but also much better structured and robust.
Surprisingly it's even source-code compatible with previous version as we barely changed return type from `void` to `Future<Void>`.

It seems to be a rule - testable code is often better designed and implemented.
Unit test is the first client code using our library.
It naturally forces us to to think more about consumers, not the implementation.
