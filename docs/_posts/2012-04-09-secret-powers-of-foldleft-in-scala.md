---
layout: post
title: Secret powers of foldLeft() in Scala
date: '2012-04-09T15:26:00.001+02:00'
author: Tomasz Nurkiewicz
tags:
- scala
modified_time: '2012-04-10T10:35:34.480+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-574688540848567249
blogger_orig_url: https://www.nurkiewicz.com/2012/04/secret-powers-of-foldleft-in-scala.html
---

*`foldLeft()` method, available for all collections in Scala, allows to run a given 2-argument function against consecutive elements of that collection, where the result of that function is passed as the first argument in the next invocation.
Second argument is always the current item in the collection.*
Doesn't sound very encouraging but as we will see soon there are great some use-cases waiting to be discovered.

Before we dive into `foldLeft`, let us have a look at `reduce` - simplified version of `foldLeft`.
I always believed that a [working code is worth a thousand words](http://en.wikipedia.org/wiki/A_picture_is_worth_a_thousand_words):

```scala
val input = List(3, 5, 7, 11)
input.reduce((total, cur) => total + cur)
```

or more readable:

```scala
def op(total: Int, cur: Int) = total + cur

input reduce op
```

The result is `26` (sum).
The code is more-or-less readable: to `reduce` method we are passing 2-argument function `op` (operation).
Both parameters of that function (and its return value) need to have the same type as the collection.
`reduce()` will invoke that operation on two first items of the collection:

```scala
op(3, 5)  //8
```

The result (`8`) is passed as a first argument to a subsequent invocation of `op` where the second argument is the next collection element:

```scala
op(8, 7)  //15
```

and finally:

```scala
op(15, 11)  //26
```

From the logical standpoint the following composed operation has been invoked:

```scala
op(op(op(3, 5), 7), 11)
```

When we realize that `op()` is basically an addition:

```scala
(((3 + 5) + 7) + 11)
```

So far so good - `reduce()` *reduces* a collection of a given type to a single value of the same type.
Example use-cases include adding up numbers, concatenating a sequence of strings, etc.:

```scala
List("Foo", "Bar", "Buzz").reduce(_ + _)
```

Note the shorthand notation for code block without naming the parameters: `_ + _`.
Obviously we are not limited to addition operator:

```scala
def factorial(x: Int) = (2 to x).reduce(_ * _)
```

It is worth to mention two special cases: when the collection has only one element, `reduce()` returns this very element.
When it is empty, `reduce()` will throw an exception.
Let's face it, typically we implement factorial for the first (and last) time somewhere at the beginning of the university and to add up numbers we have a convenience method:

```scala
input.sum
```

Besides the problem with empty collections is a bit painful - after all the sum of empty set of numbers is intuitively equal to 0 and the concatenation of an empty set of strings is...
an empty string.
Here is where `foldLeft()` enters with the ability to specify initial value:

```scala
input.foldLeft(0)(op)
```

In this case the `op()` function is first called with initial value `0` as the first argument and with the first collection element:

```scala
op(0, 3)
```

The subsequent iterations remain the same.
If the collection is empty, `foldLeft()` returns the initial value.
It is sad how many tutorial stop right here.
After all we can simply prepend initial value to the input list and happily use `reduce()`:

```scala
(0 :: input).reduce(op)
(0 :: Nil).reduce(op)  //empty list is prepended by 0
```

Even worse, many suggest “simplified" `foldLeft()` syntax, I doubt it simplifies anything:

```scala
(0 /: input)(op)
```

This is equivalent to `input.foldLeft(0)(op)` but intended for people who love Perl.
So, closing this way too long introduction, let us see the true power behind `foldLeft()`.

Let us assume that we have an object of type `[T]` on which we would like to perform a set of transformations.
Transformation is nothing more than a function that accepts and returns an object of type `[T]`.
We can return the same instance (no-op transformation), wrap the original object (the *Decorator* pattern) or mutate it.

It is not hard to imagine that the order of transformations is important.
For example let us use an ordinary string and set of transformations represented by functions of `String => String`:

```scala
val reverse = (s: String) => s.reverse

val toUpper = (s: String) => s.toUpperCase

val appendBar = (s: String) => s + "bar"
```

Remembering that a result of a first transformation is an argument of the second one we can say:

```scala
appendBar(toUpper(reverse("foo")))  //OOFbar
toUpper(reverse(appendBar("foo")))  //RABOOF
```

I think that's obvious.
Unfortunately we need a method taking an arbitrary (possibly empty or created dynamically) list of transformations to apply:

```scala
def applyTransformations(initial: String, transformations: Seq[String => String]) = //???

applyTransformations("foo", List(reverse, toUpper, appendBar))
applyTransformations("foo", List(appendBar, reverse, toUpper))
applyTransformations("foo", List.fill(7)(appendBar))
```

The last line performs `appendBar` transformation 7 times on an initial value `"foo"`.
How to implement `applyTransformations` method?
The programmer with highly imperative background would probably come up with something like this:

```scala
def applyTransformations(initial: String, transformations: Seq[String => String]) = {
    var cur = initial
    for(transformation <- transformations) {
        cur = transformation(cur)
    }
    cur
}
```

Boring loop over all transformations, the intermediate result is stored in a variable.
This implementation has several drawbacks.
First - it's imperative (!)
Scala tries to embrace the functional programming paradigm and this code seems very low-level.
Our second take is much more idiomatic as far as Scala is concerned - we use recursion and pattern matching:

```scala
@tailrec
def applyTransformations(initial: String, transformations: Seq[String => String]): String =
    transformations match {
        case head :: tail => applyTransformations(head(initial), tail)
        case Nil => initial
    }
```

A little bit harder to comprehend compared to imperative solution.
If the list of transformations is empty - return current value.
If it's not, apply the first transformation (`head(initial)`) and recursively call myself with the rest of the transformations (`tail`).

Turns out this problem can be implemented in much, much more concise way, without explicit loops and recursion.
Have you noticed how the problem with nested transformations (`appendBar(toUpper(reverse("foo")))`) is similar to how the `foldLeft()` works (`op(op(op(3, 5), 7), 11)`)?

```scala
def applyTransformations(initial: String, transformations: Seq[String => String]) =
    transformations.foldLeft(initial) {
        (cur, transformation) => transformation(cur)
    }
```

Understanding how the code above works requires a little bit of time - but it is really rewarding afterwards.
Also it allows you to fully grasp the power of `foldLeft()`.
Before you go further try to figure this out yourself.
Few tips:

- The type of `foldLeft()` result `[B]` doesn't necessarily have to be the same as the collection type `[A]`.
  It is the type of the initial value.
  In our example the input collection contains functions but the initial value is String.

- Function passed as an argument to `foldLeft()` does not need to accept both arguments of `[A]` type and return that type as well - as it was with `reduce()`.
  In fact, the signature of `foldLeft()` is as follows:

  ``` scala
  def foldLeft[B](initial: B)(op: (B, A) => B): B
  ```

- The value returned by `op` function should be of the same type as its first argument.
  Also the whole `foldLeft()` invocation will have the same type.

Let's think about it: the type of the first argument of `op()` is compatible with the initial value (`initial: B`) because in the first iteration it is the initial value that is passed as the first argument of `op`.
A second argument is the first element of the input collection of type `[A]`.
In the second iteration the result of `op()` invocation (of type `[B]`) is passed as the first argument of subsequent invocation of `op`.
This time the second element of the input collection is used as the second argument.
And it goes on until it reaches the end of the collection.

I think the pseudo-code would be much easier to comprehend.
First some example invocation:

```scala
List(reverse, toUpper, appendBar).foldLeft("foo") {
    (cur, transformation) => transformation(cur)
}
```

Subsequent iterations (pseudo-code):

```scala
val initial = "foo"
val temp1 = (initial, reverse) => reverse(initial)
val temp2 = (temp1, toUpper) => toUpper(temp1)
val temp3 = (temp2, appendBar) => appendBar(temp2)
```

And after inlining temporary variables:

```scala
val initial = "foo"
appendBar(toUpper(reverse(initial)))
```

Isn't this the result we've been waiting for?
As it turns out, `foldLeft()` is not only useful when we need to reduce (aggregate) collection to a single value, like adding up numbers - in fact, `reduce()` or `sum()` are better suited in this case.
`foldLeft()` seems to be a great fit when we need to iterate over an arbitrary collection but every iteration requires some sort of result from previous one.
By the way this is the reason why `fold` and `reduce` operations can't be executed in parallel.

In comments to the original article *Cezary Bartoszuk* suggested an alternative way of using `foldLeft()` in this problem:

```scala
def composeAll[A](ts: Seq[A => A]): A => A = ts.foldLeft(identity[A] _)(_ compose _)

def applyTransformations(init: String, ts: Seq[String => String]): String = composeAll(ts.reverse)(init)
```

If this solution isn't clear to your, once again few tips.
First of all `identity[A] _` is an [identity function](http://en.wikipedia.org/wiki/Identity_function) - always returning an argument untouched.
Secondly `val composed = appendBar compose toUpper` is equivalent to:

```scala
val composed = (s: String) => appendBar(toUpper(s))
```

So another mathematical term: [function composition](http://en.wikipedia.org/wiki/Function_composition).

> This was a translation of my article [*"Ukryta potęga foldLeft()"*](http://scala.net.pl/ukryta-potega-foldleft/) originally published on [scala.net.pl](http://scala.net.pl/).
