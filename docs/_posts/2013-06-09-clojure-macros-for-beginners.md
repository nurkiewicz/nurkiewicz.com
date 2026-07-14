---
layout: post
title: Clojure macros for beginners
date: '2013-06-09T23:27:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- clojure
- functional programming
modified_time: '2015-08-05T08:47:20.090+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4187944289979788653
blogger_orig_url: https://www.nurkiewicz.com/2013/06/clojure-macros-for-beginners.html
image:
  path: /assets/img/clojure-macros-for-beginners/hero.jpg
  alt: "Bjørvika"
---

This article will guide you step-by-step (or even *character-by-character*) through the process of writing macros in Clojure.
I will focus on fundamental macro characteristics while explaining what happens behind the scenes.

Imagine you are about to write an assertions library for Clojure, similar to [FEST Assertions](https://github.com/alexruiz/fest-assert-2.x/wiki), [ScalaTest assertions](http://www.scalatest.org/user_guide/using_assertions) or [Hamcrest](http://hamcrest.org/).
Of course there are [such existing](http://clojure.github.io/clojure/clojure.test-api.html) but this is just for educational purposes.
What we essentially need first is a `assert-equals` function used like this:

```clojure
(assert-equals 
    (count (filter even? primes)) 1)
```

Of course this is more than trivial:

```clojure
(defn assert-equals [actual expected] 
    (when-not (= actual expected) 
        (throw 
            (AssertionError. 
                (str "Expected " expected " but was " actual)))))
```

Quick test with incorrectly defined `primes` vector:

```clojure
user=> (def primes [0 2 3 5 7 11])
#'user/primes
user=> (assert-equals (count (filter even? primes)) 1)

AssertionError Expected 1 but was 2
```

Cool, but imagine this test failing on CI server or seeing this in your terminal.
There is no context, maybe you’ll get test name if you’re lucky.
“`Expected 1 but was 2`” tells us nothing about the nature or root cause of the problem.
Wouldn’t it be great to see:

```clojure
AssertionError Expected '(count (filter even? primes))' to be 1 but was 2
```

You see this?
Assertion error now gives us full expression that yielded incorrect result.
We can see from the very first second what the issue can be.
However, there is a problem.
Big one.
By the time we are throwing `AssertionError`, original expression is lost.
We got `actual` *value* as an argument and we have no idea where did that value came from.
It could have been a constant, result of expression like `(count (filter even? primes))` or even a random value.
Function arguments are computed eagerly and there is no way to access *code* that produced these arguments.

## Entering macros

Macros and functions in Clojure are not independent or orthogonal.
In fact, they are almost the same:

- **Functions** execute at **run time**, they take and produce **data** (values).
  Conceptually one can replace every (pure) function invocation with its value.
- **Macros** execute at **compile time**, they take and produce **code**.
  Conceptually one can replace (*expand*) every occurrence of macro with its value.

Not that much different?
Moreover since Clojure is [*homoiconic*](http://en.wikipedia.org/wiki/Homoiconicity), Clojure code can be represented as Clojure data structures.
In other words both functions and macros accept data, but in case of macros it’s more often to see Clojure source represented using data structures like lists.

What does it all mean and how can it help us?
Let’s jump straight into writing our first (incorrect) macro and improve it step-by-step to finally achieve desired result.
To keep samples focused I skip throwing an `AssertionError` and leave only equality condition:

```clojure
user=> (defmacro assert-equals [actual expected] 
            (= expected actual))
#'user/assert-equals
user=> (assert-equals 2 2)
true

user=> (assert-equals 2 3)
false
```

Works?
In fact we are very far from having a correct version:

```clojure
user=> (assert-equals (inc 5) 6)
false

user=> (def x 1)
#'user/x
user=> (assert-equals (+ x 2) 3)
false
```

`1 + 2` is definitely equal to `3`, yet it returns false.
In order to appreciate this behaviour and call it “*feature*” rather than “*bug*” we must deeply understand what just happened.
Remember, macros are executed at compile time, right?
And they are almost ordinary functions.
So, the compiler executes `assert-equals`.
However during compilation it can’t possibly know the values of variables like `x`, therefore it can’t eagerly evaluate macro arguments.
We don’t even want that, as you see later.

Instead the compiler passes **Clojure code, literally**.
The `actual` parameter is `(inc 5)` - literally, Clojure list holding two elements: `inc` symbol and `5` number.
That’s all there is to it.
`expected` is just a number.
This means that inside macro we have full access to Clojure source code enclosed by that macro.

So maybe you can now guess what happens.
Clojure compiler executes macro definition, that is `(= expected actual)`.
As far as the compiler is concerned, `actual` is a list `(inc 5)` while `expected` is a number `6`.
List can never possibly be equal to a number.
Thus macro returns `false`, just like any other function can return it.
Later on Clojure compiler replaces `(assert-equals (inc 5) 6)` expression with the outcome of macro, which happens to be… `false`.
We said before that macro should return valid Clojure code (represented using Clojure data structures).
`false` *is* valid Clojure code!

Now we know that instead of evaluating `(= expected actual)` by the compiler (after all, we don’t want the compiler to run our assertions, we only want to compile them!)
we simply want to return *code* that represents this assertion.
It’s not that hard!

```clojure
(defmacro assert-equals [actual expected] (list '= expected actual))
```

Now our macro returns result of evaluating `(list '= expected actual)` expression.
The result happens to be… `(= expected actual)`.
That’s right, it looks like valid Clojure code, again.
Extra quote (`'=`) was added so that `=` is interpreted as raw symbol rather than a function reference.
Let’s take it for a test drive:

```clojure
user=> (assert-equals (inc 5) 6)
true
user=> (macroexpand '(assert-equals (inc 5) 6))
(= 6 (inc 5))
```

`macroexpand` and `macroexpand-1` are your weapons of choice when debugging macros.
Here you see that `(assert-equals (inc 5) 6)` is actually being replaced by `(= 6 (inc 5))`.
This process happens at compile time, **macros don’t exist at runtime**.
In your compiled code you are left with `(= 6 (inc 5))`.
OK, so let’s restore the full functionality of throwing `AssertionError`.
As you know by now, our macro should return Clojure code that includes equality check and throwing an exception.
This becomes a bit unwieldy:

```clojure
(defmacro assert-equals [actual expected] 
    (list 'when-not (list '= actual expected) 
        (list 'throw 
            (list 'AssertionError.
                (list 'str "Expected " expected " but was " actual)))))
```

Notice how every single symbol has to be escaped (`'when-not`, `'throw`, `'AssertionError.`, …), otherwise compiler will try to evaluate it at compile time.
Moreover list in Clojure denotes function call so we must proceed every list literal with `(list ...)`
function call.
If you are not that familiar with Clojure: `(list 1 2)` returns list of `(1 2)` while `(1 2)` will throw an exception since `1` number is not a function.

Ugly or not, it works:

```clojure
user=> (assert-equals (inc 5) 6)
nil
user=> (assert-equals 5 6)
AssertionError Expected 6 but was 5
```

We barely reproduced what original `assert-equals` function was doing and the first commandment of writing macros is: don’t write macros if function is sufficient.
But before we go further, let us clean up what we have so far.
Typical macro definition consists of lots of Clojure code that has to be escaped and not that much *live* values like `actual` and `expected` in our case.
So there is a smart default - instead of quoting everything except few items, quote everything upfront and selectively *unquote* things.
This is called **syntax-quoting** (using \` character) and unquoting is done via `~` operator.
Look carefully: we syntax quote whole result and selectively unquote what was previously not quoted:

```clojure
(defmacro assert-equals [actual expected] 
    `(when-not (= ~actual ~expected) 
        (throw 
            (AssertionError.
                (str "Expected " ~expected " but was " ~actual)))))
```

This is equivalent to previous definition but looks much better, almost entirely like valid Clojure code.
Let’s employ `macroexpand-1` to see how our macro is expanded during compilation.
`macroexpand` would work as well, but since `when-not` is also a macro (!)
it would be recursively expanded, cluttering output:

```clojure
user=> (macroexpand-1 '(assert-equals (inc 5) 6))
(when-not 
    (= (inc 5) 6) 
        (throw 
            (java.lang.AssertionError.
                (str "Expected " 6 " but was " (inc 5)))))
```

It’s like templating language embedded within that language!
Notice how `(inc 5)` piece of code was inserted instead of `~actual` twice.
Keep that in mind.
Also experiment by removing unquote (`~`) symbol here or there.
Use `macroexpand-1` to figure out what is going on.

Remember, our ultimate goal was to show `actual` expression in its full glory, not only its value.

```clojure
(AssertionError.
   (str "Expected '???' to be " ~expected " but was " actual-value#))))))
```

What should we put in place of `???`
to print “`(inc 5)`” *string*.
We know that value of `actual` is *not* `6` but a list with two items: `(inc 5)`.
Can we somehow quote that list again so that it no longer evaluates at run-time but instead is treated as a data structure?
Of course, we know how to quote things!

```clojure
(defmacro assert-equals [actual expected] 
    `(let [~'actual-value ~actual] 
        (when-not (= ~'actual-value ~expected) 
            (throw 
                (AssertionError.
                   (str "Expected '" '~actual "' to be " ~expected " but was " ~'actual-value))))))
```

`'~actual`, oh dear!
*quote unquote actual*.
This translates to `'(inc 5)`.
And that’s it!
Look how descriptive assertion error messages are:

```clojure
user=> (assert-equals (inc 5) 5)
AssertionError Expected '(inc 5)' to be 5 but was 6

user=> (assert-equals (count (filter even? primes)) 1)
AssertionError Expected '(count (filter even? primes))' to be 1 but was 2
```

Expanding this macro manually reveals how it is translated by the compiler (edited to improve readability):

```clojure
user=> (macroexpand-1 '(assert-equals (inc 5) 5))
(when-not 
    (= (inc 5) 5) 
        (throw 
            (java.lang.AssertionError. 
                (str "Expected '" (quote (inc 5)) "' to be " 5 " but was " (inc 5)))))
```

There is really no magic here, we could have written that ourselves.
But macros avoid lots of repetitive work.

## Bindings in macros

Our solution so far has one major issue.
Imagine we are testing impure or slow function like this:

```clojure
(def question "Answer to the Ultimate Question of Life, The Universe, and Everything")
(defn answer [q] 
    (do 
        (println "Computing for 7½ million years...")
        41))
```

As you can see it returns [wrong result](http://en.wikipedia.org/wiki/Phrases_from_The_Hitchhiker%27s_Guide_to_the_Galaxy#Answer_to_the_Ultimate_Question_of_Life.2C_the_Universe.2C_and_Everything_.2842.29), which can be easily proved in a unit test:

```clojure
user=> (assert-equals (answer question) 42)
Computing for 7½ million years...
Computing for 7½ million years...

AssertionError Expected '(answer question)' to be 42 but was 41
```

The error message is fine, but notice that “`Computing...`” statement was printed twice.
Clearly because impure `answer` function was called twice as well.
Macro expansion reveals why:

```clojure
user=> (macroexpand-1 '(assert-equals (answer question) 42))
(when-not 
    (= (answer question) 42) 
        (throw (java.lang.AssertionError. 
            (str "Expected '" (quote (answer question)) "' to be " 42 " but was " 
                (answer question)))))
```

`(answer question)` appears twice (not counting `quote`d one), once during comparison and second time when we generate assertion message.
This is rarely desired, especially when *function under test* has side effects.
The solution is simple: precompute `(answer question)` once, store it somewhere and reference when needed.
But there is a twist: declaring `let` bindings inside macros is tricky.
Sometimes you might hit unexpected name shadowing and overriding when names of variables inside macro collide with the ones used in user code.
Not going into much detail, using `(gensym)` or convenient `#` suffix is enough to keep our macros safe.
In both cases Clojure compiler will produce unique names making sure they don’t collide.
Our final solution looks like this:

```clojure
(defmacro assert-equals [actual expected] 
    `(let [actual-value# ~actual] 
        (when-not (= actual-value# ~expected) 
            (throw 
                (AssertionError. 
                   (str "Expected '" '~actual "' to be " ~expected
                       " but was " actual-value#))))))
```

This time `actual-value#` binding is used to compute `actual` only once:

```clojure
user=> (macroexpand-1 '(assert-equals (answer question) 42))
(let [actual-value__264__auto__ (answer question)] 
    (when-not (= actual-value__264__auto__ 42) 
        (throw 
            (java.lang.AssertionError. 
                (str "Expected '" (quote (answer question)) "' to be " 42 "
                   but was " actual-value__264__auto__)))))
```

Extra suffix replacing `#` symbol makes sure `actual-value` is not colliding with any other symbol.

## Summary

Our `assert-equals` macro is not the most comprehensive one, just like this tutorial.
But it gives you some impression of what macros can do and how they work.
If you need further resources, check out this [great macro tutorial](http://www.learningclojure.com/2010/09/clojure-macro-tutorial-part-i-getting.html) (part [2](http://www.learningclojure.com/2010/09/clojure-macro-tutorial-part-ii-compiler.html) and [3](http://www.learningclojure.com/2010/09/clojure-macro-tutorial-part-ii-syntax.html)).
If you like the idea of enhanced assertions, [Power Assertions in Groovy](http://hamletdarcy.blogspot.no/2009/05/new-power-assertions-in-groovy.html) are even more comprehensive.
But I bet this behaviour can be reproduced in Clojure macros!
