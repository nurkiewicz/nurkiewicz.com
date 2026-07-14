---
layout: post
title: What features of Java have been dropped in Scala?
date: '2011-08-07T18:15:00.002+02:00'
author: Tomasz Nurkiewicz
tags:
- scala
modified_time: '2011-11-17T19:25:44.807+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3527227597997947083
blogger_orig_url: https://www.nurkiewicz.com/2011/08/what-features-of-java-have-been-dropped.html
---

Despite more complex and less intuitive syntax compared to Java, Scala actually drops several features of Java, sometimes for good, other times providing replacements on the standard library level.
As you will see soon, Scala isn't a superset of Java (like Groovy) and actually removes a lot of noise.
Below is a catalogue of *the missing features*.

#### break and continue in loops

Every time I see code like this:

```java

while(cond1) {
    work();
    if(cond2)
        continue;
    rest();
}
```

I feel as if it has been written by a guy who truly misses the times when goto wasn't yet considered harmful.
Hands up who finds this version more readable:

```java

while(cond1) {
    work();
    if(!cond2)
        rest();
}
```

Getting rid of break requires a little more though, but generally extracting a loop to a separate method/function (or at least putting it at the end of existing method) and using return instead will do the trick.
By the why Scala allows you to define functions inside other functions, so you won't pollute your global class namespace with plenty of small methods used only once – problem that sometimes arises when [religiously](http://www.amazon.com/gp/product/0132350882/ref=as_li_ss_tl?ie=UTF8&tag=javaandneighb-20&linkCode=as2&camp=217145&creative=399369&creativeASIN=0132350882) extracting methods in Java.

break and continue – we thank you in the name of our fathers and grandfathers for your contribution to imperative programming.
But we no longer need you and we won't miss you.

#### Arrays

It's amazing how many bad habits have we learnt by all these years and how we got used to idioms that are inconsistent and simply painful.
You have covariant arrays in Java with square brackets syntax, length final property and ability to store primitive types.
You also have Java collections framework with List\&amp;lt;T\&amp;gt; abstraction – that is not covariant, uses get() and size() methods and can't store primitives.
The list of differences does not end here, however isn't every array just a special case of List?
Why do we have a special syntax for arrays in the language while collections are implemented in on top of the language?
And isn't a bit irritating to convert them from one to another all the time?

```java

String[] array = new String[10];
List<String> list = Arrays.asList(array);
String[] array2 = list.toArray(new String[list.size()]);
```

Converting from collection to array is my favourite Java idiom...
Why not just have same syntax, same methods, same abstraction, polymorphic behaviour – and only different implementation names?

```scala

val array = Array("ab", "c", "def")
println(array(1))
array filter (_.size > 1)

val list = List("ab", "c", "def")
println(list(1))
println(list filter (_.size > 1))
```

And don't worry, behind the scenes Scala compiler will use the same efficient array bytecode as if you were using plain arrays in Java.
No magic abstractions and several layers of wrapping.

#### Primitives

Another weird Java inconsistency – why do we have a choice between primitive int and wrapping Integer?
If the variable is of Integer type does this mean it is optional (null), or is it just that you can't use primitives in collections (but can in arrays, as pointed out above)?
Is this unboxing safe (also known as: *how on earth this can throw NullPointerException*?)
Can I compare these to integers using == operator?
And can I simply call toString() to get string representation of this number?

In Scala you no longer have a choice, every primitive type is an object, while most of the time still being a primitive in memory and in bytecode.
How is that possible?
Have a look at the following popular example:

```scala

val x = 37     //x and y are objects of type Int
val y = 5
val z = x + y  //x.+(y) - yes, Int class has a "+" method
assert(z.toString == "42")
```

x, y and z are instances of type Int.
They are all objects, even adding two integers is semantically a method + called on x with y argument.
If you think it has to perform terribly – once again behind the scenes it is compiled into ordinary primitive addition.
But now you can easily use primitives in collections, pass them when any type is required (Object in Java, Any in Scala) or simply create a text representation without awkward Integer.toString(7) idiom.
Sooo many bad habits.

#### Checked exceptions

Another feature that I can hardly miss.
Not much to be said here.
Neither any mainstream language except Java have them, nor any mainstream JVM language (except Java).
This topic is still relatively controversial, however if you've ever tried to deal with ubiquitous SQLException or IOException, you know how much boilerplate it introduces without good reason.
Anyway, look at the next examples...

#### Interfaces

