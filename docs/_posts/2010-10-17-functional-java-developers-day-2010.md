---
layout: post
title: Functional Java Developers’ Day 2010
date: '2010-10-17T16:39:00.001+02:00'
author: Tomasz Nurkiewicz
tags:
- conferences
- scala
modified_time: '2011-11-17T19:06:03.745+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2059029815651797737
blogger_orig_url: https://www.nurkiewicz.com/2010/10/functional-java-developers-day-2010.html
---

**Ted Neward**s’ talk about functional programming in Java and his workshop on Scala (hence the article title) were the most memorable events during the third [JDD](http://10.jdd.org.pl/) conference that I attended last week.
Sadly most memorable, and almost the only ones.
But first things first.

After spending endless hours with great [Enterprise JavaBeans 3.0](http://www.amazon.com/gp/product/059600978X?ie=UTF8&tag=javaandneighb-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=059600978X) book by **Bill Burke** I’ve expected something fabulous, but Bills’ lecture about JAX-RS was just average, with no coding, only plain API introduction.
Scott Davis' presenting REST and ROA [last year](http://nurkiewicz.com/2009/10/yesterday-i-had-pleasure-to-participate.html) was way much better.
Thankfully **Angelika Langer** talk about Java concurrency pitfalls was much more interesting, although one might argue that she just gave a summary of marvelous [Java Concurrency in Practice](http://www.amazon.com/gp/product/0321349601?ie=UTF8&tag=javaandneighb-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=0321349601) book, that I have [recommended](http://nurkiewicz.com/2009/08/java-concurrency-in-practice-written-by.html) long time ago.
One new thing I’ve learnt is that updating volatile variable guarantees all other non-volatile variable updated earlier by the same thread to be visible by other threads, as if they were volatile as well (are you following?)
After Angelika there was a talk about Java performance testing, but I had a copy of [The Art of Application Performance Testing](http://www.amazon.com/gp/product/0596520662?ie=UTF8&tag=javaandneighb-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=0596520662) book in my knapsack, so the presentation didn’t caught a lot of my attention.

After delicious lunch Ted Neward gave a talk on functional programming concepts in Java.
Charismatic, entertaining, surprising – I knew he will make a great show.
In the middle of third or fourth slide he asked innocently who prefers slides to live coding and after finding no such person on the audience, he instantly closed the presentation and opened notepad, writing some Java code from scratch.
It looked so natural that I almost believed that he actually had any slides further – but of course this was all set up.
Ted mentioned [Functional Java](http://functionaljava.org/) library as a way to enable functional style of programming in plain old Java.
Another libraries I can point out if you have to stick with this language are: [Fun4J](http://www.fun4j.org/), Google's [Guava](http://code.google.com/p/guava-libraries) and [LambdaJ](http://code.google.com/p/lambdaj).
Also take a look at [Lombok](http://projectlombok.org/) to write more concise POJOs.

I’ve seen **Piotr Walczyszyn** several times evangelizing Flex and AIR so it came a bit of a surprise that I really enjoyed his talk, even though I don’t like front-end programming.
But a real surprise was the **Linda Rising** presentation dealing with the problem of introducing change and convincing our coworkers to it.
From time to time we need to look at our job from 10,000 ft perspective, see how ridiculously we sometimes behave and how irrational our choices are.
[See Pragmatic Thinking and Learning...](http://www.amazon.com/gp/product/1934356050?ie=UTF8&tag=javaandneighb-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=1934356050)
for a more in-depth analysis on this.
Also I recently read marvelous [Dreaming in Code](http://www.amazon.com/gp/product/1400082471?ie=UTF8&tag=javaandneighb-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=1400082471) by Scott Rosenberg.
Linda’s talk complemented these books excellently.

On the next day I sacrificed three presentations to participate in Ted Neward’s workshop on Scala – continuing the subject of functional programming.
He introduced Scala language step by step, emphasizing the differences and commons misconceptions.
I will repeat after him: Scala is compiled, statically typed, *consistent* language, don’t compare it with Groovy, these are completely different tools.
I was doing my best to follow Ted’s examples on my computer and finally I wrote few simple (compiling!)
lines of Scala code.
Too bad my first presentation on Scala ([during GeeCON 2009](http://nurkiewicz.com/2009/05/relacja-z-geecon-2009-w-krakowie.html)) by Luc Duponcheel wasn’t that good and simply beyond my comprehension.
Here are few examples of Scala concepts that significantly caught my attention.
POJO in Scala:

```scala

import org.apache.commons.lang.builder._

class Book(author: String, title: String, year: Int) {

  override def toString =
    new ToStringBuilder()
      .append("author", author)
      .append("title", title)
      .append("year", year)
      .toString()
}
```

Please note few things.
Firstly, interacting with Java libraries (Apache Commons Lang in this example) is straightforward.
Secondly all the types are objects, including primitives (Int – consistency!)
But the most important issue is: where are the fields?!?
Scala compiler (scalac) is a one clever beast: after finding constructor arguments and variables used in toString() method matching them it figured out that the programmer’s intention was to assign constructor arguments to fields so that toString() can use these fields afterwards.
Here is the proof:

```java

//javap -private Book

Compiled from "Book.scala"
public class Book extends java.lang.Object implements scala.ScalaObject{
    private final java.lang.String author;
    private final java.lang.String title;
    private final int year;
    public java.lang.String toString();
    public Book(java.lang.String, java.lang.String, int);
}
```

And a better proof if you are bytecode-capable:

```java

//javap -c Book
//...

public Book(java.lang.String, java.lang.String, int);
  Code:
   0:   aload_0
   1:   aload_1
   2:   putfield        #28; //Field author:Ljava/lang/String;
   5:   aload_0
   6:   aload_2
   7:   putfield        #35; //Field title:Ljava/lang/String;
   10:  aload_0
   11:  iload_3
   12:  putfield        #38; //Field year:I
   15:  aload_0
   16:  invokespecial   #49; //Method java/lang/Object."<init>":()V
   19:  return

}
```

Need getters?
Prepend every constructor argument with val keyword.
Setters as well?
Replace val (*value*) with var (*variable*).
No boilerplate code, no code generation needed.
Second more comprehensive example is Scala’s match operator:

```scala

def capitalizeAfterHash(list: List[Char]): List[Char] =
  list match {
    case '#' :: rest =>
      rest.map(_.toUpper)
    case _ :: rest =>
      capitalizeAfterHash(rest)
    case Nil =>
      Nil
  }

println(capitalizeAfterHash('a' :: 'b' :: '#' :: 'c' :: 'd' :: Nil))
println(capitalizeAfterHash('#' :: 'c' :: 'd' :: Nil))
println(capitalizeAfterHash('a' :: 'b' :: Nil))
```

Match is like switch on steroids.
In this example it is used to match list of characters against some patterns.
The last case means: "*if list is empty (Nil), return empty list*."
The first case states: "*if the first element of the list is ‘#’, take the rest of the list and call toUpper() on every item ("\_" placeholder)*".
Finally the second case is: "*if the first element of the list has any value (except ‘#’ examined earlier), call recursively capitalizeAfterHash with the rest of the list (effectively: repeat without the first element)*".
Can you guess what does this function do?

Scala is not for everybody and you need to have some solid programming background to fully appreciate its expressiveness.
I don’t think I will choose Scala from my toolbox anytime soon, but I will definitely follow this language development.
Actually, after observing what is currently happening with JDK 7 (and 8...)
I will say loudly: "Java (the language) is dead, long live Java (the JVM)".
Some time ago Sun was waiting for so long to develop new, easier and more productive version of their EJB 2.1 standard that competitors came up with much better, although non-standard solutions (think: Spring).
Now the same thing is happening with Java (the language) and other JVM languages.
That’s why interoperability between new JVM languages and Java code is so important: one day we will end up with tons of legacy code in (dead) Java language (because Sun/Oracle was too reluctant to update the language; see F#, LINQ, etc.), adding new features and rewriting parts of old systems in new, dynamic and more productive languages.
JVM is great, but one day Java will become only a historic language, reference and exemplary implementation, not used anymore.
Like [reference counting](http://en.wikipedia.org/wiki/Reference_counting) as a way of implementing garbage collection.

Where was I?
Oh, JDD 2010.
To be honest, nothing interesting happened after marvelous Ted Neward’s workshop.
At least two presentations were extremely boring, but I had no choice, as there was only one track.
Actually, if we exclude workshops, the amount of presentations was comparable to last year, even though the conference lasted for 2 days in the contrary to one day in 2009.
But last year there were two independent tracks.
So the conference was two times longer (which was the biggest demand of the participants last year, including myself) but introduced similar number of presentations – nice marketing trick!
The second demand was to change the place where the conference was taking place last year (sports hall with plastic chairs?
*C'mon!*) Seems like this suggestion was somehow missed...

Thankfully I attended very interesting presentations by Ted Neward, Linda Rising and Angelika Langer.
Without them I would be somewhat disappointed by this year’s Java Developers’ Day.
Main tips for organizers: find a comfortable conference centre and don’t force people to attend sponsored talks.
And don’t stop!
As still JDD is a great event with lots of potential.
