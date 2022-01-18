---
title: "#66: Aspect-oriented programming: another level of code modularization"
category: podcast
permalink: /66
tags: aop aspectj security
description: >
    DRY, or _don't repeat yourself_ is a common principle in pSpring AOP riddlerogramming.
    That's why we invented functions and objects.
    But some sources of duplication are really hard to get rid of.
    Well, sometimes it's even hard to realize there's duplication in the first place!
    Common examples are logging, validation, checking security, starting a transaction.
    Often, these are one-liners that are too simple to extract.
    Too mundane too bother.
    And too ubiquitous to forget.
---

{% include player.html episode_id="0LLY25mWRzPV7Uz1DtR3Ht" %}

{{ page.description }}

<!--
Let's take a concrete example.
Every time your code returns a `SocialSecurityNumber` object, it must belong to a logged-in user.
Returning someone else's number is a huge security hole.
So every place in code that returns that object must have a security check.
It's a simple `if` statement, throwing an exception when necessary.

Here's the problem: this one-liner must appear in every single method returning `SocialSecurityNumber`.
Forget it once and your whole application is compromised.
With aspect-oriented programming (AOP for short), we can extract such logic.
It's a declarative language on top of your normal code.
We can simply say, for example: find me all methods returning `SocialSecurityNumber`.
I don't care where they are, catch them all.
And put this extra logic at the end of each method.
Transparently.

AOP framework will inject your custom code during compilation or at runtime.
This extra security logic is invisible in the source code.
But AOP makes sure it's applied everywhere.
Even in new functions written by oblivious developers.

There are plenty of use-cases for AOP.

* Want to log every exception thrown from a method inside a given namespace?
* Maybe a method should fail when invoked by a certain object?
* Or maybe you want to start a new database transaction if a function has `transactional` in its name?
* Finally, what about adding retries to every method calling RESTful API?

All of these so-called cross-cutting concerns can be implemented with a few lines of the AOP code.
Without AOP your business logic would be cluttered with non-essential plumbing.

Typically, AOP frameworks either modify code during compilation or at runtime.
The opponents of AOP point out that reading code becomes less obvious.
Indeed, code that runs on production is not the same as the one you see in your editor.
This adds an extra level of magic.
With high-level frameworks like Spring, an insane amount of logic is hidden in aspects.

So as always, there are tradeoffs.
On one hand, we'd like to hide the glue code of security, transactions, resiliency, etc.
On the other hand, what you see is not what you get.
Moreover, unit testing may become less reliable.

Also, AOP is famously difficult to debug.
An expression that defines where to apply an aspect is known as pointcut.
Pointcuts are very tricky to write.
Moreover, quite a few times I saw aspects misconfigured or accidentally disabled.
Suddenly, your security rules are ignored and transactions are not committed.
Not a situation where you want to be.

Every time you'd like to take advantage of AOP, weigh the pros and cons.
I tend to use AOP when it's obvious, mature, and makes code much more readable.

That's it, thanks for listening, bye!
-->

# More materials

* [Aspect-oriented programming](https://en.wikipedia.org/wiki/Aspect-oriented_programming) on Wikipedia
* [AspectJ](https://www.eclipse.org/aspectj/), AOP framework for Java
* [Aspect Oriented Programming with Spring](https://docs.spring.io/spring-framework/docs/5.3.x/reference/html/core.html#aop)
* [Don't repeat yourself](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself) on Wikipedia
* [Spring AOP riddle](https://nurkiewicz.com/2009/08/spring-aop-riddle.html)
