---
layout: post
title: Simplifying ReadWriteLock with Java 8 and lambdas
date: '2014-03-17T21:14:00.003+01:00'
author: Tomasz Nurkiewicz
tags:
- multithreading
- java 8
modified_time: '2014-04-22T23:07:28.455+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-7481489635743481353
blogger_orig_url: https://www.nurkiewicz.com/2014/03/simplifying-readwritelock-with-java-8.html
---

Considering legacy Java code, no matter where you look, Java 8 with lambda expressions can definitely improve quality and readability.
Today let us look at [`ReadWriteLock`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/locks/ReadWriteLock.html) and how we can make using it simpler.
Suppose we have a class called `Buffer` that remembers last couple of messages in a queue, counting and discarding old ones.
The implementation is quite straightforward:

```java
public class Buffer {

    private final int capacity;
    private final Deque<String> recent;
    private int discarded;

    public Buffer(int capacity) {
        this.capacity = capacity;
        this.recent = new ArrayDeque<>(capacity);
    }

    public void putItem(String item) {
        while (recent.size() >= capacity) {
            recent.removeFirst();
            ++discarded;
        }
        recent.addLast(item);
    }

    public List<String> getRecent() {
        final ArrayList<String> result = new ArrayList<>();
        result.addAll(recent);
        return result;
    }

    public int getDiscardedCount() {
        return discarded;
    }

    public int getTotal() {
        return discarded + recent.size();
    }

    public void flush() {
        discarded += recent.size();
        recent.clear();
    }

}
```

Now we can `putItem()` many times, but the internal `recent` queue will only keep last `capacity` elements.
However it also remembers how many items it had to discard to avoid memory leak.
This class works fine, but only in single-threaded environment.
We use not thread-safe [`ArrayDeque`](http://docs.oracle.com/javase/7/docs/api/java/util/ArrayDeque.html) and non-synchronized `int`.
While reading and writing to `int` is atomic, changes are not guaranteed to be visible in different threads.
Also even if we use [thread safe `BlockingDeque`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/BlockingDeque.html) together with [`AtomicInteger`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/atomic/AtomicInteger.html) we are still in danger of race condition because those two variables aren't synchronized with each other.

One approach would be to [`synchronize` all the methods](http://memegenerator.net/instance/47255837), but that seems quite restrictive.
Moreover we suspect that reads greatly outnumber writes.
In such cases `ReadWriteLock` is a fantastic alternative.
It actually consists of two locks - one for reading and one for writing.
In reality they both compete for the same lock which can be obtained either by one writer or multiple readers at the same time.
So we can have concurrent reads when no one is writing and only occasionally writer blocks all readers.
Using `synchronized` will just always block all the others, no matter what they do.
The sad part of `ReadWriteLock` is that it introduces a lot of boilerplate.
You have to explicitly open a lock and remember to `unlock()` it in `finally` block.
Our implementation becomes hard to read:

```java
public class Buffer {

    private final int capacity;
    private final Deque<String> recent;
    private int discarded;

    private final Lock readLock;
    private final Lock writeLock;


    public Buffer(int capacity) {
        this.capacity = capacity;
        recent = new ArrayDeque<>(capacity);
        final ReentrantReadWriteLock rwLock = new ReentrantReadWriteLock();
        readLock = rwLock.readLock();
        writeLock = rwLock.writeLock();
    }

    public void putItem(String item) {
        writeLock.lock();
        try {
            while (recent.size() >= capacity) {
                recent.removeFirst();
                ++discarded;
            }
            recent.addLast(item);
        } finally {
            writeLock.unlock();
        }
    }

    public List<String> getRecent() {
        readLock.lock();
        try {
            final ArrayList<String> result = new ArrayList<>();
            result.addAll(recent);
            return result;
        } finally {
            readLock.unlock();
}

    public int getDiscardedCount() {
        readLock.lock();
        try {
            return discarded;
        } finally {
            readLock.unlock();
        }
    }

    public int getTotal() {
        readLock.lock();
        try {
            return discarded + recent.size();
        } finally {
            readLock.unlock();
        }
    }

    public void flush() {
        writeLock.lock();
        try {
            discarded += recent.size();
            recent.clear();
        } finally {
            writeLock.unlock();
        }
    }

}  
        
```

This is how it was done pre-Jave 8.
Effective, safe and...
ugly.
However with lambda expressions we can wrap cross-cutting concerns in a utility class like this:

```java
public class FunctionalReadWriteLock {

    private final Lock readLock;
    private final Lock writeLock;

    public FunctionalReadWriteLock() {
        this(new ReentrantReadWriteLock());
    }

    public FunctionalReadWriteLock(ReadWriteLock lock) {
        readLock = lock.readLock();
        writeLock = lock.writeLock();
    }

    public <T> T read(Supplier<T> block) {
        readLock.lock();
        try {
            return block.get();
        } finally {
            readLock.unlock();
        }
    }

    public void read(Runnable block) {
        readLock.lock();
        try {
            block.run();
        } finally {
            readLock.unlock();
        }
    }

    public <T> T write(Supplier<T> block) {
        writeLock.lock();
        try {
            return block.get();
        } finally {
            writeLock.unlock();
        }
    }

    public void write(Runnable block) {
        writeLock.lock();
        try {
            block.run();
        } finally {
            writeLock.unlock();
        }
    }

}
```

As you can see we wrap `ReadWriteLock` and provide a set of utility methods to work with.
In principle we would like to pass a `Runnable` or `Supplier<T>` (interface having single `T get()` method) and make sure calling it is surrounded with proper lock.
We could write the exact same wrapper class without lambdas, but having them greatly simplifies client code:

```java
public class Buffer {

    private final int capacity;
    private final Deque<String> recent;
    private int discarded;

    private final FunctionalReadWriteLock guard;

    public Buffer(int capacity) {
        this.capacity = capacity;
        recent = new ArrayDeque<>(capacity);
        guard = new FunctionalReadWriteLock();
    }

    public void putItem(String item) {
        guard.write(() -> {
            while (recent.size() >= capacity) {
                recent.removeFirst();
                ++discarded;
            }
            recent.addLast(item);
        });
    }

    public List<String> getRecent() {
        return guard.read(() -> {
            return recent.stream().collect(toList());
        });
    }

    public int getDiscardedCount() {
        return guard.read(() -> discarded);
    }

    public int getTotal() {
        return guard.read(() -> discarded + recent.size());
    }

    public void flush() {
        guard.write(() -> {
            discarded += recent.size();
            recent.clear();
        });
    }

}
```

See how we invoke `guard.read()` and `guard.write()` passing pieces of code that should be guarded?
Looks quite neat.
BTW have you noticed how we can turn any collection into any other collection (here: `Deque` into `List`) using `stream()`?
Now if we extract couple of internal methods we can use method references to even further simplify lambdas:

```java
public void flush() {
    guard.write(this::unsafeFlush);
}

private void unsafeFlush() {
    discarded += recent.size();
    recent.clear();
}

public List<String> getRecent() {
    return guard.read(this::defensiveCopyOfRecent);
}

private List<String> defensiveCopyOfRecent() {
    return recent.stream().collect(toList());
}
```

This is just one of the many ways you can improve existing code and libraries by taking advantage of lambda expressions.
We should be really happy that they finally made their way into Java language - while being already present in dozens of other JVM languages.
