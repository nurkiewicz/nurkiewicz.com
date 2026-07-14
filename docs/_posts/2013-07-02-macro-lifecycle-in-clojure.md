---
layout: post
title: Macro lifecycle in Clojure
date: '2013-07-02T18:37:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- clojure
modified_time: '2013-07-02T18:37:25.829+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4472167425757743542
blogger_orig_url: https://www.nurkiewicz.com/2013/07/macro-lifecycle-in-clojure.html
image:
  path: /assets/img/macro-lifecycle-in-clojure/hero.jpg
  alt: "Oslofjord from Snarøya"
---

If you still struggle to understand what are macros in Clojure and why are they so useful, I will guide you through another example today.
We will learn when macros are recognized, evaluated, expanded and executed.
I believe the most important concept is their similarity to normal functions.
As I described [last time](http://nurkiewicz.blogspot.no/2013/06/clojure-macros-for-beginners.html), macros are ordinary functions but executed at compile time and taking code rather than values as arguments.
The second difference is slightly artificial since Clojure code *is* a value in sense that it can be passed around.
So let us focus on when macros are actually expanded and executed.

We will start from trivial [GCD implementation in Clojure](http://rosettacode.org/wiki/Greatest_common_divisor#Clojure) as a normal function:

```clojure
(defn gcd [a b]
    (if (zero? b)
        a
        (recur b (mod a b))))
```

Calling this function will result in a tail-recursive loop executed **at runtime** every time it is encountered:

```clojure
user=> (gcd 18 12)
6
user=> (gcd 9 2)
1
user=> (gcd 9 (inc 2))
3
```

Not very exciting.
But what if we wrap reference to `gcd` inside a macro?

```clojure
(defmacro runtime-gcd [a b] (list 'gcd a b))
```

Or more concise syntax:

```clojure
(defmacro runtime-gcd-quote [a b] `(gcd ~a ~b))
```

Now look at the declaration of `runtime-gcd` but replace `defmacro` with `defn`, just as if it was a normal function:

```clojure
(defn runtime-gcd-fun [a b] (list 'gcd a b))
```

Every time you call `runtime-gcd-fun` in your Clojure code, it gets replaced with the following list: `(gcd 12 8)`.
As you can see it is basically a `gcd` function call.
It is quoted, thus remains a list rather than invoking the actual function.
You can evaluate this data structure by running `(eval)`:

```clojure
user=> (eval '(gcd 12 8))
4
user=> (eval (list 'gcd 12 8))
4
user=> (eval (runtime-gcd-fun 12 8))
4
```

As you can see `runtime-gcd-fun` is a function that produces data structure (`list`) that happens to be valid Clojure *code*!
`runtime-gcd-fun` does not call `(gcd a b)`, it returns code (expression) that invokes `gcd`.
OK, but what does it have to do with macros?
Let’s go back to our original `runtime-gcd` macro:

```clojure
user=>     (defmacro runtime-gcd [a b] (list 'gcd a b))
#'user/runtime-gcd
user=> (runtime-gcd 12 8)
4
user=> (runtime-gcd 12 (inc 7))
4
```

Sooo… where is the difference?
Nowhere, yet.
`(defmacro)` is executed (*expanded*) at compile time.
It is basically a function invoked during compilation.
Just like an invocation of normal function is replaced with its value at runtime, value returned from a macro replaces every occurrence of that macro in code.
Before it even gets compiled down to bytecode.
So if `runtime-gcd` is encountered, compiler calls it and replaces it with its result, that is: `(gcd a b)`.
This means we can simply replace e.g. `(runtime-gcd 12 8)` with `(gcd 12 8)` - this is what the compiler is doing for us anyway.

What’s the big deal, then?
So far macros are just fancy functions executed during compilation.
But what if we skip quoting and define `compile-time-gcd` as follows?

```clojure
user=> (defmacro compile-time-gcd [a b] (gcd a b))
#'user/compile-time-gcd
user=> (compile-time-gcd 12 8)
4
```

Stay we me, you are *this* close to enlightenment.
Notice that we no longer quote `gcd` invocation.
This has tremendous consequences.
This time when compiler encounters `compile-time-gcd` macro it executes its body (*expands it*).
While body of `runtime-gcd` was calling `list` function (thus returning a list), body of `compile-time-gcd` calls `gcd` immediately - and remember this happens at compile time!
`(gcd 12 8)` is executed by the compiler and its value (`4`) is returned as macro expansion result.
This means that the whole `(compile-time-gcd 12 8)` is replaced **at compile time** with number `4`.
In other words the computation was done during compilation and `gcd` overhead is non-existent at runtime.
Check out the output of `macroexpand` that shows what macro returns without evaluating it:

```clojure
user=> (macroexpand '(runtime-gcd 12 8))
(gcd 12 8)

user=> (macroexpand '(compile-time-gcd 12 8))
4
```

This is something you should really think about.
Macros are not just advanced search-and-replace facilities built into the compiler.
They are “real” Clojure functions that can have logic and conditions.
The only difference is that they work at compile time and operate on code rather than on values.
So why not use macros all the time if they can run the program at compile time and avoid runtime computations?
Remember that macros live in the compiler only, they don’t know anything about your runtime environment:

```clojure
user=> (compile-time-gcd 12 (inc 7))
ClassCastException clojure.lang.PersistentList cannot be cast to java.lang.Number  
    clojure.lang.Numbers.isZero (Numbers.java:90)
```

This error will actually pop-up during compilation, not at runtime!
The compiler tries to run `(gcd 12 '(inc 7))`.
Quoted `'(inc 7)` list is not equal to number 8.
It’s a `list`!
And when the compiler executes the condition `(zero? '(inc 7))` familiar `ClassCastException` is thrown.
Don’t confuse it with seemingly similar `(zero? (inc 7))` - incrementing `7` is not quoted and thus evaluates to `8`.

Are you still confused?
Let’s make it even more explicit:

```clojure
(defmacro printer [s]
    (println "Compile time:" s)
    (list 'println "Runtime:" s))
```

This macro is a function with two expressions.
Now compile the following Clojure file:

```clojure
(printer "buzz")
(printer (str "foo" "bar"))
```

Look carefully at the **compiler** output, you will see the following two lines:

```clojure
Compile time: buzz
Compile time: (str foo bar)
```

This proves that macros are expanded and executed at compile time.
But what happened with the second line?
Well, value of last expression of any function (macros are not exception here) becomes value of that function.
Thus every occurrence of `(printer s)` macro is replaced with `(println "Runtime:" s)` *list* - and this piece of code will be compiled just as if was `println` from the very beginning.

In order to make sure you understand macros really well, switch statements in `printer` macro and try to figure out what will this macro do, both at compile- and run-time (hint: value of `println` is `nil`):

```clojure
(defmacro broken-printer [s]
    (list 'println "Runtime:" s)
    (println "Compile time:" s))
```

We are not even close to explaining all aspects of macros in Clojure.
We have not covered various quoting quirks, `gensym`, splicing, etc. But I hope this article (together with [Clojure macros for beginners](http://nurkiewicz.blogspot.no/2013/06/clojure-macros-for-beginners.html)) will give you some basic idea why macros are so essential in Lisp family of languages.
