---
layout: post
title: ExecutorService - 10 tips and tricks
date: '2014-11-20T20:54:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- CompletableFuture
- multithreading
- concurrency
modified_time: '2015-11-29T23:38:58.154+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5591977136018012505
blogger_orig_url: https://www.nurkiewicz.com/2014/11/executorservice-10-tips-and-tricks.html
---

[`ExecutorService`](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ExecutorService.html)
abstraction has been around since Java 5. We are talking about 2004 here. Just a
quick reminder: both Java 5 and 6 are no longer supported, Java 7
[won't be in half a year](http://www.oracle.com/technetwork/java/eol-135779.html).
The reason I'm bringing this up is that many Java programmers still don't fully
understand how `ExecutorService` works. There are many places to learn that,
today I wanted to share few lesser known features and practices. However this
article is still aimed toward intermediate programmers, nothing especially advanced.


## 1. Name pool threads

I can't emphasize this. When dumping threads of a running JVM or during debugging,
default thread pool naming scheme is `pool-N-thread-M`, where `N` stands for pool
sequence number (every time you create a new thread pool, global `N` counter is
incremented) and `M` is a thread sequence number within a pool. For example
`pool-2-thread-3` means third thread in second pool created in the JVM lifecycle.
See: [`Executors.defaultThreadFactory()`](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/Executors.html#defaultThreadFactory--).
Not very descriptive. JDK makes it slightly complex to properly name threads because
naming strategy is hidden inside
[`ThreadFactory`](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ThreadFactory.html).
Luckily Guava has a helper class for that:

```java
import com.google.common.util.concurrent.ThreadFactoryBuilder;

final ThreadFactory threadFactory = new ThreadFactoryBuilder()
        .setNameFormat("Orders-%d")
        .setDaemon(true)
        .build();
final ExecutorService executorService = Executors.newFixedThreadPool(10, threadFactory);
```

By default thread pools create non-daemon threads, decide whether this suits you or not.


## 2. Switch names according to context

This is a trick I learnt from
[*Supercharged jstack: How to Debug Your Servers at 100mph*](http://www.takipiblog.com/supercharged-jstack-how-to-debug-your-servers-at-100mph/).
Once we remember about thread names, we can actually change them at runtime whenever
we want! It makes sense because thread dumps show classes and method names, not
parameters and local variables. By adjusting thread name to keep some essential
transaction identifier we can easily track which message/record/query/etc. is slow
or caused deadlock. Example:

```java
private void process(String messageId) {
    executorService.submit(() -> {
        final Thread currentThread = Thread.currentThread();
        final String oldName = currentThread.getName();
        currentThread.setName("Processing-" + messageId);
        try {
            //real logic here...
        } finally {
            currentThread.setName(oldName);
        }
    });
}
```

Inside `try`-`finally` block current thread is named `Processing-WHATEVER-MESSAGE-ID-IS`.
This might come in handy when tracking down message flow through the system.


## 3. Explicit and safe shutdown

Between client threads and thread pool there is a queue of tasks. When your application
shuts down, you must take care of two things: what is happening with queued tasks and
how already running tasks are behaving (more on that later). Surprisingly many developers
are not shutting down thread pool properly or consciously. There are two techniques:
either let all queued tasks to execute (`shutdown()`) or drop them (`shutdownNow()`) -
it totally depends on your use case. For example if we submitted a bunch of tasks and
want to return as soon as all of them are done, use `shutdown()`:

```java
private void sendAllEmails(List<String> emails) throws InterruptedException {
    emails.forEach(email ->
            executorService.submit(() ->
                    sendEmail(email)));
    executorService.shutdown();
    final boolean done = executorService.awaitTermination(1, TimeUnit.MINUTES);
    log.debug("All e-mails were sent so far? {}", done);
}
```

In this case we send a bunch of e-mails, each as a separate task in a thread pool.
After submitting these tasks we shut down pool so that it no longer accepts any new
tasks. Then we wait at most one minute until all these tasks are completed. However
if some tasks are still pending, `awaitTermination()` will simply return `false`.
Moreover, pending tasks will continue processing. I know hipsters would go for:

```java
emails.parallelStream().forEach(this::sendEmail);
```

Call me old fashioned, but I like to control the number of parallel threads. Never
mind, an alternative to graceful `shutdown()` is `shutdownNow()`:

```java
final List<Runnable> rejected = executorService.shutdownNow();
log.debug("Rejected tasks: {}", rejected.size());
```

This time all queued tasks are discarded and returned. Already running jobs are
allowed to continue.


## 4. Handle interruption with care

Lesser known feature of `Future` interface is cancelling. Rather than repeating
myself, check out my older article:
[*InterruptedException and interrupting threads explained*](http://www.nurkiewicz.com/2014/05/interruptedexception-and-interrupting.html)


## 5. Monitor queue length and keep it bounded

Incorrectly sized thread pools may cause slowness, instability and memory leaks. If
you configure too few threads, the queue will build up, consuming a lot of memory.
Too many threads on the other hand will slow down the whole system due to excessive
context switches - and lead to same symptoms. It's important to look at depth of queue
and keep it bounded, so that overloaded thread pool simply rejects new tasks temporarily:

```java
final BlockingQueue<Runnable> queue = new ArrayBlockingQueue<>(100);
executorService = new ThreadPoolExecutor(n, n,
        0L, TimeUnit.MILLISECONDS,
        queue);
```

Code above is equivalent to `Executors.newFixedThreadPool(n)`, however instead of
default unlimited `LinkedBlockingQueue` we use `ArrayBlockingQueue` with fixed capacity
of `100`. This means that if 100 tasks are already queued (and `n` being executed),
new task will be rejected with `RejectedExecutionException`. Also since `queue` is now
available externally, we can periodically call `size()` and put it in
logs/JMX/whatever monitoring mechanism you use.


## 6. Remember about exception handling

What will be the result of the following snippet?

```java
executorService.submit(() -> {
    System.out.println(1 / 0);
});
```

I got bitten by that too many times: it won't print **anything**. No sign of
`java.lang.ArithmeticException: / by zero`, nothing. Thread pool just swallows this
exception, as if it never happened. If it was a good'ol `java.lang.Thread` created
from scratch,
[`UncaughtExceptionHandler`](https://docs.oracle.com/javase/8/docs/api/java/lang/Thread.UncaughtExceptionHandler.html)
could work. But with thread pools you must be more careful. If you are submitting
`Runnable` (without any result, like above), you *must* surround whole body with
`try`-`catch` and at least log it. If you are submitting `Callable<Integer>`, ensure
you always dereference it using blocking `get()` to re-throw exception:

```java
final Future<Integer> division = executorService.submit(() -> 1 / 0);
//below will throw ExecutionException caused by ArithmeticException
division.get();
```

Interestingly even Spring framework made this bug with
[`@Async`](http://docs.spring.io/spring/docs/current/javadoc-api/org/springframework/scheduling/annotation/Async.html),
see: [SPR-8995](https://jira.spring.io/browse/SPR-8995) and
[SPR-12090](https://jira.spring.io/browse/SPR-12090).


## 7. Monitor waiting time in a queue

Monitoring work queue depth is one side. However when troubleshooting single
transaction/task it's worthwhile to see how much time passed between submitting task
and actual execution. This duration should preferably be close to 0 (when there was
some idle thread in a pool), however it will grow when task has to be queued. Moreover
if pool doesn't have a fixed number of threads, running new task might require spawning
thread, also consuming short amount of time. In order to cleanly monitor this metric,
wrap original `ExecutorService` with something similar to this:

```java
public class WaitTimeMonitoringExecutorService implements ExecutorService {

    private final ExecutorService target;

    public WaitTimeMonitoringExecutorService(ExecutorService target) {
        this.target = target;
    }

    @Override
    public <T> Future<T> submit(Callable<T> task) {
        final long startTime = System.currentTimeMillis();
        return target.submit(() -> {
                    final long queueDuration = System.currentTimeMillis() - startTime;
                    log.debug("Task {} spent {}ms in queue", task, queueDuration);
                    return task.call();
                }
        );
    }

    @Override
    public <T> Future<T> submit(Runnable task, T result) {
        return submit(() -> {
            task.run();
            return result;
        });
    }

    @Override
    public Future<?> submit(Runnable task) {
        return submit(new Callable<Void>() {
            @Override
            public Void call() throws Exception {
                task.run();
                return null;
            }
        });
    }

    //...

}
```

This is not a complete implementation, but you get the basic idea. The moment we
submit a task to a thread pool, we immediately start measuring time. We stop as soon
as task was picked up and begins execution. Don't be fooled by close proximity of
`startTime` and `queueDuration` in source code. In fact these two lines are evaluated
in different threads, probably milliseconds or even seconds apart, e.g.:

```
Task com.nurkiewicz.MyTask@7c7f3894 spent 9883ms in queue
```


## 8. Preserve client stack trace

Reactive programming seems to get a lot of attention these days.
[Reactive manifesto](http://www.reactivemanifesto.org/),
[reactive streams](http://www.reactive-streams.org/),
[RxJava](https://github.com/ReactiveX/RxJava) (just released 1.0!),
[Clojure agents](http://clojure.org/agents),
[scala.rx](https://github.com/lihaoyi/scala.rx)... They all work great, but stack
traces are no longer your friend, they are at most useless. Take for example an
exception happening in a task submitted to thread pool:

```
java.lang.NullPointerException: null
    at com.nurkiewicz.MyTask.call(Main.java:76) ~[classes/:na]
    at com.nurkiewicz.MyTask.call(Main.java:72) ~[classes/:na]
    at java.util.concurrent.FutureTask.run(FutureTask.java:266) ~[na:1.8.0]
    at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142) ~[na:1.8.0]
    at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617) ~[na:1.8.0]
    at java.lang.Thread.run(Thread.java:744) ~[na:1.8.0]
```

We can easily discover that `MyTask` threw NPE at line 76. But we have no idea who
submitted this task, because stack trace reveals only `Thread` and
`ThreadPoolExecutor`. We can technically navigate through the source code in hope to
find just one place where `MyTask` is created. But without threads (not to mention
event-driven, reactive, actor-ninja-programming) we would immediately see full
picture. What if we could preserve stack trace of client code (the one which submitted
task) and show it, e.g. in case of failure? The idea isn't new, for example
[Hazelcast](http://hazelcast.com/) propagates exceptions
[from owner node to client code](https://github.com/hazelcast/hazelcast/blob/7f8cd30e4e445473271d2e434ad939d156a151ca/hazelcast/src/main/java/com/hazelcast/util/ExceptionUtil.java#L29).
This is how naïve support for keeping client stack trace in case of failure could look:

```java
public class ExecutorServiceWithClientTrace implements ExecutorService {

    protected final ExecutorService target;

    public ExecutorServiceWithClientTrace(ExecutorService target) {
        this.target = target;
    }

    @Override
    public <T> Future<T> submit(Callable<T> task) {
        return target.submit(wrap(task, clientTrace(), Thread.currentThread().getName()));
    }

    private <T> Callable<T> wrap(final Callable<T> task, final Exception clientStack, String clientThreadName) {
        return () -> {
            try {
                return task.call();
            } catch (Exception e) {
                log.error("Exception {} in task submitted from thrad {} here:", e, clientThreadName, clientStack);
                throw e;
            }
        };
    }

    private Exception clientTrace() {
        return new Exception("Client stack trace");
    }

    @Override
    public <T> List<Future<T>> invokeAll(Collection<? extends Callable<T>> tasks) throws InterruptedException {
        return tasks.stream().map(this::submit).collect(toList());
    }

    //...

}
```

This time in case of failure we will retrieve full stack trace and thread name of a
place where task was submitted. Much more valuable compared to standard exception
seen earlier:

```
Exception java.lang.NullPointerException in task submitted from thrad main here:
java.lang.Exception: Client stack trace
    at com.nurkiewicz.ExecutorServiceWithClientTrace.clientTrace(ExecutorServiceWithClientTrace.java:43) ~[classes/:na]
    at com.nurkiewicz.ExecutorServiceWithClientTrace.submit(ExecutorServiceWithClientTrace.java:28) ~[classes/:na]
    at com.nurkiewicz.Main.main(Main.java:31) ~[classes/:na]
    at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method) ~[na:1.8.0]
    at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62) ~[na:1.8.0]
    at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43) ~[na:1.8.0]
    at java.lang.reflect.Method.invoke(Method.java:483) ~[na:1.8.0]
    at com.intellij.rt.execution.application.AppMain.main(AppMain.java:134) ~[idea_rt.jar:na]
```


## 9. Prefer CompletableFuture

In Java 8 more powerful
[`CompletableFuture` was introduced](http://www.nurkiewicz.com/2013/05/java-8-definitive-guide-to.html).
Please use it whenever possible. `ExecutorService` wasn't extended to support this
enhanced abstraction, so you have to take care of it yourself. Instead of:

```java
final Future<BigDecimal> future = 
    executorService.submit(this::calculate);
```

do:

```java
final CompletableFuture<BigDecimal> future = 
    CompletableFuture.supplyAsync(this::calculate, executorService);
```

`CompletableFuture` extends `Future` so everything works as it used to. But more
advanced consumers of your API will truly appreciate extended functionality given by
`CompletableFuture`.


## 10. Synchronous queue

[`SynchronousQueue`](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/SynchronousQueue.html)
is an interesting `BlockingQueue` that's not really a queue. It's not even a data
structure *per se*. It's best explained as a queue with capacity of 0. Quoting JavaDoc:

> each `insert` operation must wait for a corresponding `remove` operation by another
> thread, and vice versa. A synchronous queue does not have any internal capacity, not
> even a capacity of one. You cannot peek at a synchronous queue because an element is
> only present when you try to remove it; you cannot insert an element (using any
> method) unless another thread is trying to remove it; you cannot iterate as there is
> nothing to iterate. [...]
>
> Synchronous queues are similar to rendezvous channels used in CSP and Ada.

How is this related to thread pools? Try using `SynchronousQueue` with
`ThreadPoolExecutor`:

```java
BlockingQueue<Runnable> queue = new SynchronousQueue<>();
ExecutorService executorService = new ThreadPoolExecutor(2, 2,
        0L, TimeUnit.MILLISECONDS,
        queue);
```

We created a thread pool with two threads and a `SynchronousQueue` in front of it.
Because `SynchronousQueue` is essentially a queue with 0 capacity, such
`ExecutorService` will only accept new tasks if there is an idle thread available. If
all threads are busy, new task will be rejected immediately and will never wait. This
behavior might be desirable when processing in background must start immediately or
be discarded.

---

That's it, I hope you found at least one interesting feature!
