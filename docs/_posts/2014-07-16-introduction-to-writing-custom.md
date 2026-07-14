---
layout: post
title: Introduction to writing custom collectors in Java 8
date: '2014-07-16T00:06:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- scala
- java 8
modified_time: '2016-10-29T14:43:03.095+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-547584015613262829
blogger_orig_url: https://www.nurkiewicz.com/2014/07/introduction-to-writing-custom.html
---

Java 8 introduced the concept of collectors.
Most of the time we barely use factory methods from [`Collectors`](http://docs.oracle.com/javase/8/docs/api/java/util/stream/Collectors.html) class, e.g. [`collect(toList())`](http://docs.oracle.com/javase/8/docs/api/java/util/stream/Collectors.html#toList--), [`toSet()`](http://docs.oracle.com/javase/8/docs/api/java/util/stream/Collectors.html#toSet--) or maybe something more fancy like [`counting()`](http://docs.oracle.com/javase/8/docs/api/java/util/stream/Collectors.html#counting--) or [`groupingBy()`](http://docs.oracle.com/javase/8/docs/api/java/util/stream/Collectors.html#groupingBy-java.util.function.Function-).
Not many of us actually bother to look how collectors are defined and implemented.
Let's start from analysing what [`Collector<T, A, R>`](http://docs.oracle.com/javase/8/docs/api/java/util/stream/Collector.html) really is and how it works.

`Collector<T, A, R>` works as a "*sink*" for streams - stream pushes items (one after another) into a collector, which should produce some "*collected*" value in the end.
Most of the time it means building a collection (like `toList()`) by accumulating elements or reducing stream into something smaller (e.g.
`counting()` collector that barely counts elements).
Every collector accepts items of type `T` and produces aggregated (accumulated) value of type `R` (e.g.
`R = List<T>`).
Generic type `A` simply defines the type of intermediate mutable data structure that we are going to use to accumulate items of type `T` in the meantime.
Type `A` can, but doesn't have to be the same as `R` - in simple words the mutable data structure that we use to collect items from input `Stream<T>` can be different than the actual output collection/value.
That being said, every collector must implement the following methods:

```java
interface Collector<T,A,R> {
    Supplier<A>          supplier()
    BiConsumer<A,T>      acumulator() 
    BinaryOperator<A>    combiner() 
    Function<A,R>        finisher()
    Set<Characteristics> characteristics()
} 
```

- `supplier()` returns a function that creates an instance of accumulator - mutable data structure that we will use to accumulate input elements of type `T`.
- `accumulator()` returns a function that will take accumulator and one item of type `T`, mutating accumulator.
- `combiner()` is used to join two accumulators together into one.
  It is used when collector is executed in parallel, splitting input `Stream<T>` and collecting parts independently first.
- `finisher()` takes an accumulator `A` and turns it into a result value, e.g. collection, of type `R`.
  All of this sounds quite abstract, so let's do a simple example.

Obviously Java 8 doesn't provide a built-in collector for [`ImmutableSet<T>`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/collect/ImmutableSet.html) from Guava.
However creating one is very simple.
Remember that in order to iteratively build `ImmutableSet` we use [`ImmutableSet.Builder<T>`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/collect/ImmutableSet.Builder.html) - this is going to be our accumulator.

```java
import com.google.common.collect.ImmutableSet;

public class ImmutableSetCollector<T> 
        implements Collector<T, ImmutableSet.Builder<T>, ImmutableSet<T>> {
    @Override
    public Supplier<ImmutableSet.Builder<T>> supplier() {
        return ImmutableSet::builder;
    }

    @Override
    public BiConsumer<ImmutableSet.Builder<T>, T> accumulator() {
        return (builder, t) -> builder.add(t);
    }

    @Override
    public BinaryOperator<ImmutableSet.Builder<T>> combiner() {
        return (left, right) -> {
            left.addAll(right.build());
            return left;
        };
    }

    @Override
    public Function<ImmutableSet.Builder<T>, ImmutableSet<T>> finisher() {
        return ImmutableSet.Builder::build;
    }

    @Override
    public Set<Characteristics> characteristics() {
        return EnumSet.of(Characteristics.UNORDERED);
    }
}
```

First of all look carefully at generic types.
Our `ImmutableSetCollector` takes input elements of type `T`, so it works for any `Stream<T>`.
In the end it will produce `ImmutableSet<T>` - as expected.
`ImmutableSet.Builder<T>` is going to be our intermediate data structure.

- `supplier()` returns a function that creates new `ImmutableSet.Builder<T>`.
  If you are not that familiar with lambdas in Java 8, `ImmutableSet::builder` is a shorthand for `() -> ImmutableSet.builder()`.
- `accumulator()` returns a function that takes `builder` and one element of type `T`.
  It simply adds said element to the builder.
- `combiner()` returns a function that will accept two builders and turn them into one by adding all elements from one of them into the other - and returning the latter.
  Finally `finisher()` returns a function that will turn `ImmutableSet.Builder<T>` into `ImmutableSet<T>`.
  Again this is a shorthand syntax for: `builder -> builder.build()`.
- Last but not least, `characteristics()` informs JDK what capabilities our collector has.
  For example if `ImmutableSet.Builder<T>` was thread-safe (it isn't), we could say `Characteristics.CONCURRENT` as well.

We can now use our custom collector everywhere using `collect()`:

```java
final ImmutableSet<Integer> set = Arrays
        .asList(1, 2, 3, 4)
        .stream()
        .collect(new ImmutableSetCollector<>());
```

However creating new instance is slightly verbose so I suggest creating static factory method, similar to what JDK does:

```java
public class ImmutableSetCollector<T> implements Collector<T, ImmutableSet.Builder<T>, ImmutableSet<T>> {

    //...

    public static <T> Collector<T, ?, ImmutableSet<T>> toImmutableSet() {
        return new ImmutableSetCollector<>();
    }
}
```

From now on we can take full advantage of our custom collector by simply typing: `collect(toImmutableSet())`.
In the second part we will learn how to write more complex and useful collectors.

Check out the second part of this article: [Grouping, sampling and batching - custom collectors in Java 8](http://www.nurkiewicz.com/2014/07/grouping-sampling-and-batching-custom.html).

## Update

[@akarazniewicz](https://twitter.com/akarazniewicz) [pointed out](https://twitter.com/akarazniewicz/status/489288579882180608) that collectors are just verbose implementation of folding.
With my [love](http://www.nurkiewicz.com/2012/04/secret-powers-of-foldleft-in-scala.html) and [hate](http://www.nurkiewicz.com/2014/06/optionfold-considered-unreadable.html) relationship with folds, I have to comment on that.
Collectors in Java 8 are basically object-oriented encapsulation of the most complex type of fold found in Scala, namely [`GenTraversableOnce.aggregate[B](z: ⇒ B)(seqop: (B, A) ⇒ B, combop: (B, B) ⇒ B): B`](http://www.scala-lang.org/api/current/index.html#scala.collection.GenTraversableOnce).
`aggregate()` is like `fold()`, but requires extra `combop` to combine two accumulators (of type `B`) into one.
Comparing this to collectors, parameter `z` comes from a `supplier()`, `seqop()` reduction operation is an `accumulator()` and `combop` is a `combiner()`.
In pseudo-code we can write:

```java
finisher(
    seq.aggregate(collector.supplier())
        (collector.accumulator(), collector.combiner()))
```

`GenTraversableOnce.aggregate()` is used when concurrent reduction is possible - just like with collectors.
