---
layout: post
title: FitNesse your ScalaTest with custom Scala DSL
date: '2013-03-28T17:36:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- dsl
- testing
- scala
- scalatest
modified_time: '2015-11-12T13:24:43.623+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1022741925102059873
blogger_orig_url: https://www.nurkiewicz.com/2013/03/fitnesse-your-scalatest-with-custom.html
---

This article won't be about [FitNesse](http://fitnesse.org/).
As matter of fact I don't like this tool very much and it seems to be loosing momentum, judging by the traffic on an [official mailing list](http://tech.groups.yahoo.com/group/fitnesse/).
Instead we will implement trivial [internal DSL](http://martinfowler.com/bliki/InternalDslStyle.html) on top of Scala to simplify testing code, inspired by [`DoFixture`](http://fitnesse.org/FitNesse.UserGuide.FixtureGallery.FitLibraryFixtures.DoFixture).
`DoFixture` in FitNesse allows one to write very readable acceptance tests almost in plain English using Wiki pages:

```text
!|CarRegistrationFixtureTest|

!1 Registering car
!2 Registering brand new car for the first time

| register | brand new car | by | any owner | in | any country |
```

What might not be obvious is that the last line is actually executable and calls good old Java (or Scala for that matter) method:

```scala
class CarRegistrationFixtureTest extends DoFixture {

    val carService = new CarService

    def registerByIn(car: Car, owner: Owner, where: Country) = {
        //...
    }

}
```

Notice how oddly named `registerByIn` method maps to " ***register** brand new car **by** any owner **in** any country*" wiki syntax.
What we will learn today is writing very simple, custom Scala DSL that is even more readable and does not require new tool and testing framework.

The same test written in [ScalaTest](http://www.scalatest.org/) would look something like this:

```scala
class CarRegistrationSpec extends FeatureSpec with GivenWhenThen {

    val carService = new CarService()

    feature("Registering car") {

        scenario("Registering brand new car for the first time") {
            Given("Owner and brand new car")
            //...

            When("Car registered")
            carService.registerCar(brandNewCar, anyOwner, anyCountry)

            //...
        }
    }
}
```

Nothing fancy, ordinary `registerCar()` method call.
The rest of the test (as well as the declaration of `brandNewCar`, `anyOwner` and `anyCountry`) is not relevant to our discussion.
We can make it a little bit more readable by explicitly naming parameters:

```scala
carService.registerCar(car = brandNewCar, owner = anyOwner, where = anyCountry)
```

However it's not clear whether this is actually more readable for e.g. non-programmers.
But since we already use descriptive [`FeatureSpec`](http://www.scalatest.org/getting_started_with_feature_spec), can we make Scala code a little bit more human eye-friendly?
Of course!
Our biggest friends are [infix notation](http://docs.scala-lang.org/style/method-invocation.html) and [fluent API](http://en.wikipedia.org/wiki/Fluent_interface) pattern:

```scala
def register(car: Car) = new {
    def by(owner: Owner) = new {
        def in(country: Country) =
            carService.registerCar(car, owner, country)
    }
}
```

Looks weird, but put this code in your test and enjoy much more fluent call:

```scala
register(brandNewCar).by(anyOwner).in(anyCountry)
```

This is as far as Java can go, but Scala has infix method call syntax, which is equivalent and looks beautiful:

```scala
register(brandNewCar) by anyOwner in anyCountry
```

Why couldn't we skip first parentheses?
It is a limitation on where infix notation can be used (only one-argument method calls on an object).
Fortunately we can easily refactor our internal testing DSL by pushing noun (*owner*) onto first place and using implicit conversion:

```scala
implicit def fluentCarRegister(owner: Owner) = new {
    def registers(car: Car) = new {
        def in(country: Country) =
            carService.registerCar(car, owner, country)
    }
}
```

...which can be used as follows:

```scala
anyOwner registers brandNewCar in anyCountry
```

If you got lost, the line of code above is still Scala and is still executable.
If you don't quite get what's happening, here is a *desugared* syntax:

```scala
fluentCarRegister(anyOwner).registers(brandNewCar).in(anyCountry)
```

Tests are all about readability and maintainability.
Many people are scared of DSLs because often they are hard to implement and debug.
As I showed in this short article, writing really simple yet impressive test DSL in Scala is both simple and rewarding.
Moreover there is no reflection or magic meta-programming.
