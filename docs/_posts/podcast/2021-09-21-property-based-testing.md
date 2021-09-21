---
title: "#50: Property-based testing: find bugs automatically by generating thousands of test cases"
category: podcast
permalink: /50
tags: property-based-testing haskell scalacheck
description: >
    Property-based testing is an approach to automatically test software against well-defined rules.
    We don't specify desired output for a few inputs.
    Instead, we barely define properties that should always hold.
    It's best explained with an example.
    How do you make sure that your compression algorithm works?
    Ordinary unit tests verify a handful of inputs that you came up with.
    If you are experienced developer, you will include edge cases.
    I mean, the weirdest inputs, like an empty string or a long sequence of the same character.
    And what are the properties of a good compression algorithm?
    Its output should takes less space, obviously.
    But even more importantly, lossless algorithm should be capable of decompression.
    What if I told you, there is software that can check these properties automatically?
    With thousands of randomized tests?
---

{% include player.html episode_id="313A2uGgQeosMewYoIhaRE" %}

{{ page.description }}

<!--
Property-based testing frameworks, do just that.
The most popular one is QuickCheck for Haskell.
Here's an example of a compression algorithm test.
You simply say: for an _arbitrary_ sequence of bytes, compressing and decompressing them should yield the same sequence.
This property essentially means that we can recover compressed data.
But rather than providing examples by hand, QuickCheck will generate thousands of randomized inputs.
It will include typical corner cases, like an empty array.
The framework's task is to falsify your assumption.
You believe you compression is reversible.
The property-based testing framework will do its best to find a broken example.
A sequence of bytes that crashes your algorithm or can't be decompressed.

Once the broken input is found, the framework typically tries to shrink it.
That's because randomized inputs can be quite large.
So the framework makes an effort to reduce the sample that falsified our assumption.
A smaller sample means easier debugging.

Property-based testing works best for heavily algorithmic tasks where properties are easy to define.
For example, compression, encryption, sorting.
Also, it works great when the system receives multiple commands changing the state.
In that case our property is simple: do not crash and remain consistent.
Barely trying to crash the application is called fuzzing.
But keeping it consistent is more interesting.
Imagine a bank account.
No matter what you do, its balance should never be negative.
Or an airplane.
No matter how many reservations you accept, the same seat should never be booked twice.
In practice, both of these invariants can be broken.
Moreover, even the simplest compression property can be falsified.
I can easily imagine input which compresses to a larger output.
Testing frameworks typically allow you to define exclusion rules to avoid false-positives.

Property-based testing has some drawbacks.
If your code is relatively slow, test will become really slow when invoked thousands of times.
Also, because inputs are randomized, test may not be reproducible.
This can be circumvented by hard-coded random seed generators that are predictable.
I already mentioned QuickCheck for Haskell.
However, over time dozens of ports were created for Java, JavaScript, Python, etc.
This type of technique is not universal for any language.
However, I was often surprised what kind of edge-cases the framework found.
Typically these are malformed or otherwise unusual inputs.

That's it, thanks for listening, bye!

-->

# More materials

* [The Design and Use of QuickCheck](https://begriffs.com/posts/2017-01-14-design-use-quickcheck.html)
* [Property-based testing with ScalaCheck - custom generators](/2014/09/property-based-testing-with-scalacheck.html)
* [Property-based testing with Spock](https://nurkiewicz.com/2014/09/property-based-testing-with-spock.html)
* [What is Property Based Testing?](https://hypothesis.works/articles/what-is-property-based-testing/)
* [QuickCheck](https://en.wikipedia.org/wiki/QuickCheck)
* [QuickCheck in Every Language](https://hypothesis.works/articles/quickcheck-in-every-language/)
    * C: [theft](https://github.com/silentbicycle/theft)
    * C++: [CppQuickCheck](https://github.com/grogers0/CppQuickCheck)
    * Clojure: [test.check](https://github.com/clojure/test.check)
    * Coq: [QuickChick](https://github.com/QuickChick/QuickChick)
    * F#: [FsCheck](https://github.com/fscheck/FsCheck)
    * Go: [gopter](https://github.com/leanovate/gopter)
    * Haskell: [Hedgehog](https://hackage.haskell.org/package/hedgehog)
    * Java: [QuickTheories](https://github.com/NCR-CoDE/QuickTheories)
    * JavaScript: [jsverify](https://github.com/jsverify/jsverify)
    * PHP: [Eris](https://github.com/giorgiosironi/eris)
    * Python: [Hypothesis](https://hypothesis.works)
    * Ruby: [Rantly](https://github.com/abargnesi/rantly)
    * Rust: [Quickcheck](https://github.com/BurntSushi/quickcheck)
    * Scala: [ScalaCheck](https://www.scalacheck.org/)
    * Swift: [Swiftcheck](https://github.com/typelift/SwiftCheck)
