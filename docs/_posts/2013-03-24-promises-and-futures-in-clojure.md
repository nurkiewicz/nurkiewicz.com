---
layout: post
title: Promises and futures in Clojure
date: '2013-03-24T11:15:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- clojure
- concurrency
modified_time: '2013-04-02T23:40:02.373+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2296222456006130476
blogger_orig_url: https://www.nurkiewicz.com/2013/03/promises-and-futures-in-clojure.html
---

Clojure, being [*designed for concurrency*](http://clojure.org/rationale) is a natural fit for our [*Back to the Future* series](http://nurkiewicz.com/2013/02/javautilconcurrentfuture-basics.html).
Moreover futures are supported out-of-the-box in Clojure.
Last but not least, Clojure is the first language/library that draws a clear distinction between *futures* and *promises*.
They are so similar that most platforms either support only futures or combine them.
Clojure is very explicit here, which is good.
Let's start from promises:

## Promises

Promise is a thread-safe object that encapsulates immutable value.
This value might not be available yet and can be *delivered* exactly once, from any thread, later.
If other thread tries to *dereference* a promise before it's delivered, it'll block calling thread.
If promise is already resolved (delivered), no blocking occurs at all.
Promise can only be delivered once and can never change its value once set:

```clojure
(def answer (promise))

@answer

(deliver answer 42)
```

`answer` is a `promise` var.
Trying to dereference it using `@answer` or `(deref answer)` at this point will simply block.
This or some other thread must first deliver some value to this promise (using `deliver` function).
All threads blocked on `deref` will wake up and subsequent attempts to dereference this promise will return `42` immediately.
Promise is thread safe and you cannot modify it later.
Trying to deliver another value to `answer` is ignored.

## Futures

Futures behave pretty much the same way in Clojure from user perspective - they are containers for a single value (of course it can be a `map` or `list` - but it should be immutable) and trying to dereference future before it is resolved blocks.
Also just like promises, futures can only be resolved once and dereferencing resolved future has immediate effect.
The difference between the two is semantic, not technical.
Future represents background computation, typically in a thread pool while promise is just a simple container that can be delivered (filled) by anyone at any point in time.
Typically there is no associated background processing or computation.
It's more like an event we are waiting for (e.g.
[JMS message reply we wait for](http://nurkiewicz.com/2013/03/deferredresult-asynchronous-processing.html)).

That being said, let's start some asynchronous processing.
[Similar to Akka](http://nurkiewicz.com/2013/03/futures-in-akka-with-scala.html), underlying thread pool is implicit and we simply pass piece of code that we want to run in background.
For example to calculate the sum of positive integers below ten million we can say:

```clojure
(let 
    [sum (future (apply + (range 1e7)))] 
    (println "Started...") 
    (println "Done: " @sum)
)
```

`sum` is the future instance.
`"Started..."`
message appears immediately as the computation started in background thread.
But `@sum` is blocking and we actually have to wait a little bit<sup>1</sup> to see the `"Done: "` message and computation results.
And here is where the greatest disappointment arrives: neither [`future`](http://clojuredocs.org/clojure_core/clojure.core/future) nor [`promise`](http://clojuredocs.org/clojure_core/clojure.core/promise) in Clojure supports listening for completion/failure asynchronously.
The API is pretty much equivalent to [very limited `java.util.concurrent.Future<T>`](http://nurkiewicz.com/2013/02/javautilconcurrentfuture-basics.html).
We can create `future`, [`cancel` it](http://clojuredocs.org/clojure_core/clojure.core/future-cancel), check whether it is [`realized?` (resolved)](http://clojuredocs.org/clojure_core/clojure.core/realized_q) and block waiting for a value.
Just like `Future<T>` in Java, as a matter of fact the result of `future` function even implements `java.util.concurrent.Future<T>`.
As much as I love Clojure concurrency primitives like STM and agents, futures feel a bit underdeveloped.
Lack of event-driven, asynchronous callbacks that are invoked whenever futures completes (notice that [`add-watch`](http://clojuredocs.org/clojure_core/clojure.core/add-watch) doesn't work futures - and is still in alpha) greatly reduces the usefulness of a future object.
We can no longer:

- map futures to transform result value asynchronously
- chain futures
- translate list of futures to future of list
- ...and much more, see how [Akka does it](http://nurkiewicz.blogspot.no/2013/02/javautilconcurrentfuture-basics.html) and [Guava to some extent](http://nurkiewicz.blogspot.no/2013/02/advanced-listenablefuture-capabilities.html)

That's a shame and since it's not a technical difficulty but only a missing API, I hope to see support for completion listeners soon.
For completeness here is a slightly bigger program using futures to concurrently fetch contents of several websites, foundation for our [web crawling sample](http://nurkiewicz.blogspot.no/2013/02/executorcompletionservice-in-practice.html):

```clojure
(let [
    top-sites `("www.google.com" "www.youtube.com" "www.yahoo.com" "www.msn.com")
    futures-list (doall (
            map #(
                future (slurp (str "http://" %))
            )
            top-sites
    ))
    contents (map deref futures-list)
    ]
(doseq [s contents] (println s))
)
```

Code above starts downloading contents of several websites concurrently.
`map deref` waits for all results one after another and once all futures from `futures-list` all completed, `doseq` prints the contents (`contents` is a list of strings).

One trap I felt into was the absence of `doall` (that forces lazy sequence evaluation) in my initial attempt.
`map` produces lazy sequence out of `top-sites` list, which means `future` function is called only when given item of `futures-list` is first accessed.
That's good.
But each item is accessed for the first time only during `(map deref futures-list)`.
This means that while waiting for first future to dereference, second future didn't even started yet!
It starts when first future completes and we try to dereference the second one.
That means that last future starts when all previous futures are already completed.
To cut long story short, without `doall` that forces all futures to start immediately, our code runs sequentially, one future after another.
The beauty of side effects.

<sup>1</sup> - ~~BTW `(1L to 9999999L).sum` in Scala is faster by almost an order of magnitude, *just sayin'*...~~
- see comments by *Rave Star* below.
