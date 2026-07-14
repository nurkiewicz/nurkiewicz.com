---
layout: post
title: eta-expansion (internals) in Scala explained
date: '2012-04-06T11:03:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- scala
- spring
modified_time: '2012-04-07T22:54:46.300+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-6619693093259505249
blogger_orig_url: https://www.nurkiewicz.com/2012/04/eta-expansion-internals-in-scala.html
---

Today we will learn how Scala compiler implements very important aspect of the language known as an *eta-expansion*.
We will see how `scalac` works around the limitations of JVM, in particular with the lack of higher-order functions.
But before we begin, to a great surprise, we shall see how these limitations are bypassed by...
the Java language itself!

Here is the easiest piece of code taking full advantage of anonymous inner classes in Java: the inner class calls method from an outer class.
As you probably know every inner class has an implicit hidden `Parent.this` reference to an outer (*parent*) class.
This is illustrated by the following example:

```java
public class TestJ {
  public Runnable foo() {
    return new Runnable() {
      public void run() {
        inc(5);
      }
    };
  }

  private int inc(int x) {
    return x + 1;
  }

}
```

Anonymous inner class calls private method of its parent completely transparently.
Have you ever wondered how does an inner class get access to private methods and fields of its parent?
It is not because an inner class is defined inside parent - from the JVM point of view these are two completely independent classes where the anonymous one is named `TestJ$1`.
It is also not a result of the JVM support for inner classes - because there is no such.
So how come some arbitrary class can call private methods of `TestJ`?
Let us see what is under the hood:

```text
$ javac TestJ.java
$ javap -private TestJ
Compiled from "TestJ.java"
public class TestJ extends java.lang.Object{
    public TestJ();
    public java.lang.Runnable foo();
    private int inc(int);
    static int access$000(TestJ, int);
}
```

Isn't oddly named static `access$000(TestJ, int)` method a bit disturbing?
Superficial decompilation reveals unexpected and possibly dangerous *back door* in `TestJ`:

```java
static int access$000(TestJ testJ, int x) {
  return testJ.inc(x);
}
```

And in the inner class itself:

```java
class TestJ$1 implements java.lang.Runnable {

  final TestJ parent;

  TestJ$1(TestJ parent) {
    this. parent = parent;
  }

  public void run() {
    TestJ.access$000(parent, 5)
  }
}
```

Inner classes (including anonymous) are in fact emulated by the JVM/compiler using very simple techniques: the inner class receives a reference to its parent via constructor argument and instead of calling private methods of a parent it calls a special, invisible static method passing that parent.
Accessing private parents' fields uses the same approach.

```java
public class TestJ {
  public Runnable foo() {
    return new TestJ$1(this);
  }

  private int inc(int x) {
    return x + 1;
  }

}
```

Is this behaviour safe or not transparent in any way?
No, because synthetic `access...()` methods are invisible for reflection and only sometimes appear in stack traces.
So what does it all have to do with Scala and aforementioned *eta-expansion*?
And what it really is?

In Scala there is a distinction between methods and functions.
Methods in Scala and methods in Java are compiled to exactly same bytecode:

```scala
class Test {
  private def inc(x: Int) = x + 1
}
```

After compiling and decompiling back to Java we will see something familiar:

```java
public class Test {
  private int inc(int x) {
    return x + 1;
  }
}
```

Unfortunately neither in JVM nor in Java we can pass methods as arguments of other methods or return them (this is called *higher-order function* - and even JavaScript can do this!)
But in Scala we can write:

```scala
def inc(x: Int) = x + 1

List(1, 2) map inc  //returns List(2, 3)
```

This trivial idiom passes `inc()` method as an argument of `List.map()`.
In order to make this to work the compiler performs a process called *eta-expansion* for us.
Basically it wraps the execution of `inc()` inside an object.
This object has a single significant method named `apply()` which calls `inc()`.
As you probably guessed it is also an anonymous inner class:

```scala
List(1,2) map new Function1[Int, Int] {
  def apply(x: Int) = inc(x)
}

private def inc(x: Int) = x + 1
```

This is (more or less) compilable Scala code without syntactic sugar.
See how dangerously close we are to a way one would implement `map()` in Java - anonymous inner class with a single method.

Fortunately this process is completely transparent and we almost never have to bother about it.
However I would like to mention about subtle implementation difference with regards to accessing private method from the inner class:

```text
$ scalac Test.scala
$ javap -private Test
Compiled from "Test.scala"
public class Test extends java.lang.Object implements scala.ScalaObject{
    public final int Test$$inc(int);
    public Test();
}
```

Previously private `inc()` method suddenly changed the name, became public and final.
As you can see it serves the same purpose as `access$000()` in anonymous (inner) classes in Java, however instead of special static methods Scala developers decided to bypass standard encapsulation methods in a more object-oriented manner.
This is how the “*real*" code looks like:

```java
public final class Test$$anonfun$1 implements Function1 {

  private final Test parent;

  public int apply(int x) {
    return parent.Test$$inc(x);  //calling Test.inc()
  }

  public Test$$anonfun$1(Test parent);
    this. parent = parent;
  }
}
```

And usage:

```scala
List(1,2).map(new Test$$anonfun$1(this))
```

Why do we even bother about such subtle and internal matters in generated bytecode?
It turns out that the Scala way of compiling inner classes confuses the Spring framework.
Here is a very short working Spring application (no need for XML, this is the whole code):

```scala
case class OrderLine(name: String, count: Int)
case class Order(customerName: String, lines: Seq[OrderLine])

@Service
@Transactional
class OrderValidator {

  def allOrderLinesValid(order: Order): Boolean = order.lines forall valid
  def valid(line: OrderLine) = line.count > 0

}

@Configuration
@EnableTransactionManagement(proxyTargetClass = true)
class SpringBootstrap {

  @Bean
  def orderValidator() = new OrderValidator()

  @Bean
  def transactionManager() = Mockito mock classOf[PlatformTransactionManager]

}

object SpringBootstrap extends App {
  val context = new AnnotationConfigApplicationContext(classOf[SpringBootstrap])
  context.close()
}
```

For simplicity I mock transaction manager so that I can use `@Transactional`.
Everything works as expected, however after changing the access modifier of `valid()` method from `public` (default) to `private` we get unexpected warning printed during startup:

```text
o.s.a.f.Cglib2AopProxy | Unable to proxy method [public final boolean OrderValidator.OrderValidator$$valid(OrderLine)] because it is final: All calls to this method via a proxy will be routed directly to the proxy.
```

The meaning of this error is now irrelevant.
But what is this ` public final OrderValidator$$valid(OrderLine)` method doing here?
IT turns out that after hiding `valid()` under `private` modifier the eta-expansion mechanism had to somehow made it public again - by also obfuscating the original name.
However, in contrary to Java compiler (generating static methods following `access$000` naming convention), the ones generated by `scalac` aren't “protected" by the JVM and hidden from reflection.
Spring sees them, although we don't.

It is an open question whether this implementation is a potential security hole in generated classes.
If that is the case, fortunately the fix is simple (?)
- `scalac` should follow naming conventions compatible with `javac`.

> This was a translation of my article ["Jak działa (i czym jest) eta expansion?"](http://scala.net.pl/jak-dziala-eta-expansion/)
> originally published on [scala.net.pl](http://scala.net.pl).
