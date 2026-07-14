---
layout: post
title: Simplifying trading system with Akka
date: '2014-05-29T23:20:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- akka
- multithreading
modified_time: '2014-05-29T23:20:23.356+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-10309046592518903
blogger_orig_url: https://www.nurkiewicz.com/2014/05/simplifying-trading-system-with-akka.html
---

My colleagues are developing a trading system that processes quite heavy stream of incoming transactions.
Each transaction covers one `Instrument` (think bond or stock) and has some (now) unimportant properties.
They are stuck with Java (\< 8), so let's stick to it:

```java
class Instrument implements Serializable, Comparable<Instrument> {
    private final String name;

    public Instrument(String name) {
        this.name = name;
    }

    //...Java boilerplate

}

public class Transaction {
    private final Instrument instrument;

    public Transaction(Instrument instrument) {
        this.instrument = instrument;
    }

    //...Java boilerplate

}
```

`Instrument` will later be used as a key in `HashMap`, so [for the future](http://www.nurkiewicz.com/2014/04/hashmap-performance-improvements-in.html) we pro-actively implement `Comparable<Instrument>`.
This is our domain, now the requirements:

1.  Transactions come into the system and need to be processed (whatever that means), as soon as possible
2.  We are free to process them in any order
3.  ...however transactions for the same instrument need to be processed sequentially in the exact same order as they came in.

Initial implementation was straightforward - put all incoming transactions into a queue (e.g.
[`ArrayBlockingQueue`](http://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ArrayBlockingQueue.html)) with a single consumer.
This satisfies last requirement, since queue preserves strict FIFO ordering across all transactions.
But such an architecture prevents concurrent processing of unrelated transactions for different instruments, thus wasting compelling throughput improvement.
Not surprisingly this implementation, while undoubtedly simple, became a bottleneck.

The first idea was to somehow split incoming transactions by instrument and process instruments individually.
We came up with the following data structure:

```java
priavate final ConcurrentMap<Instrument, Queue<Transaction>> queues = 
    new ConcurrentHashMap<Instrument, Queue<Transaction>>();

public void accept(Transaction tx) {
    final Instrument instrument = tx.getInstrument();
    if (queues.get(instrument) == null) {
        queues.putIfAbsent(instrument, new LinkedBlockingQueue<Transaction>());
    }
    final Queue<Transaction> queue = queues.get(instrument);
    queue.add(tx);
}
```

Yuck!
But worst is yet to come.
How do you make sure at most one thread processes each queue at a time?
After all, otherwise two threads could pick up items from one queue (one instrument) and process them in reversed order, which is not allowed.
The simplest case is to have a `Thread` per queue - this won't scale, as we expect tens of thousands of different instruments.
So we can have say `N` threads and let each of them handle a subset of queues, e.g. `instrument.hashCode() % N` tells us which thread takes care of given queue.
But it's still not perfect for three reasons:

1.  One thread must "observe" many queues, most likely busy-waiting, iterating over them all the time.
    Alternatively queue might wake up its parent thread somehow
2.  In worst case scenario all instruments will have conflicting hash codes, targeting only one thread - which is effectively the same as our initial solution
3.  It's just damn complex!
    Beautiful code is not complex!

Implementing this monstrosity is possible, but hard and error-prone.
Moreover there is another non-functional requirement: instruments come and go and there are hundreds of thousands of them over time.
After a while we should remove entries in our map representing instruments that were not seen lately.
Otherwise we'll get a memory leak.

If you can come up with some simpler solution, let me know.
In the meantime let me tell you what I suggested my colleagues.
As you can guess, it was Akka - and it turned out to be embarrassingly simple.
We need two kinds of actors: `Dispatcher` and `Processor`.
`Dispatcher` has one instance and receive all incoming transactions.
Its responsibility is to find or spawn worker `Processor` actor for each `Instrument` and push transaction to it:

```java
public class Dispatcher extends UntypedActor {

    private final Map<Instrument, ActorRef> instrumentProcessors = 
        new HashMap<Instrument, ActorRef>();

    @Override
    public void onReceive(Object message) throws Exception {
        if (message instanceof Transaction) {
            dispatch(((Transaction) message));
        } else {
            unhandled(message);
        }
    }

    private void dispatch(Transaction tx) {
        final ActorRef processor = findOrCreateProcessorFor(tx.getInstrument());
        processor.tell(tx, self());
    }

    private ActorRef findOrCreateProcessorFor(Instrument instrument) {
        final ActorRef maybeActor = instrumentProcessors.get(instrument);
        if (maybeActor != null) {
            return maybeActor;
        } else {
            final ActorRef actorRef = context().actorOf(
                Props.create(Processor.class), instrument.getName());
            instrumentProcessors.put(instrument, actorRef);
            return actorRef;
        }
    }
}
```

This is dead simple.
Since our `Dispatcher` actor is effectively single-threaded, no synchronization is needed.
We barely receive `Transaction`, lookup or create `Processor` and pass `Transaction` further.
This is how `Processor` implementation could look like:

```java
public class Processor extends UntypedActor {

    private final LoggingAdapter log = Logging.getLogger(getContext().system(), this);

    @Override
    public void onReceive(Object message) throws Exception {
        if (message instanceof Transaction) {
            process(((Transaction) message));
        } else {
            unhandled(message);
        }
    }

    private void process(Transaction tx) {
        log.info("Processing {}", tx);
    }
}
```

That's it!
Interestingly our Akka implementation is almost identical to our first idea with map of queues.
After all an actor is just a queue and a (logical) thread processing items in that queue.
The difference is: Akka manages limited thread pool and shares it between maybe hundreds of thousands of actors.
And because every instrument has its own dedicated (and "single-threaded") actor, sequential processing of transactions per instrument is guaranteed.

One more thing.
As stated earlier, there is an enormous amount of instruments and we don't want to keep actors for instruments that weren't seen for quite a while.
Let's say that if a `Processor` didn't receive any transaction within an hour, it should be stopped and garbage collected.
If later we receive new transaction for such instrument, we can always recreate it.
This one is quite tricky - we must ensure that if transaction arrives when processor decided to delete itself, we can't loose that transaction.
Rather than stopping itself, `Processor` signals its parent it was idle for too long.
`Dispatcher` will then send `PoisonPill` to it.
Because both `ProcessorIdle` and `Transaction` messages are processed sequentially, there is no risk of transaction being sent to no longer existing actor.

Each actor manages its lifecycle independently by scheduling timeout using `setReceiveTimeout`:

```java
public class Processor extends UntypedActor {

    @Override
    public void preStart() throws Exception {
        context().setReceiveTimeout(Duration.create(1, TimeUnit.HOURS));
    }

    @Override
    public void onReceive(Object message) throws Exception {
        //...
        if (message instanceof ReceiveTimeout) {
            log.debug("Idle for two long, shutting down");
            context().parent().tell(ProcessorIdle.INSTANCE, self());
        } else {
            unhandled(message);
        }
    }

}

enum ProcessorIdle {
    INSTANCE
} 
```

Clearly, when `Processor` did not receive any message for a period of one hour, it gently signals that to its parent (`Dispatcher`).
But the actor is still alive and can handle transactions if they happen precisely after an hour.
What `Dispatcher` does is it kills given `Processor` and removes it from a map:

```java
public class Dispatcher extends UntypedActor {

    private final BiMap<Instrument, ActorRef> instrumentProcessors = HashBiMap.create();

    public void onReceive(Object message) throws Exception {
        //...
        if (message == ProcessorIdle.INSTANCE) {
            removeIdleProcessor(sender());
            sender().tell(PoisonPill.getInstance(), self());
        } else {
            unhandled(message);
        }
    }

    private void removeIdleProcessor(ActorRef idleProcessor) {
        instrumentProcessors.inverse().remove(idleProcessor);
    }

    private void dispatch(Transaction tx) {
        final ActorRef processor = findOrCreateProcessorFor(tx.getInstrument());
        processor.tell(tx, self());
    }

    //...

}
```

There was a slight inconvenience.
`instrumentProcessors` used to be a `Map<Instrument, ActorRef>`.
This proved to be insufficient, since we suddenly have to remove an entry in this map by value.
In other words we need to find a key (`Instrument`) that maps to a given `ActorRef` (`Processor`).
There are different ways to handle it (e.g.
idle `Processor` could send an `Instrumnt` it handles), but instead I used [`BiMap<K, V>`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/collect/BiMap.html) from Guava.
It works because both `Instrument`s and `ActorRef`s pointed are unique (actor-per-instrument).
Having `BiMap` I could simply `inverse()` the map (from `BiMap<Instrument, ActorRef>` to `BiMap<ActorRef, Instrument>` and treat `ActorRef` as key.

This Akka example is not more than "*hello, world*".
But compared to convoluted solution we would have to write using concurrent queues, locks and thread pools, it's perfect.
My team mates were so excited that by the end of the day they decided to rewrite their whole application to Akka.
