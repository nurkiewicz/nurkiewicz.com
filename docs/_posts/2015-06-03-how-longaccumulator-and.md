---
layout: post
title: How LongAccumulator and DoubleAccumulator classes work?
date: '2015-06-03T23:21:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- multithreading
- java 8
- concurrency
modified_time: '2015-06-05T15:57:21.824+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3544067282361166774
blogger_orig_url: https://www.nurkiewicz.com/2015/06/how-longaccumulator-and.html
---

Two classes new in Java 8 deserve some attention: `LongAccumulator` and `DoubleAccumulator`.
They are designed to *accumulate* (more on what does that mean later) values across threads safely while being extremely fast.
A test is worth a thousand words, so here is how it works:

```java
class AccumulatorSpec extends Specification {

    public static final long A = 1
    public static final long B = 2
    public static final long C = 3
    public static final long D = -4
    public static final long INITIAL = 0L

    def 'should add few numbers'() {
        given:
            LongAccumulator accumulator = new LongAccumulator({ long x, long y -> x + y }, INITIAL)
        when:
            accumulator.accumulate(A)
            accumulator.accumulate(B)
            accumulator.accumulate(C)
            accumulator.accumulate(D)
        then:
            accumulator.get() == INITIAL + A + B + C + D
    }
```

So the accumulator takes a binary operator and combines initial value with every accumulated value.
That means `((((0 + 1) + 2) + 3) + -4)` equals to `2`.
Don't go away yet, there's much more than that.
Accumulator can take other operators as well, as illustrated by this use case:

```java
def 'should accumulate numbers using operator'() {
    given:
        LongAccumulator accumulator = new LongAccumulator(operator, initial)
    when:
        accumulator.accumulate(A)
        accumulator.accumulate(B)
        accumulator.accumulate(C)
        accumulator.accumulate(D)
    then:
        accumulator.get() == expected
    where:
        operator                 | initial           || expected
        {x, y -> x + y}          | 0                 || A + B + C + D
        {x, y -> x * y}          | 1                 || A * B * C * D
        {x, y -> Math.max(x, y)} | Integer.MIN_VALUE || max(A, B, C, D)
        {x, y -> Math.min(x, y)} | Integer.MAX_VALUE || min(A, B, C, D)
}
```

Obviously accumulator would work just as well under heavy multi-threaded environment - which it was designed for.
Now the question is, what other operations are permitted in `LongAccumulator` (this applies to `DoubleAccumulator` as well) and why?
JavaDoc is not very formal this time (bold mine):

> The order of accumulation within or across threads is not guaranteed and cannot be depended upon, so this class is only applicable to **functions for which the order of accumulation does not matter.
> The supplied accumulator function should be side-effect-free**, since it may be re-applied when attempted updates fail due to contention among threads.
> The function is applied with the current value as its first argument, and the given update as the second argument.

In order to understand how `LongAccumulator` works, what type of operations are permitted and why it's so fast (because it is, compared to e.g `AtomicLong`), let's start from the back, the `get()` method:

```java
transient volatile long base;
transient volatile Cell[] cells;

private final LongBinaryOperator function;

public long get() {
    Cell[] as = cells; Cell a;
    long result = base;
    if (as != null) {
        for (int i = 0; i < as.length; ++i) {
            if ((a = as[i]) != null)
                result = function.applyAsLong(result, a.value);
        }
    }
    return result;
}
```

Which can be rewritten to not-exactly-equivalent but easier to read:

```java
public long get() {
    long result = base;
    for (Cell cell : cells)
        result = function.applyAsLong(result, cell.value);
    return result;
}
```

Or even more functionally without internal state:

```java
public long get() {
    return Arrays.stream(cells)
            .map(s -> s.value)
            .reduce(base, function::applyAsLong);
}
```

We clearly see that there is some internal `cells` array and that in the end we must go through that array and apply our operator function sequentially on each element.
Turns out `LongAccumulator` has two mechanisms for accumulating values: a single `base` counter and an array of values in case of high lock thread contention.
If `LongAccumulator` is used under no lock contention, only a single `volatile base` variable and CAS operations are used, just like in `AtomicLong`.
However if CAS fails, this class falls back to an array of values.
You don't want to see the implementation, it's 90 lines long, occasionally with 8 levels of nesting.
What you need to know is that it uses simple algorithm to always assign given thread to the same cell (improves cache locality).
From now on this thread has its own, almost private copy of counter.
It shares this copy with couple of other threads, but not with all of them - they have their own cells.
So what you end up in the end is an array of semi-calculated counters which must be aggregated.
This is what you saw in `get()` method.

This brings us again to the question, what kind of operators (`op`) are permitted in `LongAccumulator`.
We know that the same sequence of accumulations under low load will result e.g. in:

```java
((I op A) op B)  //get()
```

Which means all values are aggregated in base variable and no counter array is used.
However under high load, `LongAccumulator` will split work e.g. into two buckets (cells) and later accumulate buckets as well:

```java
(I op A)              //cell 1
(I op B)              //cell 2

(I op A) op (I op B)  //get()
```

or vice-versa:

```java
(I op B)              //cell 1
(I op A)              //cell 2

(I op B) op (I op A)  //get()
```

Clearly all invocations of `get()` should yield the same result, but it all depends on the properties of `op` operator being provided (`+`, `*`, `max`, etc.)

# Commutative

We have no control over the order of cells and how they are assigned.
That's why `((I op A) op (I op B))` and `((I op B) op (I op A))` must return the same result.
More compactly we are looking for such operators `op` where `X op Y = Y op X` for every `X` and `Y`.
This means `op` must be [**commutative**](http://en.wikipedia.org/wiki/Commutative_property).

# Neutral element (identity)

Cells are logically initialized with identity (initial) value `I`.
We have no control over the number and order of cells, thus the identity value can be applied numerous times in any order.
However this is an implementation detail, so it shouldn't affect the result.
More precisely, for every `X` and any `op`:

```java
X op I = I op X = X
```

Which means the identity (initial) value `I` must be a neutral value for every argument `X` to operator `op`.

# Associativity

Assume we have the following cells:

```java
I op A                              // cell 1
I op B                              // cell 2
I op C                              // cell 3
((I op A) op (I op B)) op (I op C)  //get()
```

but the next time they were arranged differently

```java
I op C                              // cell 1
I op B                              // cell 2
I op A                              // cell 2
((I op C) op (I op B)) op (I op A)  //get()
```

Knowing that `op` is commutative and `I` is a neutral element, we can prove that (for every `A`, `B` and `C`):

```java
((I op A) op (I op B)) op (I op C) = ((I op C) op (I op B)) op (I op A)
(A op B) op C = (C op B) op A
(A op B) op C = A op (B op C)
```

Which proves that `op` must be **[associative](http://en.wikipedia.org/wiki/Associative_property)** in order for `LongAccumulator` to actually work.

# Wrap up

`LongAccumulator` and `DoubleAccumulator` are highly specialized classes new in JDK 8.
JavaDoc is quite vaque but we tried to prove properties that an operator and initial value must fullfil in order for them to do their job.
We know that the operator must be *associative*, *commutative* and have a neutral element.
It would have been so much better if JavaDoc clearly stated that it must be an [abelian monoid](http://en.wikipedia.org/wiki/Monoid#Commutative_monoid) ;-).
Nevertheless for practical purposes these accumulators work only for adding, multiplying, min and max, as these are the only useful operators (with appropriate neutral element) that play well.
Subtracting and dividing for example is not associative and commutative, thus can't possibly work.
To make matters worse, accumulators would simply behave undeterministically.
