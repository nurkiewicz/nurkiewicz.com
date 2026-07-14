---
layout: post
title: Probability distribution for programmers
date: '2013-01-09T20:02:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- probability
- scala
- puzzles
modified_time: '2013-01-09T20:02:46.234+01:00'
thumbnail: /assets/img/probability-distribution-for-programmers/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5554563912317406972
blogger_orig_url: https://www.nurkiewicz.com/2013/01/probability-distribution-for-programmers.html
---

This is one of these very simple programming puzzles I came across recently:

> **given a function returning random integers from `0` to `4` inclusive with equal probability, write a function returning random integers from `0` to `6` inclusive.**

Of course the solution should also return equally distributed numbers.
So let’s start from an input function sample definition:

```scala
def rand4() = (math.random * 5).toInt
```

Your task is to implement `rand6()` by only using `rand4()`.
Give yourself few minutes and continue reading.

.

.

.

The first approach is pretty straightforward but happens to be completely broken:

```scala
def rand6() = rand4() * 3 / 2
```

As simple as that.
In ideal solution each output value from `0` to `6` should appear with the probability of `1/7`.
Can you tell from the code above, what's the probability of `rand6()` returning `2` or `5`?
That's right, it's no more than `0`, you'll never get these values.
I hope it's clear why.
So let's go for something more sophisticated:

```scala
def rand6() = (rand4() + rand4()) % 7
```

Looks better, but still pretty far.
The code above has two major flaws.
First of all the results of `rand4() + rand4()` expression range from `0` to `8` but we need `0` to `6`.
The obvious solution is to use `% 7` operation.
However this results in `0` and `1` being returned twice as often because `7` and `8` are overflowing to `0` and `1`.
So what about this:

```scala
def rand6(): Int = {
    val rand8 = rand4() + rand4()
    if(rand8 > 6)
        rand6()
    else
        rand8
}
```

I hope the recursion (which can easily be turned into loop, but I leave that work to the Scala compiler) is not obscuring the intent - if the sum of two `rand4()` invocations is above expected result, we simply discard it and call `rand6()` again.
However there is still one subtle but striking bug, quoting Wikipedia on [uniform distribution](http://en.wikipedia.org/wiki/Uniform_distribution_(continuous))

> The sum of two independent, equally distributed, uniform distributions yields a symmetric [triangular distribution](http://en.wikipedia.org/wiki/Triangular_distribution).

If you don't quite get the above, have a look at [this live demo in JavaScript using `<canvas/>`](http://jsfiddle.net/nurkiewicz/SXCMF/1/) illustrating what Wikipedia means:

[![](/assets/img/probability-distribution-for-programmers/1.png)](/assets/img/probability-distribution-for-programmers/1.png)

# 

This program simply places pixels at *random* `(X, Y)` positions on each panel.
In the first panel I use one `Math.random() * 300` call scaled to fit whole canvas.
As you can see the distribution is more or less uniform.
But we can't tell that about second and third panels.
On the second panel I am using the sum of two uniformly distributed variables, in principle: `(Math.random() + Math.random()) * 150)`.
Even though this expression can return anything between `0` and `300`, the points are very biased toward the middle of the canvas (triangular distribution).
The same behaviour is emphasized on the third panel where ten invocations of `Math.random()` are used.

### The correct answer

The approach I'm taking is based on the observation that `rand4()` is capable of producing two random least significant bits.
So let's start from implementing `rand3()` with known semantics:

```scala
def rand3(): Int = rand4() match {
    case 4 => rand3()
    case x => x
}
```

`rand3()` returns uniformly distributed values from `0` to `3` doing so by rejecting `4` output of `rand4()`.
How will that help us?
Well, we now have two random bits, each one being either `0` or `1` with 50% probability.
We can easily widen it for larger sequences, e.g. `rand15()` and `rand7()`:

```scala
def rand15() = (rand3() << 2) + rand3()
def rand7() = rand15() >> 1
```

You should be rather comfortable with the bit fiddling above.
Having the ability to produce two random bits I can easily generate 4 and 3.
Now `rand6()` is a no-brainer:

```scala
def rand6() = rand7() match {
    case 7 => rand6()
    case x => x
}
```

------------------------------------------------------------------------

Just to make this lesson a little bit more interesting, let's implement `randN(n: Int)` on top of `rand4()`.
`randN()` should return uniformly distributed natural values from `0` to `n`.
I'll begin by implementing helper method `atLeastKrandBits(k: Int)` returning...
*at least K random bits*:

```scala
def atLeastKrandBits(k: Int): Int = k match {
    case 0 => 0
    case 1 => rand3() >> 1
    case 2 => rand3()
    case b => (atLeastKrandBits(k - 2) << 2) + rand3()
}
```

[Alternative implementation](http://c2.com/cgi/wiki?ThereIsMoreThanOneWayToDoIt) with `foldLeft()`:

```scala
def atLeastKrandBits(k: Int) = (0 to (k + 1) / 2).foldLeft(0){
    (acc, _) => (acc << 2) + rand3()
}
```

...or if you really hate those to maintain your code:

```scala
def atLeastKrandBits(k: Int) = (0 /: (0 to (k + 1) / 2)){
    (acc, _) => (acc << 2) + rand3()
}
```

Having any of the implementations above `randN(n: Int)` is simple:

```scala
def randN(n: Int) = {
    val bitsCount = java.lang.Integer.highestOneBit(n)
    val randBits = atLeastKrandBits(bitsCount)
    if(randBits > n)
        randN(n)
    else
        randBits
}
```

### Conclusions

You might ask yourself a question: *why should I even care?*
If you fail to understand probability distribution your application might produce random output that's actually quite easy to predict.
It's not a big deal if you are writing a game and enemies are more likely to appear at some places on the map (but the players *will* discover and abuse it!)
But if you need random numbers for security reasons or you rely on uniform distribution e.g. for load-balancing purposes - any bias might become fatal.
