---
layout: post
title: Two actors - discovering Akka
date: '2012-11-02T20:29:00.001+01:00'
author: Tomasz Nurkiewicz
tags:
- akka
- scala
modified_time: '2012-11-05T19:35:30.355+01:00'
thumbnail: /assets/img/two-actors-discovering-akka/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-6026192191987177973
blogger_orig_url: https://www.nurkiewicz.com/2012/11/two-actors-discovering-akka.html
---

Hope you are having fun so far, but our application has serious performance defect.
After measuring response times of the [`RandomOrgRandom` class we developed in the previous part](http://nurkiewicz.blogspot.no/2012/10/request-and-response-discovering-akka.html) we will notice something really disturbing (the chart represents response times of subsequent invocations in milliseconds):

[![](/assets/img/two-actors-discovering-akka/1.png)](/assets/img/two-actors-discovering-akka/1.png)

[
](/assets/img/two-actors-discovering-akka/2.png)

In turns out that regularly response time (time to return one random number) is greater by several orders of magnitude (logarithmic scale!)
Remembering how the actor was implemented the reason is quite obvious: our actor fetches eagerly 50 random numbers and fills the buffer, returning one number after another.
If the buffer is empty, actor performs blocking I/O call to `random.org` web service which takes around half of a second.
This is clearly visible on the chart - every 50th invocation is much, much slower.
In some circumstances such behaviour would be acceptable (just like unpredictable garbage collection can increase latency of a response once in a while).
But still let's try to improve our implementation.

Do you have any idea how we can make response times more predictable and *flat*?
I suggest monitoring the buffer size and when it becomes dangerously close to being empty, we initiate fetching random numbers in background.
We hope that thanks to this architectural change will never be completely empty as the background response will arrive before we hit the bottom.
However, we are not forced to eagerly fetch too many random numbers.
Do you remember the original naive implementation using Java synchronization?
It had the same problem as our current system with just one actor.
But now we will finally see the true power of actor-based Akka system.
To implement the improvement suggested above we would need background thread to fetch numbers and some method of synchronization on the buffer (as it would be accessed concurrently.

In Akka each actor is logically single-threaded, thus we are not bothered by synchronization.
First we will [divide responsibilities](http://en.wikipedia.org/wiki/Single_responsibility_principle): one actor (`RandomOrgBuffer`) will hold the buffer of random numbers and return them when requested.
Second actor (`RandomOrgClient`) will barely be responsible for fetching new batches of random numbers.
When `RandomOrgBuffer` discovers low buffer level, it asks `RandomOrgClient` (by sending a message) to start fetching new random numbers.
Finally when `RandomOrgClient` receives a response from the `random.org` server, it sends new batch of random numbers to `RandomOrgBuffer` (of course using a reply message again).
`RandomOrgBuffer` fills the buffer with new numbers.

Let's start from the second actor, responsible for the communication with `random.org` web service in the background.
This actor initiates HTTP request when it receives `FetchFromRandomOrg` message - message holding the desired batch size to fetch.
When the response arrives, we parse it and send the whole batch back to the sender (`RandomOrgBuffer` in this case).
This code is quite similar to what we have already seen in `fetchRandomNumbers()`:

```scala
case class FetchFromRandomOrg(batchSize: Int)

case class RandomOrgServerResponse(randomNumbers: List[Int])

class RandomOrgClient extends Actor {
  protected def receive = LoggingReceive {
    case FetchFromRandomOrg(batchSize) =>
      val url = new URL("https://www.random.org/integers/?num=" + batchSize + "&min=0&max=65535&col=1&base=10&format=plain&rnd=new")
      val connection = url.openConnection()
      val stream = Source.fromInputStream(connection.getInputStream)
      sender ! RandomOrgServerResponse(stream.getLines().map(_.toInt).toList)
      stream.close()
    }
  }
```

Now it's time for the actual actor handling requests from potentially multiple clients asking for single random numbers.
Unfortunately the logic becomes quite complicated (but at least we don't have to worry about synchronization and thread-safety).
First of all `RandomOrgBuffer` must now handle two different messages: `RandomRequest` as before coming from client code and new `RandomOrgServerResponse` (see code above) containing batch of new random numbers sent from `RandomOrgClient`.
Secondly `RandomOrgBuffer` must remember that it initiated the process of fetching new random codes by sending `FetchFromRandomOrg`.
Otherwise we risk starting multiple concurrent connections to `random.org` or piling them up unnecessarily.

```scala
class RandomOrgBuffer extends Actor with ActorLogging {

  val BatchSize = 50

  val buffer = new Queue[Int]
  var waitingForResponse = false

  val randomOrgClient = context.actorOf(Props[RandomOrgClient], name="client")
  preFetchIfAlmostEmpty()

  def receive = {
    case RandomRequest =>
      preFetchIfAlmostEmpty()
      sender ! buffer.dequeue()
    case RandomOrgServerResponse(randomNumbers) =>
      buffer ++= randomNumbers
      waitingForResponse = false
  }

  private def preFetchIfAlmostEmpty() {
    if(buffer.size <= BatchSize / 4 && !waitingForResponse) {
      randomOrgClient ! FetchFromRandomOrg(BatchSize)
      waitingForResponse = true
    }
  }

}
```

The key part is `preFetchIfAlmostEmpty()` method that initiates the process of fetching random numbers (in background, by a different actor).
If the buffer level is too low (I assume 1/4 of the batch size) and we are not already waiting for a response from `random.org`, we send appropriate message to `RandomOrgClient`.
We also call this method immediately on startup (when the buffer is completely empty) in order to have warmed up buffer when first request arrives.
Notice how one actor can **create** an instance of another actor by calling `context.actorOf` (actually it's an `ActorRef`).

This code contains tremendous bug, can you spot it?
Imagine what will happen if suddenly `RandomOrgBuffer` receives hundreds of `RandomRequest` messages at the same time?
More than the buffer size, even immediately after filling it up?
Or if the request comes straight after the actor instantiation, when the buffer is still empty?
Unfortunately me must handle the situation when `RandomRequest` arrives and our buffer is completely empty while the `random.org` response didn't came back yet.
However we cannot simply block, waiting until the response with new random numbers batch arrives.
We cannot do this from one simple reason: if we are sleeping or waiting in other way while handling `RandomRequest`, we cannot handle any other message, including `RandomOrgServerResponse` - remember that one actor can handle only one message at a time!
Not only we would introduce dead-lock in our application, but also break one of the most important rules in Akka: never block or sleep inside an actor - more on that in next articles.

Correct way of handling this situation is to have a queue of awaiting actors - which sent us `RandomRequest` but we were incapable of sending a reply immediately due to an empty buffer.
As soon as we get `RandomOrgServerResponse` back, our priority is to handle these awaiting actors and then focus on subsequent requests in real time.
There is an interesting edge case - if the number of awaiting actors was so big that after fulfilling their requests the buffer is almost empty again, we send `FetchFromRandomOrg` immediately one more time.
It can get even more interesting - imagine the buffer is empty and we still haven't satisfied all pending actors.
The following code handles all these twists:

```scala
class RandomOrgBuffer extends Actor with ActorLogging {

  val BatchSize = 50

  val buffer = new Queue[Int]
  val backlog = new Queue[ActorRef]
  var waitingForResponse = false

  //...

  def receive = LoggingReceive {
    case RandomRequest =>
      preFetchIfAlmostEmpty()
      if(buffer.isEmpty) {
        backlog += sender
      } else {
        sender ! buffer.dequeue()
      }
    case RandomOrgServerResponse(randomNumbers) =>
      buffer ++= randomNumbers
      waitingForResponse = false
      while(!backlog.isEmpty && !buffer.isEmpty) {
        backlog.dequeue() ! buffer.dequeue()
      }
      preFetchIfAlmostEmpty()
  }

}
```

In our final version the `backlog` queue represents pending actors.
Notice how `RandomOrgServerResponse` is handled: if first tries to satisfy as many pending actors as possible.
Obviously our goal was to eliminate extremely big response times so we should strive to minimal `backlog` queue usage as every actor placed there is more likely to wait longer.
In ideal world `backlog` queue is always empty and the `RandomOrgBuffer` adjusts the batch size requested each time depending on current load (fetching smaller or bigger batches as well as adjusting the threshold below which buffer is considered almost empty).
But I'll leave these improvements to you.
Finally we can measure `RandomOrgBuffer` response times (linear scale, latencies are no longer so unevenly distributed):

[![](/assets/img/two-actors-discovering-akka/2.png)](/assets/img/two-actors-discovering-akka/2.png)

Handling of incoming messages in `RandomOrgBuffer` became quite complex.
I'm especially worried about the `waitingForResponse` flag (I hate flags!)
In the next article we will learn how to deal with this in very clear, idiomatic and object-oriented way.

> This was a translation of my article ["*Poznajemy Akka: dwóch aktorów*"](http://scala.net.pl/poznajemy-akka-dwoch-aktorow/) originally published on [scala.net.pl](http://scala.net.pl/).
