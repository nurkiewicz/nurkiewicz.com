---
layout: post
title: Building extremely large in-memory InputStream for testing purposes
date: '2014-07-21T19:33:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- guava
modified_time: '2014-07-21T22:21:01.303+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8706947186580666617
blogger_orig_url: https://www.nurkiewicz.com/2014/07/building-extremely-large-in-memory.html
---

For some reason I needed extremely large, possibly even infinite `InputStream` that would simply return the same `byte[]` over and over.
This way I could produce insanely big stream of data by repeating small sample.
Sort of similar functionality can be found in Guava: [`Iterable<T> Iterables.cycle(Iterable<T>)`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/collect/Iterables.html#cycle(java.lang.Iterable)) and [`Iterator<T> Iterators.cycle(Iterator<T>)`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/collect/Iterators.html#cycle(java.lang.Iterable)).
For example if you need an infinite source of `0` and `1`, simply say `Iterables.cycle(0, 1)` and get `0, 1, 0, 1, 0, 1...`
infinitely.
Unfortunately I haven't found such utility for `InputStream`, so I jumped into writing my own.
This article documents many mistakes I made during that process, mostly due to overcomplicating and overengineering straightforward solution.

We don't really need an infinite `InputStream`, being able to create very large one (say, 32 GiB) is enough.
So we are after the following method:

```java
public static InputStream repeat(byte[] sample, int times)
```

It basically takes `sample` array of bytes and returns an `InputStream` returning these bytes.
However when `sample` runs out, it rolls over, returning the same bytes again - this process is repeated given number of times, until `InputStream` signals end.
One solution that I haven't really tried but which seems most obvious:

```java
public static InputStream repeat(byte[] sample, int times) {
    final byte[] allBytes = new byte[sample.length * times];
    for (int i = 0; i < times; i++) {
        System.arraycopy(sample, 0, allBytes, i * sample.length, sample.length);
    }
    return new ByteArrayInputStream(allBytes);
}
```

I see you laughing there!
If `sample` is 100 bytes and we need 32 GiB of input repeating these 100 bytes, generated `InputStream` shouldn't really allocate 32 GiB of memory, we must be more clever here.
As a matter of fact `repeat()` above has another subtle bug.
Arrays in Java are limited to 2<sup>31</sup>-1 entries (`int`), 32 GiB is way above that.
The reason this program compiles is a silent integer overflow here: `sample.length * times`.
This multiplication doesn't fit in `int`.

OK, let's try something that at least theoretically can work.
My first idea was as follows: what if I create many `ByteArrayInputStream`s sharing the same `byte[] sample` (they don't do an eager copy) and somehow join them together?
Thus I needed some `InputStream` adapter that could take arbitrary number of underlying `InputStream`s and chain them together - when first stream is exhausted, switch to next one.
This awkward moment when you look for something in Apache Commons or Guava and apparently [it was in the JDK forever](http://stackoverflow.com/a/14295156)...
[`java.io.SequenceInputStream`](http://docs.oracle.com/javase/8/docs/api/java/io/SequenceInputStream.html) is almost ideal.
However it can only chain precisely two underlying `InputStream`s.
Of course since `SequenceInputStream` is an `InputStream` itself, we can use it recursively as an argument to outer `SequenceInputStream`.
Repeating this process we can chain arbitrary number of `ByteArrayInputStream`s together:

```java
public static InputStream repeat(byte[] sample, int times) {
    if (times <= 1) {
        return new ByteArrayInputStream(sample);
    } else {
        return new SequenceInputStream(
                new ByteArrayInputStream(sample),
                repeat(sample, times - 1)
        );
    }
}
```

If `times` is 1, just wrap `sample` in `ByteArrayInputStream`.
Otherwise use `SequenceInputStream` recursively.
I think you can immediately spot what's wrong with this code: too deep recursion.
Nesting level is the same as `times` argument, which will reach millions or even billions.
There must be a better way.
Luckily minor improvement changes recursion depth from O(n) to O(logn):

```java
public static InputStream repeat(byte[] sample, int times) {
    if (times <= 1) {
        return new ByteArrayInputStream(sample);
    } else {
        return new SequenceInputStream(
                repeat(sample, times / 2),
                repeat(sample, times - times / 2)
        );
    }
}
```

Honestly this was the first implementation I tried.
It's a simple [application of *divide and conquer*](http://en.wikipedia.org/wiki/Divide_and_conquer_algorithms) principle, where we produce result by evenly splitting it into two smaller sub-problems.
Looks clever, but there is one issue: it's easy to prove we create t (`t = times`) `ByteArrayInputStreams` and O(t) `SequenceInputStream`s.
While `sample` byte array is shared, millions of various `InputStream` instances are wasting memory.
This leads us to alternative implementation, creating just one `InputStream`, regardless value of `times`:

```java
import com.google.common.collect.Iterators;
import org.apache.commons.lang3.ArrayUtils;

public static InputStream repeat(byte[] sample, int times) {
    final Byte[] objArray = ArrayUtils.toObject(sample);
    final Iterator<Byte> infinite = Iterators.cycle(objArray);
    final Iterator<Byte> limited = Iterators.limit(infinite, sample.length * times);
    return new InputStream() {
        @Override
        public int read() throws IOException {
            return limited.hasNext() ?
                    limited.next() & 0xFF :
                    -1;
        }
    };
}
```

We will use `Iterators.cycle()` after all.
But before we have to translate `byte[]` into `Byte[]` since iterators can only work with objets, not primitives.
There is no idiomatic way to turn array of primitives to array of boxed types, so I use [`ArrayUtils.toObject(byte[])`](http://commons.apache.org/proper/commons-lang/apidocs/org/apache/commons/lang3/ArrayUtils.html#toObject(byte%5B%5D)) from Apache Commons Lang.
Having an array of objects we can create an `infinite` iterator that cycles through values of `sample`.
Since we don't want an infinite stream, we cut off infinite iterator using [`Iterators.limit(Iterator<T>, int)`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/collect/Iterators.html#limit(java.util.Iterator,%20int)), again from Guava.
Now we just have to bridge from `Iterator<Byte>` to `InputStream` - after all semantically they represent the same thing.

This solution suffers two problems.
First of all it produces tons of garbage due to unboxing.
Garbage collection is not that much concerned about dead, short-living objects, but still seems wasteful.
Second issue we already faced previously: `sample.length * times` multiplication can cause integer overflow.
It can't be fixed because `Iterators.limit()` takes `int`, not `long` - for no good reason.
BTW we avoided third problem by doing bitwise *and* with `0xFF` - otherwise `byte` with value `-1` would signal end of stream, which is not the case.
`x & 0xFF` is correctly translated to unsigned `255` (`int`).

So even though implementation above is short and sweet, declarative rather than imperative, it's too slow and limited.
If you have a C background, I can imagine how uncomfortable you were seeing me struggle.
After all the most straightforward, painfully simple and low-level implementation was the one I came up with last:

```java
public static InputStream repeat(byte[] sample, int times) {
    return new InputStream() {
        private long pos = 0;
        private final long total = (long)sample.length * times;

        public int read() throws IOException {
            return pos < total ?
                    sample[(int)(pos++ % sample.length)] :
                    -1;
        }
    };
}
```

GC free, pure JDK, fast and simple to understand.
Let this be a lesson for you: start with the simplest solution that jumps to your mind, don't overengineer and don't be too smart.
My previous solutions, declarative, functional, immutable, etc. - maybe they looked clever, but they were neither fast nor easy to understand.

The utility we just developed was not just a toy project, it will be used later in [subsequent article](http://www.nurkiewicz.com/2014/07/testing-code-for-excessively-large.html).
