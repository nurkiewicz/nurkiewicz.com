---
layout: post
title: Property-based testing with Spock
date: '2014-09-18T11:43:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- testing
- groovy
- Spock
modified_time: '2014-09-19T11:53:02.030+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3940304002295354954
blogger_orig_url: https://www.nurkiewicz.com/2014/09/property-based-testing-with-spock.html
---

*Property based testing* is an alternative approach to testing, complementing *example based testing*.
The latter is what we've been doing all our lives: exercising production code against "examples" - inputs we think are representative.
Picking these examples is an art on its own: "ordinary" inputs, edge cases, malformed inputs, etc. But why are we limiting ourselves to just few examples?
Why not test hundreds, millions...
**ALL** inputs?
There are at least two difficulties with that approach:

1.  Scale.
    A pure function taking just one `int` input would require 4 billion tests.
    This means few hundred gigabytes of test source code and several months of execution time.
    Square it if a function takes two `int`s.
    For `String` it practically goes to infinity.
2.  Assume we have these tests, executed on a quantum computer or something.
    How do you know the expected result for each particular input?
    You either enter it by hand (good luck) or generate expected output.
    By *generate* I mean write a program that produces expected value for every input.
    But aren't we testing such program already in the first place?
    Are we suppose to write better, error-free version of code under test just to test it?
    Also known as [ugly mirror antipattern](http://jasonrudolph.com/blog/2008/07/30/testing-anti-patterns-the-ugly-mirror/).

So you understand testing every single input, although ideal, is just a mental experiment, impossible to implement.
That being said property based testing tries to get as close as possible to this testing nirvana.
Issue \#1 is solved by slamming code under test with hundreds or thousands of random inputs.
Not all of them, not even a fraction.
But a good, *random* representation.

Issue \#2 is surprisingly harder.
Property based testing can generate random arguments, but it can't figure out what should be the expected outcome for that random input.
Thus we need a different mechanism, giving name to whole philosophy.
We have to come up with properties (invariants, behaviours) that code under test exhibits no matter what the input is.
This sounds very theoretically, but there are many such properties in various scenarios:

1.  [Absolute value](http://en.wikipedia.org/wiki/Absolute_value) of *any number* should never be negative
2.  Encoding and decoding *any string* should yield the same `String` back for every symmetric encoding
3.  Optimized version of some old algorithm should produce the same result as the old one *for any input*
4.  Total money in a bank should remain the same after *arbitrary number* of intra-bank transactions in *any order*

As you can see there are many properties we can think of that do not mention specific example inputs.
This is not exhaustive and strict testing.
It's more like sampling and making sure samples are "sane".
There are many, many libraries supporting property based testing for virtually every language.
In this article we will explore Spock and ScalaCheck later.

# Spock + custom data generators

Spock does not support property based testing out-of-the-box.
However with help from [data driven testing](http://spock-framework.readthedocs.org/en/latest/data_driven_testing.html) and 3rd-party data generators we can go quite far.
Data tables in Spock can be generalized into so-called [data pipes](http://spock-framework.readthedocs.org/en/latest/data_driven_testing.html#data-pipes):

```groovy
def 'absolute value of #value should not be negative'() {
    expect:
    value.abs() >= 0

    where:
    value << randomInts(100)
}

private static def List<Integer> randomInts(int count) {
    final Random random = new Random()
    (1..count).collect { random.nextInt() }
}
```

Code above will generate 100 random integers and make sure for all of them `.abs()` is non-negative.
You might think this test is quite dumb, but to a great surprise it actually discovers one bug!
But first let's kill some boilerplate code.
Generating random inputs, especially more complex, is cumbersome and boring.
I found two libraries that can help us.
[spock-genesis](https://github.com/Bijnagte/spock-genesis):

```groovy
import spock.genesis.Gen

def 'absolute value of #value should not be negative'() {
    expect:
    value.abs() >= 0

    where:
    value << Gen.int.take(100)
}
```

Looks great, but if you want to generate e.g. lists of random integers, `net.java.quickcheck` has nicer API and is not Groovy-specific:

```groovy
import static net.java.quickcheck.generator.CombinedGeneratorsIterables.someLists
import static net.java.quickcheck.generator.PrimitiveGenerators.integers

def 'sum of non-negative numbers from #list should not be negative'() {
    expect:
    list.findAll{it >= 0}.sum() >= 0

    where:
    list << someLists(integers(), 100)
}
```

This test is interesting.
It makes sure sum of non-negative numbers is never negative - by generating 100 lists of randoms `int`s.
Sounds reasonable.
However multiple tests are failing.
First of all due to integer overflow sometimes two positive `int`s add up to a negative one.
Duh!
Another type of failure that was discovered is actually frightening.
While `[1,2,3].sum()` is 6, obviously, `[].sum()` is...
`null` ([WAT?](http://jira.codehaus.org/browse/GROOVY-2411))

As you can see even silliest and most basic property based tests can be useful in finding unusual corner cases in your data.
But wait, I said testing absolute of `int` discovered one bug.
Actually it didn't, because of poor (too "random") data generators, not returning known edge values in the first place.
We will fix that in the [next article](http://www.nurkiewicz.com/2014/09/property-based-testing-with-scalacheck.html).
