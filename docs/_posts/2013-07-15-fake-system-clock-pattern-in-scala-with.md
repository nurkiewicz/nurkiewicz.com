---
layout: post
title: Fake system clock pattern in Scala with implicit parameters
date: '2013-07-15T18:42:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- testing
- scala
modified_time: '2013-07-15T18:45:53.660+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8053424634693693595
blogger_orig_url: https://www.nurkiewicz.com/2013/07/fake-system-clock-pattern-in-scala-with.html
image:
  path: /assets/img/fake-system-clock-pattern-in-scala-with/hero.jpg
  alt: "Sjømannsskolen"
---

[Fake system clock](http://www.javapractices.com/topic/TopicAction.do?Id=234) is a design pattern addressing testability issues of programs heavily relying on system time.
If business logic flow depends on current system time, testing various flows becomes cumbersome or even impossible.
Examples of such problematic scenarios include:

1.  certain business flow runs only (or is ignored) during weekends
2.  some logic is triggered only after an hour since some other event
3.  when two events occur at the exact same time (typically 1 ms precision), something should happen
4.  …

Each scenario above poses unique set of challenges.
Taken literally our unit tests would have to run only on specific day (1) or sleep for an hour to observe some behaviour.
Scenario (3) might even be impossible to test under some circumstances since system clock can tick 1 millisecond at any time, thus making test unreliable.

Fake system clock addresses these issues by abstracting system time over simple interface.
Essentially you never call `new Date()`, `new GregorianCalendar()` or [`System.currentTimeMillis()`](http://docs.oracle.com/javase/7/docs/api/java/lang/System.html#currentTimeMillis()) but always rely on this:

```scala
import org.joda.time.{DateTime, Instant}

trait Clock {

    def now(): Instant

    def dateNow(): DateTime

}
```

As you can see I am depending on [Joda Time](http://joda-time.sourceforge.net/) library.
Since we are already in the Scala land, one might consider [scala-time](https://github.com/jorgeortiz85/scala-time) or [nscala-time](https://github.com/nscala-time/nscala-time) wrappers.
Moreover the abstract name `Clock` is not a coincidence.
It’s short and descriptive, but more importantly it mimics [`java.time.Clock`](http://download.java.net/jdk8/docs/api/java/time/Clock.html) class from Java 8 - that happens to address the same problem discussed here at the JDK level!
But since Java 8 is still not here, let’s stay with our sweet and small abstraction.

The standard implementation that you would normally use simply delegates to system time:

```scala
import org.joda.time.{Instant, DateTime}

object SystemClock extends Clock {

    def now() = Instant.now()

    def dateNow() = DateTime.now()

}
```

For the purposes of unit testing we will develop other implementations, but first let’s focus on usage scenarios.
In a typical Spring/JavaEE applications fake system clock can be turned into a dependency that the container can easily inject.
This makes dependence on system time explicit and manageable, especially in tests:

```scala
@Controller
class FooController @Autowired() (fooService: FooService, clock: Clock) {

    def postFoo(name: String) =
        fooService store new Foo(name, clock)

}
```

Here I am using [Spring constructor injection](http://nurkiewicz.blogspot.no/2011/09/evolution-of-spring-dependency.html) asking the container to provide some `Clock` implementation.
Of course in this case `SystemClock` is marked as `@Service`.
In unit tests I can pass fake implementation and in integration tests I can place another, [`@Primary`](http://static.springsource.org/spring/docs/3.1.x/javadoc-api/org/springframework/context/annotation/Primary.html) bean in the context, shadowing the `SystemClock`.

This works great, but becomes painful for certain types of objects, namely entity/DTO beans and utility (`static`) classes.
These are typically not managed by Spring so it can’t inject `Clock` bean to them.
This forces us to pass `Clock` manually from the last “managed” layer:

```scala
class Foo(fooName: String, clock: Clock) {

    val name = fooName
    val time = clock.dateNow()

}
```

similarly:

```scala
object TimeUtil {

    def firstFridayOfNextMonth(clock: Clock) = //...

}
```

It’s not bad from design perspective.
Both `Foo` constructor and `firstFridayOfNextMonth()` method do rely on system time so let’s make it explicit.
On the other hand `Clock` dependency must be dragged, sometimes through many layers, just so that it can be used in one single method somewhere.
Again, this is not bad *per se*.
If your high level method has `Clock` parameter you know from the beginning that it relies on current time.
But still is seems like a lot of boilerplate and overhead for little gain.
Luckily Scala can help us here with:

## `implicit` parameters

Let us refactor our solution a little bit so that `Clock` is an implicit parameter:

```scala
@Controller
class FooController(fooService: FooService) {

    def postFoo(name: String)(implicit clock: Clock) =
        fooService store new Foo(name)

}

@Service
class FooService(fooRepository: FooRepository) {

    def store(foo: Foo)(implicit clock: Clock) =
        fooRepository storeInFuture foo

}

@Repository
class FooRepository {

    def storeInFuture(foo: Foo)(implicit clock: Clock) = {
        val friday = TimeUtil.firstFridayOfNextMonth()
        //...
    }

}

object TimeUtil {

    def firstFridayOfNextMonth()(implicit clock: Clock) = //...

}
```

Notice how we call `fooRepository storeInFuture foo` ignoring second `clock` parameter.
However this alone is not enough.
We still have to provide some `Clock` instance as second parameter, otherwise compilation error strikes:

```scala
could not find implicit value for parameter clock: com.blogspot.nurkiewicz.foo.Clock
    controller.postFoo("Abc")
                      ^

not enough arguments for method postFoo: (implicit clock: com.blogspot.nurkiewicz.foo.Clock)Unit.
Unspecified value parameter clock.
    controller.postFoo("Abc")
                      ^
```

The compiler tried to find implicit value for `Clock` parameter but failed.
However we are really close, the simplest solution is to use [package object](http://www.scala-lang.org/docu/files/packageobjects/packageobjects.html):

```scala
package com.blogspot.nurkiewicz.foo

package object foo {

    implicit val clock = SystemClock

}
```

Where `SystemClock` was defined earlier.
Here is what happens: every time I call a function with `implicit clock: Clock` parameter inside `com.blogspot.nurkiewicz.foo` package, the compiler will discover `foo.clock` implicit variable and pass it transparently.
In other words the following code snippets are equivalent but the second one provides explicit `Clock`, thus ignoring implicits:

```scala
TimeUtil.firstFridayOfNextMonth()
TimeUtil.firstFridayOfNextMonth()(SystemClock)
```

also equivalent (first form is turned into the second by the compiler):

```scala
fooService.store(foo)
fooService.store(foo)(SystemClock)
```

Interestingly in the bytecode level, implicit parameters aren’t any different from normal parameters so if you want to call such method from Java, passing `Clock` instance is mandatory and explicit.

`implicit clock` parameter seems to work quite well.
It hides ubiquitous dependency while still giving possibility to override it.
For example in:

## Tests

The whole point of abstracting system time was to enable unit testing by gaining full control over time flow.
Let us begin with a simple fake system clock implementation that always returns the same, specified time:

```scala
class FakeClock(fixed: DateTime) extends Clock {
    def now() = fixed.toInstant

    def dateNow() = fixed
}
```

Of course you are free to put any logic here: advancing time by arbitrary value, speeding it up, etc. You get the idea.
Now remember, the reason for `implicit` parameter was to hide `Clock` from normal production code while still being able to supply alternative implementation.
There are two approaches: either pass `FakeClock` explicitly in tests:

```scala
val fakeClock = new FakeClock(
   new DateTime(2013, 7, 15, 0, 0, DateTimeZone.UTC))

controller.postFoo("Abc")(fakeClock)
```

or make it implicit but more specific to the compiler resolution mechanism:

```scala
implicit val fakeClock = new FakeClock(
   new DateTime(2013, 7, 15, 0, 0, DateTimeZone.UTC))

controller.postFoo("Abc")
```

The latter approach is easier to maintain as you don’t have to remember about passing `fakeClock` to method under test all the time.
Of course `fakeClock` can be defined more globally as a field or even inside test package object.
No matter which technique of providing `fakeClock` we choose, it will be used throughout all calls to service, repository and utilities.
The moment we given explicit value to this parameter, implicit parameter resolution is ignored.

## Problems and summary

Solution above to testing systems heavily dependant on time is not free from issues on its own.
First of all the implicit `Clock` parameter must be propagated throughout all the layers up to the client code.
Notice that `Clock` is only needed in repository/utility layer while we had to drag it up to the controller layer.
It’s not a big deal since the compiler will fill it in for us, but sooner or later most of our methods will include this extra parameter.

Also Java and frameworks working on top of our code are not aware of Scala implicit resolution happening at compile time.
Therefore e.g. our Spring MVC controller will not work as Spring is not aware of `SystemClock` implicit variable.
It can be worked around though with [`WebArgumentResolver`](http://static.springsource.org/spring/docs/current/javadoc-api/org/springframework/web/bind/support/WebArgumentResolver.html).

Fake system clock pattern in general works only when used consistently.
If you have even one place when real time is used directly as opposed to `Clock` abstraction, good luck in finding test failure reason.
This applies equally to libraries and SQL queries.
Thus if you are designing a library relying on current time, consider providing pluggable `Clock` abstraction so that client code can supply custom implementation like `FakeClock`.
In SQL, on the other hand, do not rely on functions like [`NOW()`](http://dev.mysql.com/doc/refman/5.5/en/date-and-time-functions.html#function_now) but always explicitly provide dates from your code (and thus from custom `Clock`).
