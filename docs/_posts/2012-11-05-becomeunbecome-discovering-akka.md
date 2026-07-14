---
layout: post
title: become/unbecome - discovering Akka
date: '2012-11-05T19:43:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- akka
- scala
modified_time: '2012-11-05T21:33:40.651+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3263728146289045454
blogger_orig_url: https://www.nurkiewicz.com/2012/11/becomeunbecome-discovering-akka.html
image:
  path: /assets/img/becomeunbecome-discovering-akka/hero.jpg
  alt: "Oslo seen from Hovedøya island"
---

Sometimes our actor needs to react differently based on its internal state.
Typically receiving some specific message causes the state transition which, in turns, changes the way subsequent messages should be handled.
Another message restores the original state and thus - the way messages were handled before.
[In the previous article](http://nurkiewicz.blogspot.no/2012/11/two-actors-discovering-akka.html) we implemented `RandomOrgBuffer` actor based on `waitingForResponse` flag.
It unnecessarily complicated already complex message handling logic:

```scala
var waitingForResponse = false

def receive = {
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

private def preFetchIfAlmostEmpty() {
    if(buffer.size <= BatchSize / 4 && !waitingForResponse) {
        randomOrgClient ! FetchFromRandomOrg(BatchSize)
        waitingForResponse = true
    }
}
```

Wouldn't it be simpler to have two distinct `receive` methods - one used when we are awaiting for external server response (`waitingForResponse == true`) and the other when buffer is filled sufficiently and no request to `random.org` was yet issued?
In such circumstances `become()` and `unbecome()` methods come very handy.
By default `receive` method is used to handle all incoming messages.
However at any time we can call `become()`, which accept any method compliant with `receive` signature as an argument.
Every subsequent message will be handled by this new method.
Calling `unbecome()` restores original `receive` method.
Knowing this technique we can refactor our solution above to the following:

```scala
def receive = {
    case RandomRequest =>
        preFetchIfAlmostEmpty()
        handleOrQueueInBacklog()
    }

def receiveWhenWaiting = {
    case RandomRequest =>
        handleOrQueueInBacklog()
    case RandomOrgServerResponse(randomNumbers) =>
        buffer ++= randomNumbers
        context.unbecome()
        while(!backlog.isEmpty && !buffer.isEmpty) {
            backlog.dequeue() ! buffer.dequeue()
        }
        preFetchIfAlmostEmpty()
}

private def handleOrQueueInBacklog() {
    if (buffer.isEmpty) {
        backlog += sender
    } else {
        sender ! buffer.dequeue()
    }
}

private def preFetchIfAlmostEmpty() {
    if(buffer.size <= BatchSize / 4) {
        randomOrgClient ! FetchFromRandomOrg(BatchSize)
        context become receiveWhenWaiting
    }
}
```

We extracted code responsible for handling message while we wait for `random.org` response into a separate `receiveWhenWaiting` method.
Notice the `become()` and `unbecome()` calls - they replaced no longer needed `waitingForResponse` flag.
Instead we simply say: starting from next message please use this other method to handle (*become* slightly different actor).
Later we say: OK, let's go back to the original state and receive messages as you used to (*unbecome*).
But the most important change is the transition from one, big method into two, much smaller a better named ones.
`become()` and `unbecome()` methods are actually much more powerful since they internally maintain a *stack* of receiving methods.
Every call to `become()` (with `discardOld = false` as a second parameter) pushes current receiving method onto a stack while `unbecome()` pops it and restores the previous one.
Thus we can use `become()` to use several receiving methods and then gradually go back through all the changes.
Moreover Akka also supports [*finite state machine*](http://doc.akka.io/docs/akka/snapshot/scala/fsm.html) pattern, but more on that maybe in the future.
Source code for this article is [available on GitHub](https://github.com/nurkiewicz/learning-akka) in [`become-unbecome` tag](https://github.com/nurkiewicz/learning-akka/tree/become-unbecome).

> This was a translation of my article ["*Poznajemy Akka: become/unbecome*"](http://scala.net.pl/poznajemy-akka-become-unbecome/) originally published on [scala.net.pl](http://scala.net.pl/).
