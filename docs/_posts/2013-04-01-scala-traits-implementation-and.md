---
layout: post
title: 'Scala traits implementation and interoperability. Part I: Basics'
date: '2013-04-01T23:16:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- scala
- traits
modified_time: '2013-04-07T13:13:16.341+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8914537097194389121
blogger_orig_url: https://www.nurkiewicz.com/2013/04/scala-traits-implementation-and.html
---

Traits in Scala are similar to interfaces, but much more powerful.
They allow implementations of some of the methods, fields, stacking, etc. But have you ever wondered how are they implemented on top of JVM?
How is it possible to extend multiple traits and where the implementations go to?
In this article, based on [my StackOverflow answer](http://stackoverflow.com/a/7637888), I will give several trait examples and explain how `scalac` implements them, what are the drawbacks and what you get for free.
Often we will look at compiled classes and decompile them to Java.
It's not essential knowledge, but I hope you'll enjoy it.
All examples are compiled against Scala 2.10.1.

## Simple trait with no method implementations

The following trait:

```scala
trait Solver {
    def answer(question: String): Int
}
```

compiles down to the most boring Java interface:

```java
public interface Solver {
    int answer(String);
}
```

There is really nothing special in Scala traits.
That also means that if you ship `Solver.class` as part of your library, users can safely implement such interface from Java code.
As far as `java`/`javac` is concerned, this is an ordinary Java compiled interface.

## Traits having some methods implemented

OK, but what if trait actually has some method bodies?

```scala
trait Solver {

    def answer(s: String): Int

    def ultimateAnswer = answer("Answer to the Ultimate Question of Life, the Universe, and Everything")

}
```

Here, `ultimateAnswer` method actually has some implementation (the fact that it calls abstract `answer()` method is irrelevant) while `answer()` remains unimplemented.
What will `scalac` produce?

```java
public interface Solver {
    int answer(java.lang.String);
    int ultimateAnswer();
}
```

Well, it's still an interface and the implementation is gone.
If the implementation is gone, what happens when we extend such a trait?

```scala
class DummySolver extends Solver {

    override def answer(s: String) = 42

}
```

We need to implement `answer()` but `ultimateAnswer` is already available via `Solver`.
Anxious to see how it looks under the hood?
`DummySolver.class`:

```java
public class DummySolver implements Solver {

    public DummySolver() {
        Solver$class.$init$(this);
    }

    public int ultimateAnswer() {
        return Solver$class.ultimateAnswer(this);
    }

    public int answer(String s) {
        return 42;
    }

}
```

That...
is...
weird...
Apparently we missed one new class file, `Solver$class.class`.
Yes, the class is named `Solver$class`, this is valid even in Java.
This is *not* `Solver.class` expression which returns `Class[Solver]`, it's apparently an ordinary Java class named `Solver$class` with a bunch of static methods.
Here is how it looks like:

```java
public abstract class Solver$class {

    public static int ultimateAnswer(Solver $this) {
        return $this.answer("Answer to the Ultimate Question of Life, the Universe, and Everything");
    }

    public static void $init$(Solver solver) {}
}
```

Do you see the trick?
Scala created a helper `Solver$class` and methods that are implemented inside trait are actually placed in that hidden class.
BTW this is not a companion object, it's just a helper class invisible to you.
But the real trick is `$this` parameter, invoked as `Solver$class.ultimateAnswer(this)`.
Since we are technically in another object, we must somehow get a handle of a *real* `Solver` instance.
It is like OOP but done manually.

So we learned that method implementations from traits are extracted to a special helper class.
This class is referenced every time we call such a method.
This way we don't copy method body over and over into every single class extending given trait.

## Extending multiple traits with implementations

Imagine extending multiple traits, each implementing distinct set of methods:

```scala
trait Foo {
    def foo = "Foo"
}

trait Bar {
    def bar = "Bar"
}

class Buzz extends Foo with Bar
```

By analogy you probably know already how `Foo.class` and `Bar.class` look like:

```java
public interface Foo {
    String foo();
}

public interface Bar {
    String bar();
}
```

Implementations are hidden in mysterious `...$class.class` files just as before:

```java
public abstract class Foo$class {
    public static String foo(Foo) {
        return "Foo";
    }

    public static void $init$(Foo) {}
}

public abstract class Bar$class {
    public static String bar(Bar) {
        return "Bar";
    }

    public static void $init$(Bar) {}
}
```

Notice that static methods in `Foo$class` accept instances of `Foo` while `Bar$class` require reference to `Bar`.
This works because `Buzz` implements both `Foo` and `Bar`:

```java
public class Buzz implements Foo, Bar {

    public Buzz() {
        Foo.class.$init$(this);
        Bar.class.$init$(this);
    }

    public String bar() {
        return Bar$class.bar(this);
    }

    public String foo() {
        return Foo$class.foo(this);
    }

}
```

Both `foo()` and `bar()` pass `this` reference, but this is fine.

## Traits with fields

Fields are another interesting feature of traits.
This time let's use a real-world example from [Spring Data](http://www.springsource.org/spring-data) project.
As you know interfaces can require certain methods to be implemented.
However they can't force you to provide certain fields (or provide fields on their own).
This limitation becomes painful when working with [`Auditable<U, ID>`](http://static.springsource.org/spring-data/data-commons/docs/current/api/org/springframework/data/domain/Auditable.html) interface extending [`Persistable<ID>`](http://static.springsource.org/spring-data/data-commons/docs/current/api/org/springframework/data/domain/Persistable.html).
While these interfaces merely exist to make sure certain fields are present on your `@Entity` class, namely `createdBy`, `createdDate`, `lastModifiedBy`, `lastModifiedDate` and `id`, this cannot be expressed cleanly.
Instead you have to implement the following methods in every single entity extending `Auditable`:

```java

       U getCreatedBy();
    void setCreatedBy(final U createdBy);
DateTime getCreatedDate();
    void setCreatedDate(final DateTime creationDate);
       U getLastModifiedBy();
    void setLastModifiedBy(final U lastModifiedBy);
DateTime getLastModifiedDate();
    void setLastModifiedDate(final DateTime lastModifiedDate);

      ID getId();
 boolean isNew();
```

Moreover, every single class must of course define fields highlighted above.
Doesn't feel [DRY](http://en.wikipedia.org/wiki/Don%27t_repeat_yourself) at all.
Luckily traits can help us *a lot*.
In trait we can define what fields should be created in every class extending this trait:

```scala
trait IAmAuditable[ID <: java.io.Serializable] extends Auditable[User, ID] {

    var createdBy: User = _

    def getCreatedBy = createdBy

    def setCreatedBy(createdBy: User) {
        this.createdBy = createdBy
    }

    var createdDate: DateTime = _

    def getCreatedDate = createdDate

    def setCreatedDate(creationDate: DateTime) {
        this.createdDate = creationDate
    }

    var lastModifiedBy: User = _

    def getLastModifiedBy = lastModifiedBy

    def setLastModifiedBy(lastModifiedBy: User) {
        this.lastModifiedBy = lastModifiedBy
    }

    var lastModifiedDate: DateTime = _

    def getLastModifiedDate = lastModifiedDate

    def setLastModifiedDate(lastModifiedDate: DateTime) {
        this.lastModifiedDate = lastModifiedDate
    }

    var id: ID = _

    def getId = id

    def isNew = id == null
}
```

But wait, Scala has built-in support for POJO-style getters/setters!
So we can shorten this to:

```scala
class IAmAuditable[ID <: java.io.Serializable] extends Auditable[User, ID] {

    @BeanProperty var createdBy: User = _

    @BeanProperty var createdDate: DateTime = _

    @BeanProperty var lastModifiedBy: User = _

    @BeanProperty var lastModifiedDate: DateTime = _

    @BeanProperty var id: ID = _

    def isNew = id == null
}
```

Compiler-generated getters and setters implement interface automatically.
From now on, every class willing to provide auditing capabilities can extend this trait:

```scala
@Entity
class Person extends IAmAuditable[String] {

    //...

}
```

All the fields, getters and setters are there.
But how is it implemented?
Let's look at the generated `Person.class`:

```java
public class Person implements IAmAuditable<java.lang.String> {
    private User createdBy;
    private DateTime createdDate;
    private User lastModifiedBy;
    private DateTime lastModifiedDate;
    private java.io.Serializable id;

    public User createdBy() //...
    public void createdBy_$eq(User) //...
    public User getCreatedBy() //...
    public void setCreatedBy(User) //...

    public DateTime createdDate() //...
    public void createdDate_$eq(DateTime) //...
    public DateTime getCreatedDate() //...
    public void setCreatedDate(DateTime) //...

    public boolean isNew();

    //...
}
```

There is actually much more, but you get the idea.
So fields aren't refactored into a separate class, but that was to be expected.
Instead fields are copied into every single class extending this particular trait.
In Java we could have used abstract base class for that, but it's nice to reserve inheritance for real *is-a* relationships and do not use it for dummy field holders.
In Scala trait is such a holder, grouping common fields that we can reuse across several classes.

What about Java interoperability?
Well, `IAmAuditable` is compiled down to Java interface, thus it doesn't have fields at all.
If you implement it from Java, you gain nothing special.

We covered basic use cases for traits in Scala and their implementation.
In the next article [we will explore how mixins and stackable modifications work](http://nurkiewicz.blogspot.no/2013/04/scala-traits-implementation-and_3.html).
