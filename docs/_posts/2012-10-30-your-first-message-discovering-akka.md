---
layout: post
title: Your first message - discovering Akka
date: '2012-10-30T00:02:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- akka
- scala
modified_time: '2012-11-05T19:35:46.879+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-9180899552551171222
blogger_orig_url: https://www.nurkiewicz.com/2012/10/your-first-message-discovering-akka.html
image:
  path: /assets/img/your-first-message-discovering-akka/hero.jpg
  alt: "Holmenkollen seen from Grefsenkollen"
---

[Akka](http://akka.io/) is a platform (framework?)
inspired by Erlang, promising easier development of scalable, multi-threaded and safe applications.
While in most of the popular languages concurrency is based on memory shared between several threads, guarded by various synchronization mehods, Akka offers concurrency model based on actors.
Actor is a lightweight object which you can interact with barely by sending messages to it.
Each actor can process at most one message at a time and obviously can send messages to other actors.
Within one Java virtual machine millions of actors can exist at the same time, building a hierarchical parent (*supervisor*) - children structure, where parent monitors the behaviour of children.
If that's not enough, we can easily split our actors between several nodes in a cluster - without modifying a single line of code.
Each actor can have internal state (set of fields/variables), but communication can only occur through message passing, never through shared data structures (counters, queues).

A combination of the features above lead to a much safer, more stable and scalable code - for the price of a radical paradigm shift in concurrent programming model.
So many buzzwords and promises, let's go forward with an example.
And it's not going to be a "*Hello, world*" example, but we are going to try to build a small, but complete solution.
In the next few articles we will implement integration with [random.org API](http://www.random.org/clients/http/).
This web service allows us to fetch truly random numbers (as opposed to pseudo random generators) based on *atmospheric noise* (whatever that means).
API isn't really that complicated, please visit the following website and refresh it couple times:

<https://www.random.org/integers/?num=20&min=1000&max=10000&col=1&base=10&format=plain>

So where is the difficulty?
Reading [guidelines for automated clients](http://www.random.org/clients/) we learn that:

1.  The client application should call the URL above at most from one thread - it's forbidden to concurrently fetch random numbers using several HTTP connections.
2.  We should load random numbers in batches, not one by one in every request.
    The request above takes `num=20` numbers in one call.
3.  We are warned about latency, response may arrive even after one minute
4.  The client should periodically check random number quota (the service is free only up to a given number of random bits per day)

All these requirements make integration with `random.org` non-trivial.
In this series I have just begun we will gradually improve our application, learning new Akka features step by step.
We will soon realize that quite steep learning curve pays of quickly once we understand the basic concepts of the platform.
So, let's code!

Today we will try to handle first two requirements, that is not more than one connection at any given point in time and loading numbers in batches.
For this step we don't really need Akka, simple synchronization and a buffer is just about enough:

```scala
val buffer = new Queue[Int]

def nextRandom(): Int = {
  this.synchronized {
    if(buffer.isEmpty) {
      buffer ++= fetchRandomNumbers(50)
    }
    buffer.dequeue()
  }
}

def fetchRandomNumbers(count: Int) = {
  val url = new URL("https://www.random.org/integers/?num=" + count + "&min=0&max=65535&col=1&base=10&format=plain&rnd=new")
  val connection = url.openConnection()
  val stream = Source.fromInputStream(connection.getInputStream)
  val randomNumbers = stream.getLines().map(_.toInt).toList
  stream.close()
  randomNumbers
}
```

This code works and is equivalent to the `synchronized` keyword in Java.
The way `nextRandom()` works should be obvious: if the buffer is empty, fill it with 50 random numbers fetched from the server.
At the end take and return the first value from the buffer.
This code has several disadvantages, starting from the `synchronized` block on the first place.
Rather costly synchronization for each and every call seems like an overkill.
And we aren't even in the cluster yet, where we would have to maintain one active connection per whole cluster, not only withing one JVM!

We shall begin with implementing one actor.
Actor is basically a class extending `Actor` trait and implementing `receive` method.
This method is responsible for receiving and handling one message.
Let's reiterate what we already said: each and every actor can handle at most one message at a time, thus `receive` method is **never** called concurrently.
If the actor is already handling some message, the remaining messages are kept in a queue dedicated to each actor.
Thanks to this rigorous rule, we can avoid *any* synchronization inside actor, which is always thread-safe.

```scala
case object RandomRequest

class RandomOrgBuffer extends Actor {

  val buffer = new Queue[Int]

  def receive = {
    case RandomRequest =>
      if(buffer.isEmpty) {
        buffer ++= fetchRandomNumbers(50)
      }
      println(buffer.dequeue())
  }

}
```

`fetchRandomNumbers()` method remains the same.
Single-threaded access to `random.org` was achieved for free, since actor can only handle one message at a time.
Speaking of messages, in this case `RandomRequest` is our message - empty object not conveying any information except its type.
In Akka messages are almost always implemented using case classes or other immutable types.
Thus, if we would like to support fetching arbitrary number of random numbers, we would have to include that as part of the message:

```scala
case class RandomRequest(howMany: Int)

class RandomOrgBuffer extends Actor with ActorLogging {

  val buffer = new Queue[Int]

  def receive = {
    case RandomRequest(howMany) =>
      if(buffer.isEmpty) {
        buffer ++= fetchRandomNumbers(50)
      }
      for(_ <- 1 to (howMany min 50)) {
        println(buffer.dequeue())
      }
  }
```

Now we should try to send some message to our brand new actor.
Obviously we cannot just call `receive` method passing message as an argument.
First we have to start the Akka platform and ask for an actor reference.
This reference is later used to send a message using slightly counter-intuitive at first `!`
method, dating back to Erlang days:

```scala
object Bootstrap extends App {
  val system = ActorSystem("RandomOrgSystem")
  val randomOrgBuffer = system.actorOf(Props[RandomOrgBuffer], "buffer")

  randomOrgBuffer ! RandomRequest(10)  //sending a message

  system.shutdown()
}
```

After running the program we should see 10 random numbers on the console.
Experiment a little bit with that simple application (full source code is [available on GitHub](https://github.com/nurkiewicz/learning-akka), [`request-response` tag](https://github.com/nurkiewicz/learning-akka/commit/24b2f2ced653fadc391fbe50769b2b69e1b9a597)).
In particular notice that sending a message is non-blocking and the message itself is handled in a different thread (big analogy to JMS).
Try sending a message of different type and fix `receive` method so that it can handle more than one type.

Our application is not very useful by now.
We would like to access our random numbers somehow rather than printing them (asynchronously!)
to standard output.
As you can probably guess, since communication with an actor can only be established via asynchronous message passing (actor cannot "*return*" result, neither it shouldn't place it in any global, shared memory).
Thus an actor will send the results back via reply message sent directly to us (to sender).
But that will be part of the next article.

> This was a translation of my article ["*Poznajemy Akka: pierwszy komunikat*"](http://scala.net.pl/poznajemy-akka-pierwszy-komunikat/) originally published on [scala.net.pl](http://scala.net.pl/).
