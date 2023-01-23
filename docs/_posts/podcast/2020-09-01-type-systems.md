---
category: podcast
title: "#14: Static, Dynamic, Strong and Weak Type Systems"
redirect_from:
  - /14
tags: type-systems ruby powershell python java c# groovy
description: >
    When choosing or learning a new programming language, type system should be your first question.
    How strict is that language when types don't really match?
    Will there be a conservative, slow and annoying compiler?
    Or maybe a fast feedback loop, often resulting in crashes at runtime?
    And also, is the language runtime trusting you know what you are doing, even if you don't?
    Or maybe it's babysitting you, making it hard to write fast, low-level code?
    Believe it or not, I just described static, dynamic, weak and strong typing.

---

{% include player.html spotify_id="3ryE77MvuGwE08S9q6jv6n" youtube_id="7S-TymsA_6Y" %}

{{ page.description }}


# Static typing

Languages with static typing are quite conservative.
If you have a variable that's known to be an integer, compiler will prevent using it in another context.
Integer cannot be interpreted as a date, string, or an object.
If a function expects a certain type, compiler will not let you to pass a different one.
Statically typed languages catch many bugs at compile type, so you can avoid excessive test cases or manual testing.
Moreover, types help navigating code, so static typing is preferred in large, complex codebases.
On the other hand, when prototyping or writing one-off scripts, static typing is annoying.
Examples of statically typed languages are: Java, C, C++, C#, Go, Rust and of course, Haskell.
Also, COBOL is statically typed, as well as Solidity, the language of Ethereum.

# Dynamic typing

In dynamically typed languages the compiler is much less strict.
Passing a number where an array was expected?
Sure!
Assigning a lambda expression to date?
Of course!
Well, these are most likely bugs.
However, some languages and runtimes will do their best to run... something.
For example they may coerce a single number to an array with one element.
Or assume that a lambda expression, when executed, *will* return a date.
These languages are quite liberal to allow fast development, fast compilation (if any) and fast results.
If you make a type mistake, it's caught at runtime and you can quickly fix it.
The lack of type information in the source code makes it a little bit harder to maintain dynamic codebases.
But writing is much faster.
Examples of dynamically typed languages are: JavaScript, perl, PowerShell, Ruby, Python and Groovy.
Also Smalltalk, the father of object-oriented programming and Lisp, the father of functional programming.

# Strong typing

Now let's talk about strong vs. weak typing.
Contrary to some beliefs, strong does not equal static.
As a matter of fact, these type systems are independent of each other.
There can be static but weak type system (for example C and C++).
Also dynamically, but strongly typed language is possible (for example Ruby and Python).
OK, so what's a strongly typed language?
The definition is kind of blurry.
But in general, it's a language where types are strictly guarded, even at runtime.
For example, Python is dynamically typed, but trying to add string to int yields a type error.
The same goes for Java: even if you somehow hacked around the type system, the runtime will discover it.
Interestingly C# is sometimes referred as weakly typed due to `unsafe` blocks.

# Weak typing

So what is weak typing?
In this situation the runtime is very liberal and allows generally unsafe, but useful operations.
An example would be C that supports arbitrary casting.
Turns out viewing a floating point number as a sequence of bytes or a string is very powerful, but also dangerous.
Another example is pointer arithmetic where we can traverse memory with very little safety mechanisms.
Such arbitrary memory traversal is precisely what good type system should prevent us from doing.
Weak typing has very, uhmmm, weak definition.
Typically languages like C, C++, JavaScript and Visual Basic are attributed to this group.

That's it for today, thanks for listening, bye!

# Example of typing system in Python

```
Python 3.8.5 (default, Jul 21 2020, 10:48:26)
[Clang 11.0.3 (clang-1103.0.32.62)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
```

```python
>>> x = "abc"
>>> y = 123
>>> x + y
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: can only concatenate str (not "int") to str
>>> x = 7
>>> x + y
130
```

# More materials

* [Type system](https://en.wikipedia.org/wiki/Type_system)
* [Strong and weak typing](https://en.wikipedia.org/wiki/Strong_and_weak_typing)


