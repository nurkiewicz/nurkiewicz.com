---
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



{% include newsletter-input.md %}
