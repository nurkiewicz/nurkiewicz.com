---
layout: post
title: 'Scala traits implementation and interoperability. Part II: Traits linearization'
date: '2013-04-03T22:32:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- scala
- traits
modified_time: '2013-04-07T13:14:40.532+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2680263771961678108
blogger_orig_url: https://www.nurkiewicz.com/2013/04/scala-traits-implementation-and_3.html
---

This is a continuation of [Scala traits implementation and interoperability. Part I: Basics](http://nurkiewicz.blogspot.no/2013/04/scala-traits-implementation-and.html).
Dreadful [diamond problem](http://en.wikipedia.org/wiki/Multiple_inheritance#The_diamond_problem) can be mitigated using Scala traits and a process called *linearization*.
Take the following example:

```scala
trait Base {
    def msg = "Base"
}

trait Foo extends Base {
    abstract override def msg = "Foo -> " + super.msg
}

trait Bar extends Base {
    abstract override def msg = "Bar -> " + super.msg
}

trait Buzz extends Base {
    abstract override def msg = "Buzz -> " + super.msg
}

class Riddle extends Base with Foo with Bar with Buzz {
    override def msg = "Riddle -> " + super.msg
}
```

Now let me ask you a little question: what is the output of `(new Riddle).msg`?

1.  `Riddle -> Base`
2.  `Riddle -> Buzz -> Base`
3.  `Riddle -> Foo -> Base`
4.  `Riddle -> Buzz -> Bar -> Foo -> Base`

It's not (1) because `Base.msg` is overriden by all traits we extend, so that shouldn't be a surprise.
But it's also not (2) and (3).
One might expect that either `Buzz` or `Foo` is printed, remembering that you can stack traits and either first or last (actually: last) wins.
So why `Riddle -> Buzz -> Base` is incorrect?
Isn't `Buzz.msg` calling `super.msg` and `Buzz` explicitly states `Base` being it's parent?
There is a bit of magic here.

When you stack multiple traits as we did (`extends Base with Foo with Bar with Buzz`) Scala compiler orders them (*linearizes*) so that there is always one path from every class to the parent (`Base`).
The order is determined by the reversed order of traits mixed in (last one *wins* and becomes first).
Why would you ever...?
Turns out stackable traits are great for implementing several layers of decoration around real object.
You can easily add decorators and move them around.

We have a simple calculator abstraction and one implementation:

```scala
trait Calculator {
    def increment(x: Int): Int
}

class RealCalculator extends Calculator {
    override def increment(x: Int) = {
        println(s"increment($x)")
        x + 1
    }
}
```

We came up with three aspect we would like to selectively apply depending on some circumstances: logging all `increment()` invocations, caching and validation.
First let's define all of them:

```scala
trait Logging extends Calculator {
    abstract override def increment(x: Int) = {
        println(s"Logging: $x")
        super.increment(x)
    }
}

trait Caching extends Calculator {
    abstract override def increment(x: Int) = 
        if(x < 10) {    //silly caching...
            println(s"Cache hit: $x")
            x + 1
        } else {
            println(s"Cache miss: $x")
            super.increment(x)
        }
}

trait Validating extends Calculator {
    abstract override def increment(x: Int) = 
        if(x >= 0) {
            println(s"Validation OK: $x")
            super.increment(x)
        } else
            throw new IllegalArgumentException(x.toString)
}
```

Creating "raw" calculator is of course possible:

```scala
val calc = new RealCalculator
calc: RealCalculator = RealCalculator@bbd9e6

scala> calc increment 17
increment(17)
res: Int = 18
```

But we are free to mix-in as many trait mixins as we want, in any order:

```scala
scala> val calc = new RealCalculator with Logging with Caching with Validating
calc: RealCalculator with Logging with Caching with Validating = $anon$1@1aea543

scala> calc increment 17
Validation OK: 17
Cache miss: 17
Logging: 17
increment(17)
res: Int = 18

scala> calc increment 9
Validation OK: 9
Cache hit: 9
res: Int = 10
```

See how subsequent mixins kick in?
Of course each mixin can skip `super` call, e.g. on cache hit or validation failure.
Just to be clear here - it doesn't matter that each of decorating mixins have `Calculator` defined as a base trait.
`super.increment()` is always routed to next trait in stack (previous one in the class declaration).
That means `super` is more dynamic and dependant on target usage rather than declaration.
We will explain this later but first another example: let's put logging before caching so no matter whether there was cache hit or miss, we always get logging.
Moreover we "disable" validation by simply skipping it:

```scala
scala> class VerboseCalculator extends RealCalculator with Caching with Logging
defined class VerboseCalculator

scala> val calc = new VerboseCalculator
calc: VerboseCalculator = VerboseCalculator@f64dcd

scala> calc increment 42
Logging: 42
Cache miss: 42
increment(42)
res: Int = 43

scala> calc increment 4
Logging: 4
Cache hit: 4
res: Int = 5
```

I promised to explain how stacking works underneath.
You should be really curious how this "funky" `super` is implemented as it cannot simply rely on `invokespecial` bytecode instruction, used with normal `super`.
Unfortunately it's complex, but worth to know and understand, especially when stacking doesn't work as expected.
`Calculator` and `RealCalculator` compile pretty much exactly to what you might have expected:

```java
public interface Calculator {
    int increment(int i);
}

public class RealCalculator implements Calculator {
    public int increment(int x) {
        return x + 1;
    }
}
```

But how would the following class be implemented?

```scala
class FullBlownCalculator 
    extends RealCalculator 
       with Logging 
       with Caching 
       with Validating
```

Let's start from the class itself:

```java
public class FullBlownCalculator extends RealCalculator implements Logging, Caching, Validating {
    public int increment(int x) {
        return Validating$class.increment(this, x);
    }

    public int Validating$$super$increment(int x) {
        return Caching$class.increment(this, x);
    }

    public int Caching$$super$increment(int x) {
        return Logging$class.increment(this, x);
    }

    public int Logging$$super$increment(int x) {
        return super.increment(x);
    }
}
```

Can you see what's going on here?
Before I show the implementations of all these `*$class` classes, spend a little bit of time confronting class declaration (trait order in particular) and these awkward `*$$super$*` methods.
Here is the missing piece that will allow us to connect all the dots:

```java
public abstract class Logging$class {
    public static int increment(Logging that, int x) {
        return that.Logging$$super$increment(x);
    }
}

public abstract class Caching$class {
    public static int increment(Caching that, int x) {
        return that.Caching$$super$increment(x);
    }
}

public abstract class Validating$class {
    public static int increment(Validating that, int x) {
        return that.Validating$$super$increment(x);
    }
}
```

Not helpful?
Let's go slowly through the first step.
When you call `FullBlownCalculator`, according to trait stacking rules, `RealBlownCalculator.increment()` should call `Validating.increment()`.
As you can see, `Validating.increment()` forwards `this` (itself) to static `Validating$class.increment()` hidden class.
This class expects an instance of `Validating`, but since `FullBlownCalculator` also extends that trait, passing `this` is fine.

Now look at the `Validating$class.increment()`.
It barely forwards `FullBlownCalculator.Validating$$super$increment(x)`.
And when we, again, go back to `FullBlownCalculator` we will notice that this method delegates to static `Caching$class.increment()`.
From here the process is similar.
Why the extra delegation through `static` method?
Mixins don't know which class is going to be next in the stack ("next `super`").
Thus they simply delegate to appropriate virtual `$$super$` family of methods.
Each class using these mixins is obligated to implement them, providing correct "super".

To put that into perspective: compiler cannot simply delegate straight from `Validating$class.increment()` to `Caching$class.increment()`, even though that's the `FullBlowCalculator` workflow.
However if we create another class that reverses these mixins (`RealCalculator with Validating with Caching`) hardcoded dependency between mixins is no longer valid.
This it's the responsibility of the class, not mixin, to declare the order.

If you still don't follow, here is the complete call stack for `FullBlownCalculator.increment()`:

```text
val calc = new FullBlownCalculator
calc increment 42

FullBlownCalculator.increment(42)
`- Validating$class.increment(calc, 42)
   `- Validating.Validating$$super$increment(42) (on calc)
      `- Caching$class.increment(calc, 42)
         `- Caching.Caching$$super$increment(42) (on calc)
            `- Logging$class.increment(calc, 42)
               `- Logging.Logging$$super$increment(42) (on calc)
                  `- super.increment(42)
                     `- RealCalculator.increment(42) (on calc)
```

Now you see why it's called "*linearization*"!
