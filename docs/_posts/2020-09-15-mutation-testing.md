---
category: podcast
title: "#15: Mutation testing"
permalink: /15
tags: mutation-testing tdd pitest
description: >
    Imagine I wrote a script that takes your codebase and removes a random line.
    Fairly simple.
    Or maybe some more subtle change, like replacing plus with minus operator?
    Or switching `x` and `y` parameters with each other?
    OK, so now my script builds your project.
    Most of the time it will fail the compilation or test phase.
    But what if the build succeeds?
    Well, apparently your test suite is not covering some lines?

    OK, but what if my script only removes or alters lines covered by tests?
    How is it possible that the build still succeeds?
    Turns out your tests aren't as good as you think.
    And I just described mutation testing that discovers that.

---

{% include player.html episode_id="4xfgxHrelMvrHYzry9qOU6" %}

{{ page.description }}

Your code coverage metric doesn't tell the full story.
The fact that a given line was executed during the unit testing phase doesn't mean it's thoroughly tested!
Maybe you skipped an assertion or forgot an edge case?
How can you automatically tell a test is thorough?
Well, it's definitely not if random changes to the production code don't trigger failures.
Changes, known as _mutations_.
Tools that perform mutation testing have a wide range of such defects:

* removing lines and expressions
* inverting condition
* forcing different return values
* changing constants
* ...and so on

If a test suite succeeded with a mutation, we say it survived - thus our tests need to be more strict.
Otherwise, we assume a developer did a good job.
In the end we get a so-called mutant score, which sounds really cool!
This is the number of killed mutations to overall number of mutations.
One is a perfect score.

## Technicalities

A good mutation testing framework needs to be quite clever.
First of all it must run cove coverage analysis.
Based on them framework chooses precisely which tests are covering which lines.
When mutating one function, there's no reason to rerun tests that never touch that function.
Secondly, framework must somehow alter our code.
This is challenging.
Theoretically the easiest way is to parse the source code and make a few changes, here and there.
In practice, surprisingly, machine code is much easier to tamper with.



## Disadvantages

Mutation testing can take a lot of time.
Mainly due to running a test suite repeatedly.
Also, you may expect many false-positives.
Last, but not least, it will not help you with code that's not covered.
It won't replace writing tests.

Moreover, if you religiously practice TDD, mutation testing is of no use.
Every feature is tested before written so it's technically impossible to write untested code.

Even if you are not using mutation testing framework on a daily basis, consider being one yourself.
What?
Well, I've seen tests that were green by accident too many times.
For example an assertion statement was used incorrectly.
If you are not sure if your tests are actually testing anything, make a random change to your codebase.
Replacing _greater than_ with _greater than or equal_ operator should cause a few tests to fail.
Ideally - just one.
If suddenly 90% of your tests failed - well, I think you are testing the same thing too many times.
If your tests are still green - you have a serious problem.


# More materials: Mutation testing tools

Copied from [Wikipedia]():

* Alloy: [MuAlloy](https://github.com/kaiyuanw/MuAlloy)
* C/C++
    * [llvm-mutate](https://eschulte.github.io/llvm-mutate/)
    * [Frama-C plugin](https://github.com/gpetiot/Frama-C-Mutation/)
    * [mull-project/mull](https://github.com/mull-project/mull)
    * [mutate_cpp](https://github.com/nlohmann/mutate_cpp)
    * [accmut](https://github.com/wangbo15/accmut)
    * [MUSIC](https://github.com/swtv-kaist/MUSIC)
    * [dextool](https://github.com/joakim-brannstrom/dextool)
    * [SRCIROR](https://github.com/TestingResearchIllinois/srciror)
    * [MART](https://github.com/thierry-tct/mart)
* C#
    * [stryker-mutator/stryker-net](https://github.com/stryker-mutator/stryker-net)
    * [ComparetheMarket/fettle](https://github.com/ComparetheMarket/fettle)
    * [Testura.Mutation](https://github.com/Testura/Testura.Mutation)
* Clojure
    * [mutant](https://github.com/jstepien/mutant)
* Crystal
    * [crytic](https://github.com/hanneskaeufler/crytic)
* Elixir
    * [JordiPolo/mutation](https://github.com/JordiPolo/mutation)
* Erlang
    * [parsifal-47/muterl](https://github.com/parsifal-47/muterl)
* Go
    * [zimmski/go-mutesting](https://github.com/zimmski/go-mutesting)
* Haskell
    * [mucheck](https://hackage.haskell.org/package/MuCheck)
    * [rudymatela/fitspec](https://github.com/rudymatela/fitspec)
* Java/JVM
    * [hcoles/pitest](https://github.com/hcoles/pitest)
    * [metamutator](https://github.com/SpoonLabs/metamutator)
    * [Major](http://mutation-testing.org)
* JavaScript
    * [stryker-mutator/stryker](https://github.com/stryker-mutator/stryker)
* PHP
    * [infection/infection](https://github.com/infection)
* Python
    * [sixty-north/cosmic-ray](https://github.com/sixty-north/cosmic-ray)
    * [boxed/mutmut](https://github.com/boxed/mutmut)
    * [xmutant.py](https://github.com/vrthra/xmutant.py)
* Ruby
    * [mbj/mutant](https://github.com/mbj/mutant)
    * [backus/mutest](https://github.com/backus/mutest)
* Rust
    * [llogiq/mutagen](https://github.com/llogiq/mutagen)
* Scala
    * [sugakandrey/scalamu](https://github.com/sugakandrey/scalamu)
    * [stryker4s](https://stryker-mutator.io/stryker4s/)
* Smalltalk
    * [pavel-krivanek/mutalk](https://github.com/pavel-krivanek/mutalk)
* Swift
    * [SeanROlszewski/muter](https://github.com/SeanROlszewski/muter)




