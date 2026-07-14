---
layout: post
title: Testing Quartz Cron expressions
date: '2012-10-20T19:40:00.002+02:00'
author: Tomasz Nurkiewicz
tags:
- scala
- intellij idea
- quartz
modified_time: '2012-10-31T13:37:40.772+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-7081347593846515102
blogger_orig_url: https://www.nurkiewicz.com/2012/10/testing-quartz-cron-expressions.html
image:
  path: /assets/img/testing-quartz-cron-expressions/hero.jpg
  alt: "Trollvann"
---

Declaring complex Cron expressions is still giving me some headaches, especially when some more advanced constructs are used.
After all, can you tell when the following trigger will fire `"0 0 17 L-3W 6-9 ? *"`?
Since triggers are often meant to run far in the future, it's desired to test them beforehand and make sure they will actually fire when we think they will.

[Quartz scheduler](http://quartz-scheduler.org/) (I'm testing version 2.1.6) doesn't provide direct support for that, but it's easy to craft some simple function based on existing APIs, namely [`CronExpression.getNextValidTimeAfter()`](http://quartz-scheduler.org/api/2.1.5/org/quartz/CronExpression.html#getNextValidTimeAfter(java.util.Date)) method.
Our goal is to define a method that will return next `N` scheduled executions for a given Cron expression.
We cannot request *all* since some triggers (including the one above) do not have end date, repeating infinitely.
We can only depend on aforementioned `getNextValidTimeAfter()` which takes a date as an argument and returns nearest fire time `T`<sub>`1`</sub> after that date.
So if we want to find second scheduled execution, we must ask about next execution after the first one (`T`<sub>`1`</sub>).
And so on.
Let's put that into code:

```scala
def findTriggerTimesIterative(expr: CronExpression, from: Date = new Date, max: Int = 100): Seq[Date] = {
    val times = mutable.Buffer[Date]()
    var next = expr getNextValidTimeAfter from
    while (next != null && times.size < max) {
        times += next
        next = expr getNextValidTimeAfter next
    }
    times
}
```

If there is no next fire time (e.g.
trigger is suppose to run only in 2012 and we ask about fire times after 1st of January 2013), `null` is returned.
A little bit of crash testing:

```scala
findTriggerTimesRecursive(new CronExpression("0 0 17 L-3W 6-9 ? *")) foreach println
```

yields:

```text
Thu Jun 27 17:00:00 CEST 2013
Mon Jul 29 17:00:00 CEST 2013
Wed Aug 28 17:00:00 CEST 2013
Fri Sep 27 17:00:00 CEST 2013
Fri Jun 27 17:00:00 CEST 2014
Mon Jul 28 17:00:00 CEST 2014
Thu Aug 28 17:00:00 CEST 2014
Fri Sep 26 17:00:00 CEST 2014
Fri Jun 26 17:00:00 CEST 2015
Tue Jul 28 17:00:00 CEST 2015
Fri Aug 28 17:00:00 CEST 2015
Mon Sep 28 17:00:00 CEST 2015
Mon Jun 27 17:00:00 CEST 2016
...
```

Hope the meaning of our complex Cron expression is now clearer: *closest week day (`W`) three days before the end of month (`L-3`) between June and September (`6-9`) at 17:00:00 (`0 0 17`)*.
Now I started experimenting a little bit with different implementations to find the most elegant and suitable for this quite simple problem.
First I noticed that the problem is not iterative, but recursive: finding next 100 execution times is equivalent to finding first execution and finding 99 remaining executions after the first one:

```scala
def findTriggerTimesRecursive(expr: CronExpression, from: Date = new Date, max: Int = 100): List[Date] = 
    expr getNextValidTimeAfter from match {
        case null => Nil
        case next =>
            if (max > 0)
                next :: findTriggerTimesRecursive(expr, next, max - 1)
            else
                Nil
    }
```

Seems like the implementation is much simpler: no matches - return empty list (`Nil`).
Match found - return it prepended to next matches, unless we already collected enough dates.
There is one problem with this implementation though, it's not [tail-recursive](http://en.wikipedia.org/wiki/Tail_call).
Very often this can be changed by introducing second function and accumulating the intermediate results in arguments:

```scala
def findTriggerTimesTailRecursive(expr: CronExpression, from: Date = new Date, max: Int = 100) = {

    @tailrec def accum(curFrom: Date, curMax: Int, acc: List[Date]): List[Date] = {
        expr getNextValidTimeAfter curFrom match {
            case null => acc
            case next =>
                if (curMax > 0)
                    accum(next, curMax - 1, next :: acc)
                else
                    acc
        }
    }

    accum(from, max, Nil)
}
```

A little bit more complex, but at least [`StackOverflowError`](http://docs.oracle.com/javase/7/docs/api/java/lang/StackOverflowError.html) won't wake us up in the middle of night.
BTW I just noticed IntelliJ IDEA not only shows icons identifying recursion (see next to line number), but also uses different icons when tail-call optimization is employed (!):

[![](/assets/img/testing-quartz-cron-expressions/1.png)](/assets/img/testing-quartz-cron-expressions/1.png)

So I thought that's best what I can get when another idea came to me.
First of all, the artificial `max` limit (defaulting to 100) seemed awkward.
Also why accumulate all the results if we can compute them on the fly, one after another?
This is when I realized that I don't need `Seq` or `List`, I need an `Iterator[Date]`!

```scala
class TimeIterator(expr: CronExpression, from: Date = new Date) extends Iterator[Date] {
    private var cur = expr getNextValidTimeAfter from

    def hasNext = cur != null

    def next() = if (hasNext) {
        val toReturn = cur
        cur = expr getNextValidTimeAfter cur
        toReturn
    } else {
        throw new NoSuchElementException
    }
}
```

I've spent some time trying to reduce the `if` true-branch into one-liner and avoid intermediate `toReturn` variable.
It's possible, but for clarity (and to spare your eyes) I won't reveal it<sup>\*</sup>.
But why an iterator, known to be less flexible and pleasant to use?
Well, first of all it allows us to lazily generate next trigger times, so we don't pay for what we don't use.
Also intermediate results aren't stored anywhere, so we can save memory as well.
And because everything that works for sequences works for iterators as well, we can easily work with iterators in Scala, e.g. printing (*taking*) first 10 dates:

```scala
new TimeIterator(expr) take 10 foreach println
```

It's tempting to do a little benchmark comparing different implementations (here using [caliper](http://code.google.com/p/caliper/)):

```scala
object FindTriggerTimesBenchmark extends App {
    Runner.main(classOf[FindTriggerTimesBenchmark], Array("--trials", "1"))
}

class FindTriggerTimesBenchmark extends SimpleBenchmark {

    val expr = new CronExpression("0 0 17 L-3W 6-9 ? *")

    def timeIterative(reps: Int) {
        for (i <- 1 to reps) {
            findTriggerTimesIterative(expr)
        }
    }

    def timeRecursive(reps: Int) {
        for (i <- 1 to reps) {
            findTriggerTimesRecursive(expr)
        }
    }

    def timeTailRecursive(reps: Int) {
        for (i <- 1 to reps) {
            findTriggerTimesTailRecursive(expr)
        }
    }

    def timeUsedIterator(reps: Int) {
        for (i <- 1 to reps) {
            (new TimeIterator(expr) take 100).toList
        }
    }

    def timeNotUsedIterator(reps: Int) {
        for (i <- 1 to reps) {
            new TimeIterator(expr)
        }
    }
}
```

Seems like the implementation changes have negligible impact on time since most of the CPU is presumably burnt inside `getNextValidTimeAfter()`.

[![](/assets/img/testing-quartz-cron-expressions/2.png)](/assets/img/testing-quartz-cron-expressions/2.png)

#### What have we learnt today?

- don't think too much about performance unless you really have a problem.
  Strive for best design and simplest implementation.
- think a lot about data structures you want to use to represent your problem and solution.
  In this (trivial on first sight) problem `Iterator` (lazily evaluated, possibly infinite stream of items) turned out to be the best approach

<sup>\*</sup> OK, here's how.
Hint: assignment has `Unit` type and `(Date, Unit)` tuple is involved here:

```scala
def next() = if (hasNext)
    (cur, cur = expr getNextValidTimeAfter cur)._1
else
    throw new NoSuchElementException
```
