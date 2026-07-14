---
layout: post
title: Managing congested actors in Akka
date: '2013-07-17T18:51:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- akka
- scala
modified_time: '2013-07-17T18:51:48.636+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8076627398809277023
blogger_orig_url: https://www.nurkiewicz.com/2013/07/managing-congested-actors-in-akka.html
image:
  path: /assets/img/managing-congested-actors-in-akka/hero.jpg
  alt: "Hovedøya"
---

There comes a time in an Akka application when an actor can longer handle increasing load.
Since each actor can only handle one message at a time and it keeps a backlog of pending messages in a queue called [mailbox](http://doc.akka.io/docs/akka/2.2.0/scala/mailboxes.html), there is a risk of overloading one actor if too many messages are sent to one actor at the same time or actor fails to process messages fast enough - queue will keep growing and growing.
This will negatively impact responsiveness of the system and might even result in application crashing.

It’s actually very easy to simulate such load by simply sending continuous stream of messages to an actor as fast as possible:

```scala
case object Ping

class PingActor extends Actor {

    def receive = {
        case Ping => 
            //don't do this at home!
            Thread sleep 1
    }
}

object Main extends App {
    val system = ActorSystem("Heavy")
    val client = system.actorOf(Props[PingActor], "Ping")
    while(true) {
        client ! Ping
    }
}
```

Of course you should not sleep in actor, ever, this is just to stress the mailbox.
If you are (un)lucky and play a bit with the amount of sleep, your application will soon spend most of the time doing (fruitless) GC and you might see dreadful OOM errors:

```scala
Exception: java.lang.OutOfMemoryError thrown from the UncaughtExceptionHandler in thread "Heavy-akka.actor.default-dispatcher-6"
Exception: java.lang.OutOfMemoryError thrown from the UncaughtExceptionHandler in thread "Heavy-akka.actor.default-dispatcher-10"
```

…and finally die:

```scala
Uncaught error from thread [Heavy-akka.actor.default-dispatcher-7] shutting down JVM 
since 'akka.jvm-exit-on-fatal-error' is enabled for ActorSystem[Heavy]
java.lang.OutOfMemoryError: GC overhead limit exceeded
```

Today we will learn how to handle such congested actors so that sudden burst of traffic does not crash the whole application.

## Routing and load balancing

One simple solution to reducing load of one actor is spreading work across several copies of such actor.
Akka provides built in [routing and load balancing](http://doc.akka.io/docs/akka/2.2.0/scala/routing.html) actor that stands in front and manages several instances of our actor.
Router chooses (using configurable strategy) one of the underlying instances, therefore spreading load:

```scala
val props = Props[PingActor].
       withRouter(RoundRobinRouter(nrOfInstances = 10))
val client = system.actorOf(props, "Ping")
```

What we did is we asked Akka to put [Round Robin](http://en.wikipedia.org/wiki/Round-robin_scheduling) router in front of 10 independent instances of `PingActor` (instead of just one).
Theoretically this could cut latency by an order of magnitude.
So if routing is so effective, why not use it by default and transparently, like Enterprise Java Beans pooling?

To answer this question we need a bit more complex example.
`PingActor` is stateless thus it can be safely replicated behind a router.
But what about the following actor?

```scala
class StoreActor extends Actor {

    private var lastUsedId = 0

    def receive = {
        case Store(s) =>
            val id = nextUniqueId()
            slowStore(s, id)
            sender ! Done(id)
    }

    private def nextUniqueId() = {
        lastUsedId += 1
        lastUsedId
    }

    private def slowStore(s: String, id: Int) {
        //...
    }
}
```

Clearly `StoreActor` assumes there is only one instance of `lastUsedId` and since `receive` is never called concurrently, uniqueness of IDs is guaranteed.
We generate unique ID, store some message and send generated ID back to the client actor.

Unfortunately the moment we put any router in front of `StoreActor`, each copy of that actor has its own `lastUsedId` variable and duplicates are unavoidable.
Let’s rethink our design.
In order to generate unique IDs we must have just one copy of the counter and restrict access to it.
But storing is most likely thread-safe, thus can be parallelized.
The simples solution would be to use `StoreActor` companion object and [`AtomicInteger`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/atomic/AtomicInteger.html):

```scala
//DIRTY! Close your eyes!
object StoreActor {

    val lastUsedId = new AtomicInteger

}

class StoreActor extends Actor with ActorLogging {

    private def nextUniqueId() = StoreActor.lastUsedId.incrementAndGet()

    //...

}
```

Well… Honestly, shared mutable state is hardly what we’re after.
We should rather look into actor model more closely and extract ID generation logic to separate actor, promoting [*single responsibility principle*](http://en.wikipedia.org/wiki/Single_responsibility_principle) as a bonus:

```scala
case object GiveMeUniqueId

class UniqueIdActor extends Actor {

    private var lastUsedId = 0

    def receive = {
        case GiveMeUniqueId =>
            lastUsedId += 1
            sender ! lastUsedId
    }

}
```

Obviously all `StoreActor` instances behind router should share reference to one single instance of `UniqueIdActor`:

```scala
class StoreActor(uniqueIdActor: ActorRef) extends Actor {

    private implicit val timeout = Timeout(10 minutes)

    import context.dispatcher

    def receive = {
        case Store(s) =>
            uniqueIdActor ? GiveMeUniqueId map {
                case id: Int =>
                    slowStore(s, id)
                    Done(id)
            } pipeTo sender
    }

    private def slowStore(s: String, id: Int) {
        //...
    }
}
```

As you can see `uniqueIdActor` is passed to the actor constructor.
Obviously we should not create new `UniqueIdActor` in each `StoreActor` as that would produce 10 independent child copies rather than one centralized actor.
Here is a glue code:

```scala
val uniqueIdActor = system.actorOf(Props[UniqueIdActor], "UniqueId")
val props = Props(classOf[StoreActor], uniqueIdActor).
       withRouter(RoundRobinRouter(nrOfInstances = 10))
val client = system.actorOf(props, "Heavy")
```

## Software transactional memory

You might have a feeling that a separate actor to simply wrap one `Int` is an overkill.
On the other hand shared mutable `AtomicInteger` is far from Akka’s share-nothing spirit.
We can experiment with [software transactional memory in Akka](http://doc.akka.io/docs/akka/2.2.0/scala/stm.html) built on top of [ScalaSTM](http://nbronson.github.io/scala-stm/).
We will wrap mutable `Int` with transactional `Ref` and share this reference among all `StoreActor`s:

```scala
class StoreActor(counter: Ref[Int]) extends Actor {

    def receive = {
        case Store(s) =>
            val id = nextUniqueId()
            slowStore(s, id)
            sender ! Done(id)
    }

    private def nextUniqueId() = atomic {
        implicit tx =>
            counter += 1
            counter()
    }

    //...

}
```

This time all `StoreActor` instances share transactional `Ref[Int]`.
Calling `nextUniqueId()` increments `counter` within transaction, thus the code is thread-safe.
Much simpler architecture and synchronous `nextUniqueId()` are easier to read and maintain.
However shared data structure of any kind is problematic, especially when we try to scale out.
But just as an exercise try to replace STM with [agents](http://doc.akka.io/docs/akka/2.2.0/scala/agents.html).
Here is a starting glue code for STM:

```scala
import scala.concurrent.stm.Ref

val globalUniqueId = Ref(0)
val props = Props(classOf[StoreActor], globalUniqueId).
       withRouter(RoundRobinRouter(nrOfInstances = 10))
val client = system.actorOf(props, "Heavy")
```

In a perfect world distributing work between several actors can work.
But what if we *really* need just one, single instance and it can’t keep up with incoming messages?
In that case we should at least fail fast with

## Bounded mailbox

By default mailboxes are limited only by the amount of memory we have.
This means that one rogue actor can impact the whole system since each actor has a separate mailbox but they all share the same heap.
A simple solution is to limit the size of mailbox and simply discard everything above given threshold.
Luckily Akka supports [bounded mailboxes](http://doc.akka.io/docs/akka/2.2.0/scala/mailboxes.html) out-of-the-(mail)box.
In general, if we can’t cope with increasing load, we should at least fail fast rather than hanging forever.

```scala
class StoreActor extends Actor with RequiresMessageQueue[BoundedMessageQueueSemantics] {

    private var lastUniqueId = 0

    //...

}
```

Additionally you must configure queue capacity, either in code or in `application.conf`:

```text
bounded-mailbox {
    mailbox-type = "akka.dispatch.BoundedMailbox"
    mailbox-capacity = 1000
    mailbox-push-timeout-time = 100ms
}
```

With this configuration there is only one instance of `StoreActor` that can queue up to 1000 messages.
If more messages are sent they are discarded and forwarded to *Dead Letter Queue*, unless mailbox of `StoreActor` doesn’t shrink within 100 milliseconds.

## Summary

Keeping mailboxes short and actors fast is a key factor that impacts responsiveness and stability of Akka application.
By monitoring your system you should discover bottlenecks and either scale up/out or fail fast.
Otherwise your JVM will quickly start choking and loose momentum.
