---
layout: post
title: Lazy sequences in Scala and Clojure
date: '2013-05-04T11:53:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- clojure
- scala
modified_time: '2013-05-04T11:53:04.458+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2890020890886760312
blogger_orig_url: https://www.nurkiewicz.com/2013/05/lazy-sequences-in-scala-and-clojure.html
---

*Lazy sequences* (also known as *streams*) are an interesting functional data structure which you might have never heard of.
Basically lazy sequence is a list that is not fully known/computed until you actually use it.
Imagine a list that is very expensive to create and you don't want to compute too much - but still allow clients to consume as much as they want or need.
Similar to iterator, however iterators are destructive - once you read them, they're gone.
Lazy sequences on the other hand remember already computed elements.

Notice that this abstraction even allows us to construct and work with *infinite* streams!
It's perfectly possible to create a lazy sequence of prime numbers or [Fibonacci series](http://en.wikipedia.org/wiki/Fibonacci_number).
It's up to the client to decide how many elements they want to consume - and only that many are going to be generated.
Compare it to eager list - that has to be precomputed prior to first usage and iterator - that forgets about already computed values.

Remember however that lazy sequences are always traversed from the beginning so in order to find Nth element lazy sequence will have to compute preceding N-1 elements.

I try to avoid purely academic examples thus there will be no Fibonacci series example.
You will find it in every article on the subject.
Instead we will implement something useful - [Cron expression](http://en.wikipedia.org/wiki/Cron) testing utility, returning a sequence of next fire times.
We already [implemented testing Cron expressions](http://nurkiewicz.blogspot.no/2012/10/testing-quartz-cron-expressions.html) before, using recursion and iterator.
To quickly recap, we would like to make sure that our Cron expression is correct and fires when we really expect it.
[Quartz scheduler](http://www.quartz-scheduler.org/) provides convenient [`CronExpression.getNextValidTimeAfter(Date)`](http://quartz-scheduler.org/api/2.1.7/org/quartz/CronExpression.html#getNextValidTimeAfter(java.util.Date)) method that returns next fire time after given date.
If we want to compute e.g. next ten fire times, we need to call this method ten times, but!
The result of first invocation should be passed as an argument to the second invocation - after all once we know when the job will fire the first time, we want to know what is the fire time of the next invocation (after the first one).
And continuing, in order to find third invocation time we must pass second invocation time as an argument.
This description led us to simple recursive algorithm:

```scala
def findTriggerTimesRecursive(expr: CronExpression, after: Date): List[Date] =
    expr getNextValidTimeAfter after match {
        case null => Nil
        case next => next :: findTriggerTimesRecursive(expr, next)
    }
```

`getNextValidTimeAfter()` may return `null` to indicate that Cron expression will never fire again (e.g.
it only runs during 2013 and we already reached the end of year).
However this solution has multiple issues:

- we don't really know how many future dates client needs so we most likely generate too much, unnecessarily consuming CPU cycles<sup>1</sup>
- even worse, some Cron expressions never end.
  `"0 0 17 * * ? *"` will run at 5 PM every day, every year, to infinity.
  We definitely don't have that much time and memory
- our implementation is not tail-recursive.
  Easy to fix though

What if we had a "list-like" data structure that we could pass around and work with it just like with any other sequence, but without eagerly evaluating it?
Here is an implementation in Scala of `Stream[Date]` that computes next fire times only when needed:

```scala
def findTriggerTimes(expr: CronExpression, after: Date): Stream[Date] =
    expr getNextValidTimeAfter after match {
        case null => Stream.Empty
        case next => next #:: findTriggerTimes(expr, next)
    }
```

Look carefully as it's almost identical!
We replaced `List[Date]` with `Stream[Date]` (both implement [`LinearSeq`](http://www.scala-lang.org/api/current/index.html#scala.collection.LinearSeq)), `Nil` with `Stream.Empty` and `::` with `#::`.
Last change is crucial.
`#::` method (yes, it's a method...)
accepts `tl: => Stream[A]` - *by name*.
It means the `findTriggerTimes(expr, next)` is not really called here!
It is actually a closure that we pass to `#::` higher order function.
This closure is evaluated only if needed.
Let's play a bit with this code:

```scala
val triggerTimesStream = findTriggerTimes("0 0 17 L-3W 6-9 ? *")

println(triggerTimesStream)
//Stream(Thu Jun 27 17:00:00 CEST 2013, ?)

val firstThree = triggerTimesStream take 3
println(firstThree.toList)
//List(Thu Jun 27 17:00:00 CEST 2013, Mon Jul 29 17:00:00 CEST 2013, Wed Aug 28 17:00:00 CEST 2013)

println(triggerTimesStream)
//Stream(Thu Jun 27 17:00:00 CEST 2013, Mon Jul 29 17:00:00 CEST 2013, Wed Aug 28 17:00:00 CEST 2013, ?)
```

Look carefully.
Initially printing the stream barely shows the first element.
Question mark in `Stream.toString` represents unknown remaining part of the stream.
Then we take first three elements.
Interestingly we have to transform the result to `List`.
Invoking `take(3)` alone barely returns another stream, further postponing evaluation as long as possible.
But printing the original stream again shows all three elements as well, but the forth one is not known yet.

Let's do something more advanced.
Say we would like to find out when will the Cron expression fire for the 100th time?
And how many times will it fire within one year from today?

```scala
val hundredth = triggerTimesStream.drop(99).head

val calendar = new GregorianCalendar()
calendar.add(Calendar.YEAR, 1)
val yearFromNow = calendar.getTime

val countWithinYear = triggerTimesStream.takeWhile(_ before yearFromNow).size
```

Computing 100th fire time is pretty straightforward - simply discard first 99 dates and take the first one of what's left.
However the word *discard* is a bit unfortunate - these items are computed and cached in `triggerTimesStream` so the next time we try to access any of the first 100 elements, they are available immediately.
Interesting fact: [`Stream[T]`](http://www.scala-lang.org/api/current/index.html#scala.collection.immutable.Stream) in Scala is immutable and thread-safe but it keeps changing internally while you iterate over it.
But this is an implementation detail.

You may be wondering why I use `takeWhile(...).size` instead of simple `filter(...).size` or even `count(...)`?
Well, from the definition fire times in our stream are growing so if we only want to count dates within one year, the moment we find first non-matching date we can stop.
But it's not only a micro-optimization.
Remember that streams can be infinite?
Think about it.
In the meantime we will port our small utility to Clojure.

# Clojure

the stream (`lazy-seq`) in Clojure:

```clojure
(defn find-trigger-times [expr after]
    (let [next (. expr getNextValidTimeAfter after)] 
        (case next
            nil []
            (cons next (lazy-seq (find-trigger-times expr next))))))
```

This is almost exact translation of Scala code, except it uses one `let` binding to capture `getNextValidTimeAfter()` result.
Less literate but more compact translation can be crafted with `if-let` form:

```clojure
(defn find-trigger-times [expr after]
    (if-let [next (. expr getNextValidTimeAfter after)] 
        (cons next (lazy-seq (find-trigger-times expr next)))
        []))
```

`if-let` combines condition and binding.
If expression bound to `next` is false (or `nil` in our case), 3rd line is not evaluated at all.
Instead the result of fourth line (empty sequence) is returned.
These two implementations are equivalent.
For completeness let us see how to grab 100th element and count number of dates matching Cron expression within one year:

```clojure
(def expr (new CronExpression "0 0 17 L-3W 6-9 ? *"))
(def trigger-times (find-trigger-times expr (new Date)))

(def hundredth (first (drop 99 trigger-times)))

(def year-from-now (let [calendar (new GregorianCalendar)] 
    (. calendar add Calendar/YEAR 1)
    (. calendar getTime)))

(take-while #(.before % year-from-now) trigger-times)
```

Notice that, again, we use `take-while` instead of simple `filter`

# Space and time complexity

Imagine using `filter()` instead of `takeWhile()` to calculate how many times Cron trigger will fire within next year.
Remember that streams in general (and our Cron stream in particular) can be infinite.
Simple `filter()` on a `Stream` will run until it reaches end - which may never happen with infinite stream.
The same applies to even such simple methods like `size` - `Stream` will keep evaluating more and more until it reaches the end.
But sooner your program will fill in whole heap space.
Why?
Because once element is evaluated, `Stream[T]` will cache it for later.

Accidentally holding head of a large `Stream` is another danger:

```scala
val largeStream: Stream[Int] = //,..
//...
val smallerStream = largeStream drop 1000000
```

`smallerStream` is a reference to a stream without first million elements.
But these elements are still cached in original `largeStream`.
As long as you keep a reference to it, they are kept in memory.
The moment `largeStream` reference goes out of scope, first million elements are eligible for garbage collection, while the remaining part of the stream is still referenced.

The discussion above applies equally well to Scala and Clojure.
As you can see you have to be really careful when working with lazy sequences.
They are very powerful and ubiquitous in functional languages - but ["*With great power, comes great responsibility*"](http://en.wikiquote.org/wiki/Stan_Lee).
The moment you start playing with possibly infinite entities, you have to be careful.

# `iterate`

If you are more experienced with Clojure or Scala you might be wondering why I haven't used [`(iterate f x)`](http://clojuredocs.org/clojure_core/clojure.core/iterate) or [`Stream.iterate()`](http://www.scala-lang.org/api/current/index.html#scala.collection.immutable.Stream$).
These helper methods are great when you have an infinite stream and when each element can be computed as a function of the previous one.
Clearly Cron stream cannot take advantage of this handy tool as it *can* be finite as shown earlier.
But for the sake of being complete, here is a much shorter, **but incorrect** implementation using `iterate`:

```scala
def infiniteFindTriggerTimes(expr: CronExpression, after: Date) =
    Stream.iterate(expr getNextValidTimeAfter after){last =>
        expr getNextValidTimeAfter last
    }
```

...and Clojure:

```clojure
(defn find-trigger-times [expr after]
    (iterate 
        #(. expr getNextValidTimeAfter %)
        (. expr getNextValidTimeAfter after)))
```

The idea in both cases is simple: we provide initial element `x` (first argument in Scala, second in Clojure) and a function `f` that transforms previous element to current one.
In other words we produce the following stream: `[x, f(x), f(f(x)), f(f(f(x))), ...]`.

Implementations above work until they reach end of stream (if any).
So to end with something positive we shall use `iterate` to produce infinite stream of prime numbers (apologize for such a theoretical problem) using naïve `prime?`
predicate:

```clojure
(defn- divisors [x] 
    (filter #(zero? (rem x %))
        (range 2 (inc (Math/sqrt x)))))
(defn- prime? [x] (empty? (divisors x)))
(defn- next-prime [after] 
    (loop [x (inc after)] 
        (if (prime? x) 
            x
            (recur (inc x)))))
(def primes (iterate next-prime 2))
```

I hope both the idea and the implementation are clear.
If a number doesn't have any divisors, it's considered prime.
`next-prime` returns subsequent prime number greater than a given value.
So `(next-prime 2)` yields `3`, `(next-prime 3)` gives `5` and so on.
Using this function we can build `primes` lazy sequence by simply providing first prime number and `next-prime` function.

# Conclusion

Lazy sequences (or streams) are great abstractions, impossible or tedious to represent in imperative languages.
They feel like normal lists but they are evaluated only when needed.
Both Scala and Clojure have great support for them and they behave similarly.
You can map, filter, cut etc. on streams and they never really compute their elements as long as it's not really needed.
Moreover they cache already computed values while still being thread-safe.
However when dealing with infinity, care must be taken.
If you try to innocently count elements of infinite stream or find non-existing item (e.g.
`primes.find(_ == 10)`) no one will save you.

<sup>1</sup> - `getNextValidTimeAfter()` full implementation is [400 lines long](http://grepcode.com/file/repo1.maven.org/maven2/org.quartz-scheduler/quartz/2.1.6/org/quartz/CronExpression.java#CronExpression.getTimeAfter(java.util.Date)).
