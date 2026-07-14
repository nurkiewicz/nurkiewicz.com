---
layout: post
title: Futures in Akka with Scala
date: '2013-03-07T18:39:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- akka
- scala
- multithreading
modified_time: '2013-03-07T18:39:31.570+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8062284487960397370
blogger_orig_url: https://www.nurkiewicz.com/2013/03/futures-in-akka-with-scala.html
---

Akka is actor based, event-driven framework for building highly concurrent, reliable applications.
Shouldn't come a surprise that concept of a *future* is ubiquitous in a system like that.
You typically never block waiting for a response, instead you send a message and expect response to arrive some time in the future.
Sounds like great fit for...
futures.
Moreover futures in Akka are special for two reasons: Scala syntax together with type inference greatly improve readability and *monadic* nature.
To fully appreciate the latter advantage check out [*scala.Option Cheat Sheet*](http://blog.tmorris.net/posts/scalaoption-cheat-sheet/) if you haven't yet grasped monads in practice in Scala.

We will continue our [web crawler example](http://nurkiewicz.blogspot.no/2013/02/executorcompletionservice-in-practice.html) taking [yet another](http://nurkiewicz.blogspot.no/2013/02/listenablefuture-in-guava.html) approach, this time with Akka on top of Scala.
First the basic syntax:

```scala
val future = Future {
    Source.fromURL(
        new URL("http://www.example.com"), StandardCharsets.UTF_8.name()
    ).mkString
}
```

That was quick!
`future` is of [`scala.concurrent.Future[String]`](http://www.scala-lang.org/api/current/index.html#scala.concurrent.Future) inferred type.
Provided code block will be executed asynchronously later and `future` (of `Future[String]` type) represents a handle to the value of that block.
By now you should be wondering, how do you configure threads running this task?
Good question, this code won't compile as it stands, it needs [`ExecutionContext`](http://www.scala-lang.org/api/current/index.html#scala.concurrent.ExecutionContext) to work on.
`ExecutionContext` is just like [`ExecutorService`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/ExecutorService.html) but can be given implicitly.
You have several choices:

```scala
import ExecutionContext.Implicits.global

//or

implicit val ec = ExecutionContext.fromExecutorService(Executors.newFixedThreadPool(50))

//or (inside actor)

import context.dispatcher

//or (explicitly)

val future = Future {
    //...
} (ec)
```

First approach uses built in execution context composed of as many threads as many CPU/cores you have.
Use this context only for small applications as it doesn't scale well and is quite inflexible.
Second approach takes existing `ExecutorService` and wraps it.
You have full control over the number of threads and their behaviour.
Notice how `implicit val` is picked up automatically.
If you are inside an actor you can reuse Akka `dispatcher` to run your task using the same thread pool as actors use.
Finally you can of course pass `ExecutionContext` explicitly.
In next examples I assume some implicit context is available.

Having `Future` instance we would like to process the result.
I am not even mentioning about blocking and waiting for them synchronously (but examine [official documentation](http://doc.akka.io/docs/akka/2.1.1/scala/futures.html) if you *really* need it).
More in a spirit of [`ListenableFuture` from Guava](http://nurkiewicz.blogspot.no/2013/02/listenablefuture-in-guava.html) we will register some completion callbacks first:

```scala
Future {
    Source.fromURL(new URL("http://www.example.com"), StandardCharsets.UTF_8.name()).mkString
} onComplete {
    case Success(html) => logger.info("Result: " + html)
    case Failure(ex) => logger.error("Problem", ex)
}
```

This feels pretty much like `ListenableFuture` but with cleaner syntax.
However there are even more powerful tools in our box.
Remember, last time we had one synchronous method to parse downloaded HTML and a second, asynchronous method to compute *relevance* of the document (whatever that means):

```scala
def downloadPage(url: URL) = Future {
    Source.fromURL(url, StandardCharsets.UTF_8.name()).mkString
}

def parse(html: String): Document = //...

def calculateRelevance(doc: Document): Future[Double] = //...
```

Of course we can register `onComplete` callback but futures in Akka/Scala are monads, thus we can process the data as a sequence of chained, strongly typed transformations (explicit types preserved for clarity):

```scala

val htmlFuture:         Future[String]   = downloadPage(new URL("http://www.example.com"))
val documentFuture:     Future[Document] = htmlFuture map parse
val relevanceFuture:    Future[Double]   = documentFuture flatMap calculateRelevance
val bigRelevanceFuture: Future[Double]   = relevanceFuture filter {_ > 0.5}
bigRelevanceFuture foreach println
```

I want to be clear here.
Calling `Future.map(someOperation)` does not wait for that future to complete.
It simply wraps it and runs `someOperation` the moment it completes, some time in the, *ekhem*, future.
The same applies to `Future.filter` and `Future.foreach`.
You might be surprised to see them in this context as we typically associate such operators with collections.
But just as with `Option[T]`, `Future[T]` is, greatly oversimplifying, a collection that may or may not contain exactly one element.
With this comparison it should be obvious what the code above does.
`Future.filter` invocation might not be clear but it basically specifies that we are not interested in the result of asynchronous operation that does not meet certain criteria.
If the predicate yields `false`, `foreach` operation will never be executed.

Of course you can take advantage of type inference and chaining to get more concise, but not necessarily easier to read code:

```scala
downloadPage(new URL("http://www.example.com")).
    map(parse).
    flatMap(calculateRelevance).
    filter(_ > 0.5).
    foreach(println)
```

But the biggest win comes from for-comprehensions.
You might not be aware of that, but because `Future` implements `map`, `foreach`, `filter` and such (simplifying), we can use it inside for comprehension (same applies to `Option[T]`).
So yet another, arguably most readable approach would be:

```scala
for {
    html <- downloadPage(new URL("http://www.example.com"))
    relevance <- calculateRelevance(parse(html))
    if(relevance > 0.5)
} println(relevance)

println("Done")
```

It feels very imperative and sequential but in fact each step of this for comprehension is executed asynchronously and there is no blocking here.
`"Done"` message will be displayed immediately, long before the computed relevance.
This construct brings best of both worlds - looks sequential but in fact runs in background.
Moreover it hides the obscure difference between functions returning value vs. `Future` of value (`map` vs. `flatMap`).

Say we run code above for a list of web sites which gives us `List[Future[Double]]` and now we want to find the biggest relevance in that set.
By now you should refuse all solutions involving blocking.
There are two clever ways to do this in Scala - either by turning a `List[Future[Double]]` to `Future[List[Double]]` or by folding over a list of futures.
The first solutions is identical to [`Futures.allAsList` in Guava](http://nurkiewicz.blogspot.no/2013/02/advanced-listenablefuture-capabilities.html):

```scala
val futures: Seq[Future[Double]] = //...
val future: Future[Seq[Double]] = Future sequence futures
future.onSuccess{
    case x => println(s"Max relevance: ${x.max}")
}
```

or even more concisely (remember that `x` is a `Seq[Double]` in both cases:

```scala
Future.sequence(futures).map {x =>
    println(s"Max relevance: ${x.max}")
}
```

Remember that there is no blocking here.
`Future[Seq[Double]]` completes when last underlying `Future[Double]` reports completion.
If you like `foldLeft()` just like [I do](http://nurkiewicz.blogspot.no/2012/04/secret-powers-of-foldleft-in-scala.html) (but not necessarily here) consider the following idiom:

```scala
Future.fold(futures)(0.0) {_ max _} map {maxRel =>
    println(s"Max relevance: $maxRel")
}
```

This ones iterates over futures one-by-one and invokes our supplied `{_ max _}` fold function whenever given future succeeds.

## Summary

Futures in Scala and Akka are very powerful: they allow non-blocking, CPU-effective asynchronous programming but they feel like imperative, single-threaded programming.
You can apply sequence of transformations on top of a single future or a collection of them just as if that future was already resolved.
Code looks totally imperative where you wait for one stage, run some transformation and run second stage.
But in reality everything is asynchronous and event driven.
Due to monadic nature of `Future[V]` and concise syntax, futures in Scala are a wonderful tool without introducing too much ceremony.
