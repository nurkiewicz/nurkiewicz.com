---
title: "#49: Functional programming: academic research or new hope for the industry?"
category: podcast
permalink: /49
tags: functional-programming currying memoization higher-order-function monad lambda-expression map-reduce immutability
description: >
    Functional programming means programming using functions.
    See, I need much less than 256 seconds for that!
    Unfortunately, this definition is as useful as saying that object-oriented programming means programming with objects.
    So let's dive deeper.
    First of all, I mean *pure* functions as defined by mathematicians.
    In math, a function always returns the same output for a given input.
    A length of a string is a function.
    A form validator is typically a function as well.
    For the same form inputs it always returns the same result: valid or invalid.
    On the other hand, returning the current date for a given location is not a function.
    Or reading a file.
---

{% include player.html spotify_id="7eagJKitLtJlcZgfLPyywg" youtube_id="L693WOIBcfs" %}

{{ page.description }}

There is another important distinction of what is a function.
It can't have visible side effects.
For example, registering a user saves that user to the database.
First of all, storing the same user for the second time may fail or return a different ID.
In both cases, the same input produces different output.
But there is one more subtle violation.
Changing the database may influence the results of other functions.
I hope you get the idea.

Being so strict about input and output has some surprising benefits.
First of all, _memoization_.
It's a fancy name for caching.
Because one input always returns the same output, caching is perfectly safe.
Secondly, immutability.
It's an important concept in functional programming.
Data structures and objects are never modified by any function.
So for example, a function adding a new element to a list actually creates a new list with one extra element.
This sounds insane and wasteful until you start writing concurrent programs.
Concurrency is so damn hard because we must synchronize changes between threads.
But if functions can't change the state and mutate any data, the biggest issue disappears!
Moreover, if input of one function is not dependent on the output of another function, we can run them concurrently!
Or even rearrange to better utilize resources.
By definition, it won't change the outcome of the program.
That's why functional programming is gaining popularity when building scalable systems.

OK, I barely scratched the surface of functional programming so far.
Another important concept is higher order functions.
Such a functions can take functions as arguments or return functions as a result.
This sounds like an inception, but it's actually quite useful.
A simple `sort` function that takes a comparator function and a list to sort.
It's a higher order function!
It can be even more meta.
What if you forget the second argument to the `sort` function?
Code doesn't compile?
What if I told you this is a valid technique in functional programming, known as _partial application_?
Calling `sort` with only the first argument returns a more specific `sort` function.
Taking a list as input with hardcoded comparator.
This is known as _currying_ and is a very powerful technique.

There are many more important concepts in functional programming.
For example lambda expressions, which are anonymous functions defined ad-hoc.
Or monads, which abstract away impure context in which the program runs.
Actually, handling the outside world (the input/output) is quite complex in pure functional languages.
But monads deserve a separate episode.

That's it, thanks for listening, bye!

# More materials

* [Functional programming](https://en.wikipedia.org/wiki/Functional_programming)
* [Learn You a Haskell for Great Good!](http://learnyouahaskell.com/chapters)
* [Memoization](https://en.wikipedia.org/wiki/Memoization)
* [MapReduce](/11) framework was heavily inspired by functional programming
