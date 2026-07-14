---
layout: post
title: Playing with Scala futures
date: '2013-12-15T22:37:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- scala
- concurrency
modified_time: '2013-12-22T20:26:09.668+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1756823750730610764
blogger_orig_url: https://www.nurkiewicz.com/2013/12/playing-with-scala-futures.html
image:
  path: /assets/img/playing-with-scala-futures/hero.jpg
  alt: "View from Kolsåstoppen"
---

During job interviews we often give Scala developers a simple design task: to model a binary tree.
The simplest but not necessarily best implementation involves `Option` idiom:

```scala
case class Tree[+T](value: T, left: Option[Tree[T]], right: Option[Tree[T]])
```

Bonus points for immutability, using `case` class and covariance.
Much better but more complex implementation involves two `case` classes but at least allows modelling empty trees:

```scala
sealed trait Tree[+T]
case object Empty extends Tree[Nothing]
case class Node[+T](value: T, left: Tree[T], right: Tree[T]) extends Tree[T]
```

Let's stick to the first idea.
Now implement building a tree with arbitrary height:

```scala
def apply[T](n: Int)(block: => T): Tree[T] = n match {
    case 1 => Tree(block, None, None)
    case _ =>
        Tree(
            block,
            Some(Tree(n - 1)(block)),
            Some(Tree(n - 1)(block))
        )
}
```

In order to build a tree with 1024 leaves and all random variable it's enough to say:

```scala
val randomTree: Tree[Double] = Tree(1 + 10)(math.random)
```

This is an open-ended question, next requirement may be to write a `map` method equivalent to `Seq.map()` or `Option.map()`.
Understanding what that means is part of the question.
The implementation is surprisingly straightforward:

```scala
case class Tree[+T](value: T, left: Option[Tree[T]], right: Option[Tree[T]]) = {

def map[R](f: T => R): Tree[R] =
    Tree(
        f(value), 
         left.map{_.map(f)}, 
        right.map{_.map(f)})    
}
```

OK...
`.map{_.map(f)}`, are you kidding me?
Remember that `left` and `right` are `Option`s and `Option.map(f)` turns `Option[T]` to `Option[R]`.
So first `map` comes from an `Option`.
Second `_.map(f)` is actually a recursive call to `Tree.map()`.
Now we can for example create a second tree (immutability!)
with every value incremented but preserving structure:

```scala
val tree: Tree[Int] = //...
val incremented = tree.map(1 +)
```

...or with `toString()` called on each value:

```scala
val stringified = tree.map(_.toString) 
```

Let' go a bit further.
If `f` function is time-consuming and side-effect free (which happens to be a frequent requirement when doing `map()`) or our tree is considerably big what about parallelizing `Tree.map()` in some way?
There are few ways to achieve this and quite a few traps.
The simplest approach is to use a thread pool backed by `ExecutionContext`:

```scala
case class Tree[+T](value: T, left: Option[Tree[T]], right: Option[Tree[T]]) {
    def pmap[R](f: T => R)(implicit ec: ExecutionContext, timeout: Duration): Tree[R] = {
        val transformed: Future[R] = Future { f(value)}
        val  leftFuture: Option[Future[Tree[R]]] =  left.map { l => Future { l.pmap(f)}}
        val rightFuture: Option[Future[Tree[R]]] = right.map { r => Future { r.pmap(f)}}

        Tree(
            Await.result(transformed, timeout),
             leftFuture.map(Await.result(_, timeout)),
            rightFuture.map(Await.result(_, timeout)))
    }
}
```

Using `pmap` (name is not a [coincidence](http://clojuredocs.org/clojure_core/clojure.core/pmap)) is quite simple once you sort out few `implicits`:

```scala
import scala.concurrent.{Await, Future, ExecutionContext}
import java.util.concurrent.Executors
import scala.concurrent.duration._

val pool = Executors newFixedThreadPool 10
implicit val ec: ExecutionContext = ExecutionContext fromExecutor pool
implicit val timeout = 10.second

val tree = Tree("alpha",
    None,
    Some(
        Tree("beta",
            None,
            None)))

println(tree.pmap{_.toUpperCase})
```

Sample code above will take a simple tree with "*alpha*" root and "*beta*" right child and upper case all the values in multiple threads.
Calling `Future { ... }` is a simple idiom to submit asynchronous task to a thread pool and get a `Future[T]` in return.

There are at least couple of issues with this code.
First of all it mainly...
waits.
Several threads will sit idle merely waiting for children to complete.
But that's not the worst case scenario.
Imagine our thread pool is limited to one thread (problem remains for larger, but still limited pools).
We spawn sub tasks for children and wait until they finish.
But these sub tasks never start because they are unable to obtain thread from a thread pool.
Why?
Because there is only one thread in the pool and we are already consuming it!
This one and only thread is blocked waiting idle for tasks that can never finish.
It's called a **deadlock**.
Actually the code will time out after given amount of time but it doesn't change the fact that the implementation above fails miserably.
`ForkJoinPool` would solve this issue but there are more advanced and rewarding solutions.

## Entering `Tree[Future[R]]`

Surprisingly there is even better, more functional and clean approach.
Reactive programming discourages waiting.
Instead of hiding asynchronous nature of processing tree, let's emphasize it!
Since the processing is already based on `Future`s, place them explicitly in the API:

```scala
case class Tree[+T](value: T, left: Option[Tree[T]], right: Option[Tree[T]]) {
    def mapf[R](f: T => R)(implicit ec: ExecutionContext, timeout: Duration): Tree[Future[R]] = {
        Tree(
            Future { f(value) },
             left.map {_.mapf(f)},
            right.map {_.mapf(f)}
        )
    }
}
```

`Tree.mapf()` returns immediately but instead of returning `Tree[R]` we now get `Tree[Future[R]]`.
So we have a tree where each node contains an independent `Future`.
How can we go back to familiar `Tree[R]`?
One approach uses `Tree.map()`, which we already implemented:

```scala
val treeOfFutures: Tree[Future[R]] = ...

val tree = treeOfFutures.map(Await.result(_, 10.seconds))
```

I bet it's not clear but in principle this is simple - for each node wait on independent future object until all of them are resolved.
There is no risk of deadlock because futures are not dependant on each other.

# Turning `Tree[Future[R]]` into `Future[Tree[R]]`

But we want to go deeper.
Why work with a bunch of futures if we can have only *one future to rule them all*?
Think about [`Future.sequence()`](http://www.scala-lang.org/api/current/index.html#scala.concurrent.Future$) that turns `Seq[Future[T]]` into `Future[Seq[T]]`.
Implementing such method for `Tree[Future[T]]` is a nice task on its own.
The idea is to have a counter of all unresolved tasks and once all of them are done - dereference all futures without blocking (since they are already finished):

```scala
object Tree {

    def sequence[T](tree: Tree[Future[T]])(implicit ec: ExecutionContext, timeout: Duration): Future[Tree[T]] = {
        val promise = Promise[Tree[T]]()
        val pending = new AtomicInteger(tree.size)
        for {
            future <- tree
            value <- future
        } if(pending.decrementAndGet() == 0) {
            promise.success(
                tree.map(Await.result(_, 0.seconds))    //will never block
            )
        }
        promise.future
    }
}
```

Code above is a bit imperative and doesn't handle exceptions properly - but can be a good starting point.
We iterate over all futures and decrement a counter after each one of them completes.
If all futures are done we complete our custom promise.
Code above requires two extra methods: `Tree.size` and `Tree.foreach()` (used implicitly inside for comprehension) - which I leave for you as an exercise.
