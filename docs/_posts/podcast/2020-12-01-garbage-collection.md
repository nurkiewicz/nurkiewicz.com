---
category: podcast
title: "#23: Garbage collection: how automatic memory management makes writing software much easier"
redirect_from:
  - /23
tags: gc lisp
description: >
    Creating new objects, arrays or strings is so straightforward that we often forget what happens underneath.
    And I don't mean trying to figure out what `this` refers to in JavaScript objects.
    I mean: memory management.
    On each request we create a ton of objects.
    A server can easily allocate hundreds of megabytes of memory.
    Per second.
    Memory is cheap and there's a lot of it.
    But it's not infinite.
    How come we can simply call `new Object()` over and over again, taking more and more memory from our computer?
    Many objects are no longer needed a few milliseconds after they're created.
    What happens to the memory they occupy?
    We take for granted what was thought to be almost impossible: automatic memory management.
---

{% include player.html spotify_id="35G1SNLsaGlJiWMHSqWUpf" youtube_id="uJ11kAzjva4" %}

{{ page.description }}



Back in the old days of C and C++, every object we created had to be manually freed.
It seems hard to imagine.
Every time you created a new instance of almost anything, you had to remember to destroy that.
Seriously, every single `Date` object, every string, every lambda function, every breadth you take.
When there is `new`, there has to be corresponding `delete` exactly once.
Forget about freeing memory and you get a memory leak.
Your application consumes more and more memory, even though you don' use and have no access to it.
Eventually it crashes.

What if your programming language could somehow figure out that you no longer need a certain object?
Cleaning up obsolete objects is called _garbage collection_.
How can you discover that an object is not needed anymore?
Well, no-one uses it, I mean, has a pointer or reference to it.
For example, when you detach a piece of DOM or remove something from a dictionary.
How can you tell no-one references a certain object?
Well, you can put a small counter next to each and every object.
This counter tells how many other objects can access said objects.
If this counter falls to zero, there is no place in our codebase that use said object.
It is considered garbage.

This method has one serious drawback.
If two objects are referencing each other, but nothing else references either of them - garbage collector will not touch them.
Despite these weaknesses, reference counting is still used in multiple languages.
However, most of them have some mechanisms to reclaim cycles.

More robust approach is tracing.
This family of algorithms scavenges through all _reachable_ objects, starting from `main` function.
Everything that was reached directly or indirectly is kept alive.
Everything that's left - is garbage.
This process is quite time and memory intensive.
Therefor an empirical observation, known as generational hypothesis, was introduced.
Developers of garbage collectors realized one fact: objects either live for very short or for very long.
Short-living objects don't survive beyond single request or even single loop iteration.
Long-lived ones are kept in memory for several minutes and are unlikely to be garbage collected.
By focusing on short-lived objects we can save time ignoring long-lived ones.

Often garbage collector requires full application pause, sometimes known as stop-the-world.
This means that all requests are frozen, your application doesn't receive any data, UI hangs.
Also language runtimes with GC require much more memory in less predictable patterns.
However, memory leaks and corrupted heap are really widespread in non-managed environments.
Some believe that the lack of GC in C++ was the main reason it didn't became mainstream for general purpose programming.
Java, Python C# and Go did.

Another interesting approach is Rust.
It doesn't have a classic garbage collector.
But you don't have to manage memory yourself either.
Instead, each object has exactly one owner.
When order goes out of scope (like a local variable), everything it owned can be garbage collected.
Unless we first transfer the ownership to someone else.
In practice this allows the compiler to free memory for you.
And guarantee at compile time that no memory leaks.

That's it, thanks for listening, bye!




# More materials

* [Garbage collection](https://en.wikipedia.org/wiki/Garbage_collection_(computer_science)) on Wikipedia
* [Reference counting](https://en.wikipedia.org/wiki/Reference_counting) on Wikipedia
* [Reference counting in Swift](https://docs.swift.org/swift-book/LanguageGuide/AutomaticReferenceCounting.html#//apple_ref/doc/uid/TP40014097-CH20-XID_54)
* [Yes, Rust Has Garbage Collection, And A Fast One](https://blog.akquinet.de/2020/10/09/yes-rust-has-garbage-collection-and-a-fast-one/)


