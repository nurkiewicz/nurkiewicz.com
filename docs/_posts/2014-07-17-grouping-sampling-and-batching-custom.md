---
layout: post
title: Grouping, sampling and batching - custom collectors in Java 8
date: '2014-07-17T23:20:00.001+02:00'
author: Tomasz Nurkiewicz
tags:
- groovy
- java8
- Spock
modified_time: '2016-10-29T14:45:02.763+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1716414012264105388
blogger_orig_url: https://www.nurkiewicz.com/2014/07/grouping-sampling-and-batching-custom.html
---

Continuing [first article](http://www.nurkiewicz.com/2014/07/introduction-to-writing-custom.html), this time we will write some more useful custom collectors: for grouping by given criteria, sampling input, batching and sliding over with fixed size window.

## Grouping (counting occurrences, histogram)

Imagine you have a collection of some items and you want to calculate how many times each item (with respect to `equals()`) appears in this collection.
This can be achieved using [`CollectionUtils.getCardinalityMap()`](https://draft.blogger.com/CollectionUtils.html#getCardinalityMap(java.lang.Iterable)) from Apache Commons Collections.
This method takes an `Iterable<T>` and returns `Map<T, Integer>`, counting how many times each item appeared in the collection.
However sometimes instead of using `equals()` we would like to group by an arbitrary attribute of input `T`.
For example say we have a list of `Person` objects and we would like to compute the number of males vs. females (i.e.
`Map<Sex, Integer>`) or maybe an age distribution.
There is a built-in collector [`Collectors.groupingBy(Function<T, K> classifier)`](http://docs.oracle.com/javase/8/docs/api/java/util/stream/Collectors.html#groupingBy-java.util.function.Function-) - however it returns a map from key to all items mapped to that key.
See:

```java
import static java.util.stream.Collectors.groupingBy;

//...

final List<Person> people = //...
final Map<Sex, List<Person>> bySex = people
        .stream()
        .collect(groupingBy(Person::getSex));
```

It's valuable, but in our case unnecessarily builds two `List<Person>`.
I only want to know the number of people.
There is no such collector built-in, but we can compose it in a fairly simple manner:

```java
import static java.util.stream.Collectors.counting;
import static java.util.stream.Collectors.groupingBy;

//...

final Map<Sex, Long> bySex = people
        .stream()
        .collect(
                groupingBy(Person::getSex, HashMap::new, counting()));
```

This overloaded version of `groupingBy()` takes three parameters.
First one is the key (*classifier*) function, as previously.
Second argument creates a new map, we'll see shortly why it's useful.
`counting()` is a nested collector that takes all people with same sex and combines them together - in our case simply counting them as they arrive.
Being able to choose map implementation is useful e.g. when building age histogram.
We would like to know how many people we have at given age - but age values should be sorted:

```java
final TreeMap<Integer, Long> byAge = people
    .stream()
    .collect(
            groupingBy(Person::getAge, TreeMap::new, counting()));

byAge
        .forEach((age, count) ->
                System.out.println(age + ":\t" + count));
```

We ended up with a `TreeMap` from age (sorted) to count of people having that age.

## Sampling, batching and sliding window

[`IterableLike.sliding()`](http://www.scala-lang.org/api/current/#scala.collection.IterableLike) method in Scala allows to view a collection through a sliding fixed-size window.
This window starts at the beginning and in each iteration moves by given number of items.
Such functionality, missing in Java 8, allows several useful operators like computing [moving average](http://en.wikipedia.org/wiki/Moving_average), splitting big collection into batches (compare with [`Lists.partition()` in Guava](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/collect/Lists.html#partition(java.util.List,%20int))) or sampling every n-th element.
We will implement collector for Java 8 providing similar behaviour.
Let's start from unit tests, which should describe briefly what we want to achieve:

```groovy
import static com.nurkiewicz.CustomCollectors.sliding

@Unroll
class CustomCollectorsSpec extends Specification {

    def "Sliding window of #input with size #size and step of 1 is #output"() {
        expect:
        input.stream().collect(sliding(size)) == output

        where:
        input  | size | output
        []     | 5    | []
        [1]    | 1    | [[1]]
        [1, 2] | 1    | [[1], [2]]
        [1, 2] | 2    | [[1, 2]]
        [1, 2] | 3    | [[1, 2]]
        1..3   | 3    | [[1, 2, 3]]
        1..4   | 2    | [[1, 2], [2, 3], [3, 4]]
        1..4   | 3    | [[1, 2, 3], [2, 3, 4]]
        1..7   | 3    | [[1, 2, 3], [2, 3, 4], [3, 4, 5], [4, 5, 6], [5, 6, 7]]
        1..7   | 6    | [1..6, 2..7]
    }

    def "Sliding window of #input with size #size and no overlapping is #output"() {
        expect:
        input.stream().collect(sliding(size, size)) == output

        where:
        input | size | output
        []    | 5    | []
        1..3  | 2    | [[1, 2], [3]]
        1..4  | 4    | [1..4]
        1..4  | 5    | [1..4]
        1..7  | 3    | [1..3, 4..6, [7]]
        1..6  | 2    | [[1, 2], [3, 4], [5, 6]]
    }

    def "Sliding window of #input with size #size and some overlapping is #output"() {
        expect:
        input.stream().collect(sliding(size, 2)) == output

        where:
        input | size | output
        []    | 5    | []
        1..4  | 5    | [[1, 2, 3, 4]]
        1..7  | 3    | [1..3, 3..5, 5..7]
        1..6  | 4    | [1..4, 3..6]
        1..9  | 4    | [1..4, 3..6, 5..8, 7..9]
        1..10 | 4    | [1..4, 3..6, 5..8, 7..10]
        1..11 | 4    | [1..4, 3..6, 5..8, 7..10, 9..11]
    }

    def "Sliding window of #input with size #size and gap of #gap is #output"() {
        expect:
        input.stream().collect(sliding(size, size + gap)) == output

        where:
        input | size | gap | output
        []    | 5    | 1   | []
        1..9  | 4    | 2   | [1..4, 7..9]
        1..10 | 4    | 2   | [1..4, 7..10]
        1..11 | 4    | 2   | [1..4, 7..10]
        1..12 | 4    | 2   | [1..4, 7..10]
        1..13 | 4    | 2   | [1..4, 7..10, [13]]
        1..13 | 5    | 1   | [1..5, 7..11, [13]]
        1..12 | 5    | 3   | [1..5, 9..12]
        1..13 | 5    | 3   | [1..5, 9..13]
    }

    def "Sampling #input taking every #nth th element is #output"() {
        expect:
        input.stream().collect(sliding(1, nth)) == output

        where:
        input  | nth | output
        []     | 1   | []
        []     | 5   | []
        1..3   | 5   | [[1]]
        1..6   | 2   | [[1], [3], [5]]
        1..10  | 5   | [[1], [6]]
        1..100 | 30  | [[1], [31], [61], [91]]
    }
}
```

Using [data driven tests in Spock](http://spock-framework.readthedocs.org/en/latest/data_driven_testing.html) I managed to write almost 40 test cases in no-time, succinctly describing all requirements.
I hope these are clear for you, even if you haven't seen this syntax before.
I already assumed existence of handy factory methods:

```java
public class CustomCollectors {

    public static <T> Collector<T, ?, List<List<T>>> sliding(int size) {
        return new SlidingCollector<>(size, 1);
    }

    public static <T> Collector<T, ?, List<List<T>>> sliding(int size, int step) {
        return new SlidingCollector<>(size, step);
    }

}
```

The fact that collectors receive items one after another makes are job harder.
Of course first collecting the whole list and sliding over it would have been easier, but sort of wasteful.
Let's build result iteratively.
I am not even pretending this task can be parallelized in general, so I'll leave `combiner()` unimplemented:

```java
public class SlidingCollector<T> implements Collector<T, List<List<T>>, List<List<T>>> {

    private final int size;
    private final int step;
    private final int window;
    private final Queue<T> buffer = new ArrayDeque<>();
    private int totalIn = 0;

    public SlidingCollector(int size, int step) {
        this.size = size;
        this.step = step;
        this.window = max(size, step);
    }

    @Override
    public Supplier<List<List<T>>> supplier() {
        return ArrayList::new;
    }

    @Override
    public BiConsumer<List<List<T>>, T> accumulator() {
        return (lists, t) -> {
            buffer.offer(t);
            ++totalIn;
            if (buffer.size() == window) {
                dumpCurrent(lists);
                shiftBy(step);
            }
        };
    }

    @Override
    public Function<List<List<T>>, List<List<T>>> finisher() {
        return lists -> {
            if (!buffer.isEmpty()) {
                final int totalOut = estimateTotalOut();
                if (totalOut > lists.size()) {
                    dumpCurrent(lists);
                }
            }
            return lists;
        };
    }

    private int estimateTotalOut() {
        return max(0, (totalIn + step - size - 1) / step) + 1;
    }

    private void dumpCurrent(List<List<T>> lists) {
        final List<T> batch = buffer.stream().limit(size).collect(toList());
        lists.add(batch);
    }

    private void shiftBy(int by) {
        for (int i = 0; i < by; i++) {
            buffer.remove();
        }
    }

    @Override
    public BinaryOperator<List<List<T>>> combiner() {
        return (l1, l2) -> {
            throw new UnsupportedOperationException("Combining not possible");
        };
    }

    @Override
    public Set<Characteristics> characteristics() {
        return EnumSet.noneOf(Characteristics.class);
    }

}
```

I spent quite some time writing this implementation, especially correct `finisher()` so don't be frightened.
The crucial part is a `buffer` that collects items until it can form one sliding window.
Then "oldest" items are discarded and window slides forward by `step`.
I am not particularly happy with this implementation, but tests are passing.
`sliding(N)` (synonym to `sliding(N, 1)`) will allow calculating moving average of `N` items.
`sliding(N, N)` splits input into batches of size `N`.
`sliding(1, N)` takes every N-th element (samples).
I hope you'll find this collector useful, enjoy!
