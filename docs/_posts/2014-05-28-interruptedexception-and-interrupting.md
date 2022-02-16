---
layout: post
title: InterruptedException and interrupting threads explained
date: '2014-05-28T19:40:00.002+02:00'
author: Tomasz Nurkiewicz
tags:
- multithreading
modified_time: '2015-11-29T09:52:41.329+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-9001464640366716101
blogger_orig_url: https://www.nurkiewicz.com/2014/05/interruptedexception-and-interrupting.html
---

If
[`InterruptedException`](http://docs.oracle.com/javase/8/docs/api/java/lang/InterruptedException.html)
wasn't a checked exception, probably no one wouldn't even notice it - which
would actually prevent couple of bugs throughout these years. But since
it has to be handled, many handle it incorrectly or thoughtlessly.
Let's take a simple example of a thread that periodically does some
clean up, but in between sleeps most of the time.


```java
class Cleaner implements Runnable {

  Cleaner() {
    final Thread cleanerThread = new Thread(this, "Cleaner");
    cleanerThread.start();
  }

  @Override
  public void run() {
    while(true) {
      cleanUp();
      try {
        TimeUnit.SECONDS.sleep(1);
      } catch (InterruptedException e) {
        // TODO Auto-generated catch block
        e.printStackTrace();
      }
    }
  }

  private void cleanUp() {
    //...
  }

}
```

This code is wrong on so many layers!


1.  Starting `Thread` in a constructor might not be a good idea in some
    environments, e.g. some frameworks like Spring will create dynamic
    subclass to support method interception. We will end-up with two
    threads running from two instances.
2.  `InterruptedException` is swallowed, and the exception itself is not
    logged properly
3.  This class starts a new thread for every instance, it should use
    [`ScheduledThreadPoolExecutor`](http://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ScheduledThreadPoolExecutor.html)
    instead, shared among many instances (more robust and
    memory-effective)
4.  Also with `ScheduledThreadPoolExecutor` we could avoid coding
    sleeping/working loop by ourselves, and also switch to fixed-rate as
    opposed to fixed-delay behaviour presented here.
5.  Last but not least there is no way to get rid of this thread, even
    when `Cleaner` instance is no longer referenced by anything else

All problems are valid, but swallowing `InterruptedException` is its
biggest sin. Before we understand why, let us think for a while what
does this exception mean and how we can take advantage of it to
interrupt threads gracefully. Many blocking operations in JDK declare
throwing `InterruptedException`, including:


-   `Object.wait()`
-   `Thread.sleep()`
-   `Process.waitFor()`
-   `AsynchronousChannelGroup.awaitTermination()`
-   Various blocking methods in `java.util.concurrent.*`, e.g.
    `ExecutorService.awaitTermination()`, `Future.get()`,
    `BlockingQueue.take()`, `Semaphore.acquire()` `Condition.await()`
    and many, many others
-   `SwingUtilities.invokeAndWait()`

Notice that blocking I/O does not throw `InterruptedException` (which is
a shame). If all these classes declare `InterruptedException`, you might
be wondering when is this exception ever thrown?


-   When a thread is blocked on some method declaring
    `InterruptedException` and you call `Thread.interrupt()` on such
    thread, most likely blocked method will immediately throw
    `InterruptedException`.
-   If you submitted a task to a thread pool
    (`ExecutorService.submit()`) and you call `Future.cancel(true)`
    while the task was being executed. In that case the thread pool will
    try to interrupt thread running such task for you, effectively
    interrupting your task.

Knowing what `InterruptedException` actually means, we are well equipped
to handle it properly. If someone tries to interrupt our thread and we
discovered it by catching `InterruptedException`, the most reasonable
thing to do is letting said thread to finish, e.g.:


```java
class Cleaner implements Runnable, AutoCloseable {

  private final Thread cleanerThread;

  Cleaner() {
    cleanerThread = new Thread(this, "Cleaner");
    cleanerThread.start();
  }

  @Override
  public void run() {
    try {
      while (true) {
        cleanUp();
        TimeUnit.SECONDS.sleep(1);
      }
    } catch (InterruptedException ignored) {
      log.debug("Interrupted, closing");
    }
  }

  //...   

  @Override
  public void close() {
    cleanerThread.interrupt();
  }
}
```

Notice that `try-catch` block now surrounds `while` loop. This way if
`sleep()` throws `InterruptedException`, we will break out of the loop.
You might argue that we should log `InterruptedException`'s
stack-trace. This depends on the situation, as in this case interrupting
a thread is something we really expect, not a failure. But it's up to
you. The bottom-line is that if `sleep()` is interrupted by another
thread, we quickly escape from `run()` altogether. If you are very
careful you might ask what happens if we interrupt thread while it's in
`cleanUp()` method rather than sleeping? Often you'll come across
manual flag like this:


```java
private volatile boolean stop = false;

@Override
public void run() {
  while (!stop) {
    cleanUp();
    TimeUnit.SECONDS.sleep(1);
  }
}

@Override
public void close() {
  stop = true;
}
```

However notice that `stop` flag (it has to be `volatile`!) won't
interrupt blocking operations, we have to wait until `sleep()` finishes.
On the other side one might argue that explicit `flag` gives us better
control since we can monitor its value at any time. It turns out thread
interruption works the same way. If someone interrupted thread while it
was doing non-blocking computation (e.g. inside `cleanUp()`) such
computations aren't interrupted immediately. However thread is marked
as *interrupted* and every subsequent blocking operation (e.g.
`sleep()`) will simply throw `InterruptedException` immediately - so we
won't loose that signal.

We can also take advantage of that fact if we write non-blocking thread
that still wants to take advantage of thread interruption facility.
Instead of relying on `InterruptedException` we simply have to check for
`Thread.isInterrupted()` periodically:


```java
public void run() {
  while (!Thread.currentThread().isInterrupted()) {
    someHeavyComputations();
  }
}
```

Above, if someone interrupts our thread, we will abandon computation as
soon as `someHeavyComputations()` returns. If it runs for two long or
infinitely, we will never discover interruption flag. Interestingly
`interrupted` flag is not a *one-time pad*. We can call
`Thread.interrupted()` instead of `isInterrupted()`, which will reset
`interrupted` flag and we can continue. Occasionally you might want to
ignore interrupted flag and continue running. In that case
`interrupted()` might come in handy. BTW I (imprecisely) call
\"getters\" that [change the state of object being
observed](http://en.wikipedia.org/wiki/Observer_effect_(physics))
\"*Heisengetters*\".


## Note on `Thread.stop()`

If you are old-school programmer, you may recall
[`Thread.stop()`](http://docs.oracle.com/javase/8/docs/api/java/lang/Thread.html#stop--)
method, which has been [deprecated for 10 years
now](http://docs.oracle.com/javase/1.5.0/docs/guide/misc/threadPrimitiveDeprecation.html).
In Java 8 there were plans to [\"de-implement
it\"](http://cs.oswego.edu/pipermail/concurrency-interest/2013-December/012028.html),
but in 1.8u5 it's still there. Nevertheless, don't use it and refactor
any code using `Thread.stop()` into `Thread.interrupt()`.


## `Uninterruptibles` from Guava

Rarely you might want to ignore `InterruptedException` altogether. In
that case have a look at
[`Uninterruptibles`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/util/concurrent/Uninterruptibles.html)
from Guava. It has plenty of utility methods like
`sleepUninterruptibly()` or `awaitUninterruptibly(CountDownLatch)`. Just
be careful with them. I know they don't declare `InterruptedException`
(which might be handful), but they also completely prevent current
thread from being interrupted - which is quite unusual.


## Summary

By now I hope you have some understanding why certain methods throw
`InterruptedException`. The main takeaways are:


-   Caught `InterruptedException` should be handled *properly* - most of
    the time it means breaking out of the current task/loop/thread
    entirely
-   Swallowing `InterruptedException` is rarely a good idea
-   If thread was interrupted while it wasn't in a blocking call, use
    `isInterrupted()`. Also entering blocking method when thread was
    already interrupted should immediately throw `InterruptedException`