This one is good!
Scala doesn't have interfaces.
Instead it introduces traits – something in between abstract classes (some trait methods might have implementation) and interfaces (one can mix in more than one trait).
So essentially traits enables you to implement multiple inheritance while avoiding dreadful [diamond problem](http://en.wikipedia.org/wiki/Diamond_problem).
How it is done requires an article on its own (in short: last trait wins), but I would rather show you an example how helpful traits are to reduce duplication.

Suppose you are writing an interface to abstract binary protocol.
Most implementations take raw byte array, so in Java you would simply say:

```java

public interface Marshaller {
    long send(byte[] content);
}
```

This is great from the implementation perspective – just implement a single method and the abstraction is ready.
However users of the interface are complaining that it is cumbersome and not very convenient.
They would like to send strings, binary and text streams, serialized objects and so on.
They can either create a facade around this interface (and every user will create his/hers very own with a distinct set of bugs) or force the author of the API to extend it:

```java

public interface Marshaller {

    long send(byte[] content);

    long send(InputStream stream);
 
    long send(Reader reader);
 
    long send(String s);

    long send(Serializable obj);

}
```

Now the API is a breeze, however every implementation has to implement five methods instead of one.
Also note that since most abstracted protocols are based on byte arrays, all the methods can be implemented in terms of the first one.
And only the first one contains the actual marshalling code.
This in turns causes every implementation to have the exact same four methods – duplication didn't go away – it has just been moved.
Actually this problem is known as a thin vs. rich interface and it has been described in great [Programming in Scala](http://www.amazon.com/gp/product/0981531644/ref=as_li_ss_tl?ie=UTF8&tag=javaandneighb-20&linkCode=as2&camp=217145&creative=399369&creativeASIN=0981531644) book.
What I was typically doing was to give service providers an abstract class with typical implementations of all the methods except the root one, which was used by all other methods:

```java

import org.apache.commons.io.IOUtils;

public abstract class MarshallerSupport implements Marshaller {

    @Override
    public abstract long send(byte[] content);

    @Override
    public long send(InputStream stream) {
        try {
            return send(IOUtils.toByteArray(stream));
        } catch (IOException e) {
            throw new RuntimeException(e);  //choose something more specific in real life
        }
    }

    @Override
    public long send(Reader reader) {
        try {
            return send(IOUtils.toByteArray(reader));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public long send(String s) {
        try {
            return send(s.getBytes("UTF8"));
        } catch (UnsupportedEncodingException e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public long send(Serializable obj) {
        try {
            final ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            new ObjectOutputStream(bytes).writeObject(obj);
            return send(bytes.toByteArray());
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

}
```

Now everyone is happy – instead of copying all the overloaded methods over and over, just subclass the MarshallerSupport and implement what you need.
But what if your interface implementation also has to subclass some other class?
You are out of luck then.
In Scala however you change the interface to trait, opening the possibility to mix in (think something between extending and implementing) several other traits.
By the way do you remember what I said about checked exceptions?

```scala

trait MarshallerSupport extends Marshaller {

    def send(content: Array[Byte]): Long

    def send(stream: InputStream): Long = send(IOUtils.toByteArray(stream))

    def send(reader: Reader): Long = send(IOUtils.toByteArray(reader))

    def send(s: String): Long = send(s.getBytes("UTF8"))

    def send(obj: Serializable): Long = {
        val bytes = new ByteArrayOutputStream
        new ObjectOutputStream(bytes).writeObject(obj)
        send(bytes.toByteArray)
    }
}
```

#### Switch statement

There is no switch statement in Scala.
Calling [pattern matching](http://www.scala-lang.org/node/120) a better switch would be a blasphemy.
Not only because pattern matching in Scala is an expression returning a value and also not because you can switch over literally any value if you want.
Not even because there is no fall-through, break and default.
It's because Scala's pattern matching enables you to match whole object structures and lists, even with wildcards.
Consider this expression simplification method, originally taken from already mentioned [Programming in Scala](http://www.amazon.com/gp/product/0981531644/ref=as_li_ss_tl?ie=UTF8&tag=javaandneighb-20&linkCode=as2&camp=217145&creative=399369&creativeASIN=0981531644) book:

```scala

abstract class Expr
case class Var(name: String) extends Expr
case class Number(num: Double) extends Expr
case class UnOp(operator: String, arg: Expr) extends Expr
case class BinOp(operator: String, left: Expr, right: Expr) extends Expr

//...

def simplify(expr: Expr): Expr = expr match {
    case UnOp("-", UnOp("-", e)) => e  //double negation
    case BinOp("+", e, Number(0)) => e //adding zero
    case BinOp("*", e, Number(1)) => e //multiplying by one
    case _ => expr
}
```

Look carefully how clever this code is!
If our expression is unary “-” operation and the argument is a second unary “-” operation with any expression e as an argument (think: -(-e)), then simply return e.
If you find this pattern matching example hard to read, check out the roughly equivalent Java code.
However please remember: size doesn't matter (one could probably do the same with Perl one-liner) – it's about readability and maintainability:

```java

public Expr simplify(Expr expr) {
    if (expr instanceof UnOp) {
        UnOp unOp = (UnOp) expr;
        if (unOp.getOperator().equals("-")) {
            if (unOp.getArg() instanceof UnOp) {
                UnOp arg = (UnOp) unOp.getArg();
                if (arg.getOperator().equals("-"))
                    return arg.getArg();
            }
        }
    }
    if (expr instanceof BinOp) {
        BinOp binOp = (BinOp) expr;
        if (binOp.getRight() instanceof Number) {
            Number arg = (Number) binOp.getRight();
            if (binOp.getOperator().equals("+") && arg.getNum() == 0 ||
                    binOp.getOperator().equals("*") && arg.getNum() == 1)
                return binOp.getLeft();
        }
    }
    return expr;
}
```

UPDATE: In one of the comments *Yassine Elouafi*claims this example is too limited as it can not simplify nested expressions like: BinOp("+", Var("x"), BinOp("\*", Var("y"), Number(0))) which reads: x + y \* 0.
Indeed this algorithm assumes nested terms are already simplified.
But it should be pretty obvious to improve this code to work with arbitrary complex expressions – without loosing readability.
Recursion with bottom-up approach seems perfect: simplify the leaves first (simplest terms) and go up.
Here is the improved code:

```scala

def simplify(expr: Expr): Expr = expr match {
    case UnOp("-", UnOp("-", e)) => simplify(e)
    case BinOp("+", e, Number(0)) => simplify(e)
    case b@BinOp("+", _, _) => simplify(BinOp(b.operator, simplify(b.left), simplify(b.right)))
    case BinOp("*", e, Number(1)) => simplify(e)
    case BinOp("*", e, Number(0)) => Number(0)
    case _ => expr
}
```

Not that bad, don't you think?
Of course there are still several improvements that might be applied (0 + e, 1 \* e, operations on constants, etc.), but thanks to the power of recursion the results are already quite impressive:

```scala

//x + y * 0
assert(simplify(BinOp("+", Var("x"), BinOp("*", Var("y"), Number(0)))) === Var("x"))

//(x + y) * 0
assert(simplify(BinOp("*", BinOp("+", Var("x"), Var("y")), Number(0))) === Number(0.0))

//-(-(-(-5)))
assert(simplify(UnOp("-", UnOp("-", UnOp("-", UnOp("-", Number(5)))))) === Number(5.0))

//y * 1 + (x + z) * 0
assert(
    simplify(
        BinOp(
            "+",
            BinOp(
                "*",
                Var("y"),
                Number(1)
            ),
            BinOp(
                "*",
                BinOp(
                    "+",
                    Var("x"),
                    Var("z")
                ),
                Number(0)
            )
        )
    ) === Var("y")
)
```

So is Scala scalable?

#### instanceof/casting

As with many other features, Scala does not have a built-in syntax for instanceof and downcasting.
Instead the language provides you methods on actual objects:

```scala

val b: Boolean = expr.isInstanceOf[UnOp]
val unOp: UnOp = expr.asInstanceOf[UnOp]
```

In Scala a lot of features normally considered as part of the language are actually implemented in the language itself or at least they don't require a special syntax.
I like this idea, in fact I find Ruby's way of creating objects (Foo.new – method instead of new operator) very attractive and even unusual lack of if conditionals in Smalltalk requires some [attention](http://en.wikipedia.org/wiki/Smalltalk#Control_structures).

#### Enums

Scala doesn't have built-in support for enums.
Enumerations in Java are known to have several fancy features which other languages envy like type safety and ability to add methods to each enum.
There are at least two ways to emulate enums in Scala:

```scala

object Status extends Enumeration {
   type Status = Value

   val Pending = Value("Pending...")
   val Accepted = Value("Accepted :-)")
   val Rejected = Value("Rejected :-(")
}

assume(Status.Pending.toString == "Pending...")
assume(Status.withName("Rejected :-(") == Status.Rejected)
```

Or if you don't care about textual enum representation:

```scala

object Status extends Enumeration {
   type Status = Value

   val Pending, Accepted, Rejected = Value
}
```

However the second and the most comprehensive way to emulate enums is to use case classes.
Side note: name is actually an abstract method defined in base class.
When you declare a method without defining the method body it is implicitly assumed to be abstract – no need to mark the obvious with extra keywords:

```scala

sealed abstract class Status(val code: Int) {
 def name: String
}

case object Pending extends Status(0) {
 override def name = "?"
}

case object Accepted extends Status(1) {
 override def name = "+"
}

case object Rejected extends Status(-1) {
 override def name = "-"
}

//...

val s: Status = Accepted

assume(s.name == "+")
assume(s.code == 1)

s match {
    case Pending =>
    case Accepted =>
    case Rejected =>  //comment this line, you'll see compiler warning
}
```

This approach, although has nothing to do with enums per se, has many advantages.
The biggest one is that the compiler will warn you when performing non exhaustive pattern matching – think: switch over an enum in Java without explicitly referencing each and every value or default block.

#### Static methods/fields

Scala doesn't have a notion of static fields and methods.
Instead it has a feature named objects as opposed to classes.
When you define a class using object keyword, Scala runtime will eagerly create one instance of this class and make it available under class name.
This is essentially a *singleton* pattern built into the language but the most important is the mindset shift introduced by this approach.
Instead of a bunch of static functions artificially gathered together inside a class (which is only a *de facto* namespace in this case) you have a singleton with *true* methods:

```scala

sealed abstract class Status
case object Pending extends Status
case object Accepted extends Status
case object Rejected extends Status

case class Application(status: Status, name: String)

object Util {

    def groupByStatus(applications: Seq[Application]) = applications groupBy {_.status}

}
```

Here is how the syntax works (and nice [ScalaTest](http://www.scalatest.org/scaladoc-1.6.1/#org.scalatest.matchers.ShouldMatchers) DSL example):

```scala

@RunWith(classOf[JUnitRunner])
class UtilTest extends FunSuite with ShouldMatchers {

   type ? = this.type

   test("should group applications by status") {
      val applications = List(
         Application(Pending, "Lorem"),
         Application(Accepted, "ipsum"),
         Application(Accepted, "dolor")
      )

      val appsPerStatus = Util.groupByStatus(applications)

      appsPerStatus should have size (2)
      appsPerStatus(Pending) should (
            have size (1) and
            contain (Application(Pending, "Lorem"))
      )
      appsPerStatus(Accepted) should (
            have size (2) and
            contain (Application(Accepted, "ipsum")) and
            contain (Application(Accepted, "dolor"))
      )
   }
}
```

#### volatile/transient/native and serialVersionUID are gone

The language designers decided to convert the first three keywords into annotations.
Both approaches have pros and cons, hard to find the clear winner.
However turning serialVersionUID into a class level annotation is a pretty good choice.
I know this field existed long before annotations were introduced to the Java language, so we shouldn't blame it.
But I always hated when in statically typed languages some names/fields have special meaning not reflected anywhere except the language specification itself (*magic numbers?*) Unfortunately there are examples of this unpleasant behaviour in Scala as well, namely special treatment of apply() method and methods ending with colon.
Too bad.

#### Pre/post-increment

You cannot do i++ and ++i in Scala.
Period.
You need a bit more verbose i += 1 – and to make matters worse this expression return Unit (think: void).
How can we deal with this noticeable feature missing?
Turns out that very often this type of constructs are imperative style legacy and they can easily be avoided by using more functional and pure constructs.
Take the following problem as an example:

You have two same sized arrays: one with names and a second one with ages.
Now you want to display each name with a corresponding age – somehow iterating over both arrays in parallel.
In Java this is surprisingly tough to implement cleanly:

```java

String[] names = new String[]{"Alice", "Bobby", "Eve", "Jane"};
Integer[] ages = new Integer[]{27, 31, 29, 25};

int curAgeIdx = 0;
for (String name : names) {
    System.out.println(name + ": " + ages[curAgeIdx]);
    ++curAgeIdx;
}

//or:

for(int idx = 0; idx < names.length; ++idx)
    System.out.println(names[idx] + ": " + ages[idx]);
}
```

In Scala maybe it is shorter, but very mysterious at first:

```scala

var names = Array("Alice", "Bobby", "Eve", "Jane")
var ages = Array(27, 31, 29, 25)

names zip ages foreach {p => println(p._1 + ": " + p._2)}
```

zip?
I encourage you play a bit with this example.
If you don't feel like starting up the whole IDE, try it with Scala REPL:

```bash

$ scala
scala> Array("one", "two", "three") zip Array(1, 2, 31)   
res1: Array[(java.lang.String, Int)] = Array((one,1), (two,2), (three,31))
```

Look carefully, do you see the result array containing pairs of corresponding elements from the first and the second arrays “*zipped*” together?
One simple experiment and now suddenly it should be clear and much more readable than ordinary imperative solution.

Scala inventors looked very thoroughly on Java language and they didn't just add syntactic sugar (like function literals or implicit conversions).
They discovered plenty of inconsistencies and annoyances in Java, getting rid of them and providing more concise and deliberate replacements.
Despite higher level constructs like primitive and array objects, under the hood the same fast and straightforward bytecode is generated.
