---
layout: post
title: 'Request and response - discovering Akka '
date: '2012-10-31T19:52:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- akka
- scala
modified_time: '2012-11-05T19:35:52.440+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-226342276927572987
blogger_orig_url: https://www.nurkiewicz.com/2012/10/request-and-response-discovering-akka.html
image:
  path: /assets/img/request-and-response-discovering-akka/hero.jpg
  alt: "Holmenkollen seen from a roof in Nydalen"
---

In the previous part we [implemented our first actor](http://nurkiewicz.blogspot.no/2012/10/your-first-message-discovering-akka.html) and sent message to it.
Unfortunately actor was incapable of returning any result of processing this message, which rendered him rather useless.
In this episode we will learn how to send reply message to the sender and how to integrate synchronous, blocking API with (by definition) asynchronous system based on message passing.

Before we begin I must draw very strong distinction between an actor (extending [`Actor`](http://doc.akka.io/api/akka/2.0/akka/actor/Actor.html) trait) and an actor reference of [`ActorRef`](http://doc.akka.io/api/akka/2.0/akka/actor/ActorRef.html) type.
When implementing an actor we extend `Actor` trait which forces us to implement `receive` method.
However we do not create instances of actors directly, instead we ask `ActorSystem`:

```scala
val randomOrgBuffer: ActorRef = system.actorOf(Props[RandomOrgBuffer], "buffer")
```

To our great surprise returned object is not of `RandomOrgBuffer` type like our actor, it's not even an `Actor`.
Thanks to `ActorRef`, which is a *wrapper* (*proxy*) around an actor:

- internal state, i.e. fields, of an actor is inaccessible from outside (encapsulation)
- the Akka system makes sure that `receive` method of each actor processes at most one message at a time (single-threaded) and queues awaiting messages
- the actual actor can be deployed on a different machine in the cluster, `ActorRef` transparently and invisibly to the client sends messages over the wire to the correct node in the cluster (more on that later in the series).

That being said let's somehow "return" random numbers fetched inside our actor.
In turns out that inside every actor there is a method with very promising name `sender`.
It won't be a surprise if I say that it's an `ActorRef` pointing to an actor that sent the message which we are processing right now:

```scala
object Bootstrap extends App {
    //...
    randomOrgBuffer ! RandomRequest
    //...
}

//...

class RandomOrgBuffer extends Actor with ActorLogging {

    def receive = {
        case RandomRequest =>
            if(buffer.isEmpty) {
                buffer ++= fetchRandomNumbers(50)
            }
            sender ! buffer.dequeue()
    }
}
```

I hope you are already accustomed to `!`
notation used to send a message to an actor.
If not, there are more conservative alternatives:

```scala
sender tell buffer.dequeue()
sender.tell(buffer.dequeue())
```

Nevertheless instead of printing new random numbers on screen we send them back to the sender.
Quick test of our program reveals that...
nothing happens.
Looking closely at the `sender` reference we discover that it points to `Actor[akka://Akka/deadLetters]`.
`deadLetters` doesn't sound very well, but it's logical.
`sender` represents a reference to an actor that sent given message.
We have sent the message inside a normal Scala class, not from an actor.
If we were using two actors and the first one would have sent a message to the second one, then the second actor can use `sender` reference pointing to the first actor to send the reply back.
Obviously then we would still not be capable of receiving the reply, despite increasing the abstraction.

We will look at multi-actor scenarios soon, for the time being we have to learn how to integrate normal, non-Akka code with actors.
In other words how to receive a reply so that Akka is not only a black hole that receives messages and never sends any results back.
The solution is surprisingly simple - we can *wait* for a reply!

```scala
implicit val timeout = Timeout(1 minutes)

val future = randomOrgBuffer ? RandomRequest
val veryRandom: Int = Await.result(future.mapTo[Int], 1 minute)
```

The name `future` is not a coincidence.
Although it's not an instance of [`java.util.concurrent.Future`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Future.html), semantically it represents the exact same concept.
But first note that instead of exclamation mark we use question mark (`?`) to send a message.
This communication model is known as "*ask*" as opposed to already introduced "*tell*".
In essence Akka created a temporary actor named `Actor[akka://Akka/temp/$d]`, sent a message on behalf of that actor and now waits up to one minute for a reply sent back to aforementioned temporary actor.
Sending a message is still not-blocking and `future` object represents result of an operation that might not have been finished yet (it will be available in the *future*).
Next (now in blocking manner) we wait for a reply.
In addition `mapTo[Int]` is necessary since Akka does not know what type of response we expect.

You must remember that using the "*ask*" pattern and waiting/blocking for a reply is very rare.
Typically we rely on asynchronous messages and event driven architecture.
One actor should never block waiting for a reply from another actor.
But in this particular case we need a direct access to return value as we are building bridge between imperative request/response method and message-driven Akka system.
Having a reply, what interesting use-cases can we support?
For example we can design our own [`java.util.Random`](http://docs.oracle.com/javase/7/docs/api/java/util/Random.html) implementation based entirely on ideal, true random numbers!

```scala
class RandomOrgRandom(randomOrgBuffer: ActorRef) extends java.util.Random {
    implicit val timeout = Timeout(1 minutes)

    override def next(bits: Int) = {
        if(bits <= 16) {
            random16Bits() & ((1 << bits) - 1)
        } else {
            (next(bits - 16) << 16) + random16Bits()
        }
    }

    private def random16Bits(): Int = {
        val future = randomOrgBuffer ? RandomRequest
        Await.result(future.mapTo[Int], 1 minute)
    }
}
```

The implementation details are irrelevant, enough to say that we must implement the `next()` method returning requested number of random bits, whereas our actor always returns 16 bits.
The only thing we need now is a lightweight [`scala.util.Random`](http://www.scala-lang.org/api/current/scala/util/Random.html) wrapping `java.util.Random` and enjoy ideally shuffled sequence of numbers:

```scala
val javaRandom = new RandomOrgRandom(randomOrgBuffer)
val scalaRandom = new scala.util.Random(javaRandom)
println(scalaRandom.shuffle((1 to 20).toList))
//List(17, 15, 14, 6, 10, 2, 1, 9, 8, 3, 4, 16, 7, 18, 13, 11, 19, 5, 12, 20)
```

Let's wrap up.
First we developed a simple system based on one actor that (if necessary) connects to external web service and buffers a batch of random numbers.
When requested, it sends back one number from the buffer.
Next we integrated asynchronous world of actors with synchronous API.
By wrapping our actor we implemented our own `java.util.Random` implementation (see also [`java.security.SecureRandom`](http://docs.oracle.com/javase/7/docs/api/java/security/SecureRandom.html)).
This class can now be used in any place where we need random numbers of very high quality.
However the implementation is far from perfect, which we will address in next parts.

[Source code](https://github.com/nurkiewicz/learning-akka) is available on GitHub ([request-response tag](https://github.com/nurkiewicz/learning-akka/commit/24b2f2ced653fadc391fbe50769b2b69e1b9a597)).

> This was a translation of my article ["*Poznajemy Akka: żądanie i odpowiedź*"](http://scala.net.pl/poznajemy-akka-zadanie-i-odpowiedz/) originally published on [scala.net.pl](http://scala.net.pl/).
