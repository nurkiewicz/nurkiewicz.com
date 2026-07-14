---
layout: post
title: Option.fold() considered unreadable
date: '2014-06-23T22:17:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- scala
- functional programming
- Haskell
modified_time: '2014-06-23T22:17:17.077+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-893869958175356978
blogger_orig_url: https://www.nurkiewicz.com/2014/06/optionfold-considered-unreadable.html
---

We had a lengthy discussion recently during code review whether [`scala.Option.fold()`](http://www.scala-lang.org/api/2.11.1/index.html#scala.Option) is idiomatic and clever or maybe unreadable and tricky?
Let's first describe what the problem is.
`Option.fold` does two things: maps a function `f` over `Option`'s value (if any) or returns an alternative `alt` if it's absent.
Using simple pattern matching we can implement it as follows:

```scala
val option: Option[T] = //...
def alt: R = //...
def f(in: T): R = //...

val x: R = option match {
    case Some(v) => f(v)
    case None => alt
}
```

If you prefer one-liner, `fold` is actually a combination of `map` and `getOrElse`

```scala
val x: R = option map f getOrElse alt
```

Or, if you are a C programmer that still wants to write in C, but using Scala compiler:

```scala
val x: R = if (option.isDefined)
    f(option.get)
else
    alt
```

Interestingly this is similar to how `fold()` is actually implemented, but that's an implementation detail.
OK, all of the above can be replaced with single `Option.fold()`:

```scala
val x: R = option.fold(alt)(f)
```

Technically you can even use `/:` and `\:` operators (`alt /: option`) - but that would be simply masochistic.
I have three problems with `option.fold()` idiom.
First of all - it's anything but readable.
We are folding (reducing) over `Option` - which doesn't really make much sense.
Secondly it reverses the ordinary *positive-then-negative-case* flow by starting with failure (absence, `alt`) condition followed by presence block (`f` function; see also: [*Refactoring map-getOrElse to fold*](http://www.coolscala.com/wiki/Cool_Scala/Refactoring_map-getOrElse_to_fold)).
Interestingly this method would work great for me if it was named `mapOrElse`:

```scala
/**
 * Hypothetical in Option
 */
def mapOrElse[B](f: A => B, alt: => B): B =
    this map f getOrElse alt
```

Actually there is already such method in Scalaz, called [`OptionW.cata`](http://scalaz.googlecode.com/svn/continuous/latest/doc/scalaz/OptionW.html).
**cata**.
Here is what [Martin Odersky has to say about it](http://stackoverflow.com/questions/5328007):

> "I personally find methods like `cata` that take two closures as arguments are often overdoing it.
> Do you really gain in readability over `map` + `getOrElse`?
> Think of a newcomer to your code\[...\]"

While `cata` has some [theoretical background](http://en.wikipedia.org/wiki/Catamorphism), `Option.fold` just sounds like a random name collision that doesn't bring anything to the table, apart from confusion.
I know what you'll say, that `TraversableOnce` has `fold` and we are sort-of doing the same thing.
Why it's a random collision rather than extending the contract described in `TraversableOnce`?
`fold()` method in Scala collections typically just delegates to one of `foldLeft()`/`foldRight()` (the one that works better for given data structure), thus it doesn't guarantee order and folding function has to be associative.
But in `Option.fold()` the contract is different: folding function takes just one parameter rather than two.
If you read [my previous article about folds](http://www.nurkiewicz.com/2012/04/secret-powers-of-foldleft-in-scala.html) you know that reducing function always takes two parameters: current element and accumulated value (initial value during first iteration).
But `Option.fold()` takes just one parameter: current `Option` value!
This breaks the consistency, especially when realizing `Option.foldLeft()` and `Option.foldRight()` have *correct* contract (but it doesn't mean they are more readable).

The only way to understand folding over option is to imagine `Option` as a sequence with `0` or `1` elements.
Then it sort of makes sense, right?
No.

```scala
def double(x: Int) = x * 2

Some(21).fold(-1)(double)   //OK: 42
None.fold(-1)(double)       //OK: -1
```

but:

```scala
Some(21).toList.fold(-1)(double)
<console>: error: type mismatch;
 found   : Int => Int
 required: (Int, Int) => Int
              Some(21).toList.fold(-1)(double)
                                       ^
```

If we treat `Option[T]` as a `List[T]`, awkward `Option.fold()` breaks because it has different type than `TraversableOnce.fold()`.
This is my biggest concern.
I can't understand why *folding* wasn't defined in terms of the type system (trait?)
and implemented strictly.
As an example take a look at:

## `Data.Foldable` in Haskell (advanced)

[`Data.Foldable` typeclass](https://hackage.haskell.org/package/base-4.7.0.0/docs/Data-Foldable.html) describes various flavours of folding in Haskell.
There are familiar `foldl`/`foldr`/`foldl1`/`foldr1`, in Scala named `foldLeft`/`foldRight`/`reduceLeft`/`reduceRight` accordingly.
They have the same type as Scala and behave unsurprisingly with all types that you can fold over, including `Maybe`, lists, arrays, etc. There is also a function named `fold`, but it has a completely different meaning:

```text
class Foldable t where
    fold :: Monoid m => t m -> m
```

While other folds are quite complex, this one barely takes a foldable container of `m`s (which have to be [`Monoid`](https://hackage.haskell.org/package/base-4.7.0.0/docs/Data-Monoid.html)s) and returns the same `Monoid` type.
A quick recap: a type can be a `Monoid` if there exists a neutral value of that type and an operation that takes two values and produces just one.
Applying that function with one of the arguments being neutral value yields the other argument.
`String` (`[Char]`) is a good example with empty string being neutral value (`mempty`) and string concatenation being such operation (`mappend`).
Notice that there are two different ways you can construct monoids for numbers: under addition with neutral value being `0` (`x + 0 == 0 + x == x` for any `x`) and under multiplication with neutral `1` (`x * 1 == 1 * x == x` for any `x`).
Let's stick to strings.
If I fold empty list of strings, I'll get an empty string.
But when a list contains many elements, they are being concatenated:

```text
> fold ([] :: [String])
""
> fold [] :: String
""
> fold ["foo", "bar"]
"foobar"
```

In the first example we have to explicitly say what is the type of empty list `[]`.
Otherwise Haskell compiler can't figure out what is the type of elements in a list, thus which monoid instance to choose.
In second example we declare that whatever is returned from `fold []`, it should be a `String`.
From that the compiler infers that `[]` actually must have a type of `[String]`.
Last `fold` is the simplest: the program folds over elements in list and concatenates them because concatenation is the operation defined in `Monoid String` typeclass instance.

Back to options (or more precisely `Maybe`).
Folding over `Maybe` monad having type parameter being `Monoid` (I can't believe I just said it) has an interesting interpretation: it either returns value inside `Maybe` or a default `Monoid` value:

```text
> fold (Just "abc")
"abc"
> fold Nothing :: String
""
```

`Just "abc"` is same as `Some("abc")` in Scala.
You can see here that if `Maybe String` is `Nothing`, neutral `String` monoid value is returned, that is an empty string.

## Summary

Haskell shows that folding (also over `Maybe`) can be at least consistent.
In Scala `Option.fold` is unrelated to `List.fold`, confusing and unreadable.
I advise avoiding it and staying with slightly more verbose `map`/`getOrElse` transformations or pattern matching.

PS: Did I mention there is also [`Either.fold()`](http://www.scala-lang.org/api/current/index.html#scala.util.Either) (with even different contract) but no [`Try.fold()`](http://www.scala-lang.org/api/current/index.html#scala.util.Try)?
