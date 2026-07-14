---
layout: post
title: Java features applicability
date: '2012-10-28T22:28:00.000+01:00'
author: Tomasz Nurkiewicz
tags: 
modified_time: '2012-10-28T23:38:14.725+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4778318691311508573
blogger_orig_url: https://www.nurkiewicz.com/2012/10/java-features-applicability.html
image: /assets/img/java-features-applicability/hero.png
---

Java language and standard library is powerful, but [*with great power comes great responsibility*](http://en.wikipedia.org/wiki/Uncle_Ben#.22With_great_power_comes_great_responsibility.22).
After seeing a lot of user code misusing or abusing rare Java features on one hand and completely forgetting about most basic feature on the other, I decided to compose this summary.
This is **not** a list of requirements and areas every Java developer should explore, know and use.
It's quite the opposite!
I group Java features in three categories: *day to day*, *occasionally* and *never (frameworks and libraries only)*.
The rule is simple: if you find yourself using given feature more often then suggested, you are probably over-engineering or trying to build something too general and too reusable.
If you don't use given feature often enough (according to my subjective list), you're probably missing some really interesting and important opportunities.
Note that I only focus on Java, JVM and JDK.
I do not suggest which frameworks and how likely you should use.
Also I assume typical, server-side business-facing application.

------------------------------------------------------------------------

#### Day to day

The following features of the Java language are suppose to be used every day.
If you have never seen some of them or find yourself using them very rarely, you might take a closer look, they are really helpful:

- **classes, interfaces, packages** - seriously.
  Put your code in classes.
  You remember from the university that class is an encapsulated data + methods acting upon that data?
  Class with only state is barely a structure.
  Class with only methods is just a namespace enclosing functions.
  Also use interfaces whenever needed.
  But think twice before creating an interface with only one implementation.
  Maybe you don't need a middleman?
  Nevertheless, put everything in packages, following [well established naming convention](http://docs.oracle.com/javase/tutorial/java/package/namingpkgs.html).
- **static methods** - don't be afraid of them.
  But use them only for stateless utility methods.
  Don't encode any business logic inside `static` method, ever.
- [**`ExecutorService` - thread pools**](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Executors.html) - creating and effectively using thread pools, understanding how queueing and [`Future<T>`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Future.html) works is a must.
  Don't reimplement thread pools, think about them every time someone says *producer-consumer*.
- [**`Atomic`-\* family**](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/atomic/package-summary.html) - don't use `synchronized` to barely read/update some counter or reference atomically.
  `Atomic`-\* family of classes use effective [*compare-and-swap*](http://en.wikipedia.org/wiki/Compare-and-swap) low-level instructions to be amazingly efficient.
  Make sure you understand the guarantees these classes provide.
- **design patterns** - Not technically a Java language part, but essential.
  You should, know, understand, and use them willingly but sparingly.
  Just like with interfaces - don't go overboard.
  [GoF](http://www.amazon.com/gp/product/0201633612/ref=as_li_ss_tl?ie=UTF8&tag=javaandneighb-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=0201633612) or even [EI patterns](http://rcm.amazon.com/e/cm?lt1=_blank&bc1=000000&IS2=1&bg1=FFFFFF&fc1=000000&lc1=0000FF&t=javaandneighb-20&o=1&p=8&l=as4&m=amazon&f=ifr&ref=ss_til&asins=0321200683) should often occur in the code base.
  But let patterns emerge during your thought process, rather than you letting your thought process be driven by patterns.
- **built-in collections, including concurrent** - you absolutely must know and use built in collections, understanding the differences between `List`, `Map` and `Set`.
  Using thread-safe collections should not be an issue for you.
  Understand performance characteristics and have basic overview of the implementation behind them.
  This is really basic.
  Also know and use various [`BlockingQueue`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/BlockingQueue.html) implementations.
  Concurrency is hard, don't make it even harder by reimplementing some of this stuff yourself.
- **Built-in annotations** - annotations are here to stay, learn to use [`@Override`](http://docs.oracle.com/javase/7/docs/api/java/lang/Override.html) (and [`@Deprecated`](http://docs.oracle.com/javase/7/docs/api/java/lang/Deprecated.html) to some degree) every day consistently.
- **exceptions** - use unchecked exceptions to signal abnormal, exceptional failure that requires action being taken.
  Learn to live with checked exceptions.
  Learn to read stack traces.
- [**try-with-resources**](http://docs.oracle.com/javase/tutorial/essential/exceptions/tryResourceClose.html) - familiarize yourself with this fabulous language construct.
  Implement [`AutoCloseable`](http://docs.oracle.com/javase/7/docs/api/java/lang/AutoCloseable.html) if your class requires any cleanup.
- **Blocking IO** - using [`Reader`](http://docs.oracle.com/javase/7/docs/api/java/io/Reader.html)/[`Writer`](http://docs.oracle.com/javase/7/docs/api/java/io/Writer.html), [`InputStream`](http://docs.oracle.com/javase/7/docs/api/java/io/InputStream.html)/[`OutputStream`](http://docs.oracle.com/javase/7/docs/api/java/io/OutputStream.html) classes is something you should be really familiar with.
  Understand the difference between them, using buffering and other decorators without fear.

This ends the list of everyday tools you should use.
If you've never heard of some of them or used them only occasionally, study them more carefully as they might become your lifesavers.

------------------------------------------------------------------------

#### Occasionally

Following are the language features you should not be afraid to use, but they should not be abused as well.
If you find yourself exploiting them every day, if these are kind of features you see several times before lunch, there may be something wrong with your design.
I am looking from a back-end, enterprise Java developer perspective.
These types of features are useful, but not too often.

- **inheritance and abstract classes** - really, it turns out I don't use inheritance that often and I don't really miss it.
  Polymorphism driven by interfaces is by far more flexible, especially with a painful lack of traits in Java.
  Also prefer [composition over inheritance](http://en.wikipedia.org/wiki/Composition_over_inheritance).
  Too many levels of inheritance lead to very unmaintainable code.

[![](/assets/img/java-features-applicability/1.png)](/assets/img/java-features-applicability/1.png)

- **regular expressions** - [*Some people, when confronted with a problem, think "I know, I'll use regular expressions."
  Now they have two problems.*](http://en.wikiquote.org/wiki/Jamie_Zawinski).
  The world without regular expressions would be much more boring and cumbersome.
  They are wonderful for parsing regular languages (but [not HTML](http://stackoverflow.com/a/1732454)) but its way too easy to overuse them.
  If you find yourself crafting, testing, fixing and coursing whole day in front of regular expressions, you are probably using wrong tool for the job.
  My all time favourite:

  ``` java
  public static boolean isNegative(int x) {
      return Integer.toString(x).matches("-[0-9]+");
  }
  ```

- **[`Semaphore`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Semaphore.html), [`CountDownLatch`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/CountDownLatch.html), [`CyclicBarrier`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/CyclicBarrier.html) and others** - they are all extremely useful better by an order of magnitude than infomous `wait()`/`notify()` pair.
  But even them won't prevent you from concurrency bugs when abused.
  Consider thread-safe collections or some frameworks when you see these synchronization mechanism too often.

- **generic types in user code** - using built-in collections and other classes that have generic types should not only be a day to day practice, it should be obvious for you.
  But I mean developing code yourself taking or returning generic types.
  Something like this:

  ``` java
  public <T, F> ContractValidator<T extends Contract> T validate(Validator<T>, F object)
  ```

  It is sometimes necessary to use generics in your own code, but don't go too *meta-*.
  Of course static typing and type safety should be your priority, but maybe you can avoid too many generic, complex types?

- [**Scripting languges in JVM**](http://docs.oracle.com/javase/6/docs/technotes/guides/scripting/programmer_guide/index.html) - do you know JDK has a built-in JavaScript interpreter?
  And that you can plug virtually any other language like Groovy or JRuby?
  Sometimes it's simpler to embed small script inside your application that can be changed even by the customer.
  It's not often, but in very fast changing markets redeploying might not be an option.
  Just remember that if the total number of lines of scripted code exceeds 1% of the total amount of your code, you should start worrying about maintenance.

- [**Java NIO**](http://docs.oracle.com/javase/7/docs/api/java/nio/package-summary.html) - it is hard to get it right and even harder to actually benefit from it.
  But in rare cases you actually have to use NIO to squeeze as much performance and scalability as you can.
  However prefer libraries that can do it for you.
  Also in normal circumstances blocking IO is typically enough.

- **`synchronized` keyword** - you should not use it too often for a simple reason.
  The more often it's used, the more often it's executed, thus impacting performance.
  Consider thread-safe collections and atomic primitive wrappers instead.
  Also make sure you always understand which object is used as a mutex.

I consider features above valuable and important, but not necessarily on a day-to-day basis.
If you see any of them every single day it might be a sign of over-engineered design or...
inexperienced developer.
Simplicity comes with experience.
However, you might also have very unusual requirements, which applies to the third group as well.

------------------------------------------------------------------------

#### Never (think: framework and library developers only)

You should know and understand the principles behind the features below in order to understand frameworks and libraries.
And you must understand them to effectively us them, I see way too many questions on StackOverflow that could have been avoided if the person in question simply read the code of a library in use.
But understanding doesn't mean use.
You should almost never use them directly, they are mostly advanced, dirty and complicated.
Even one occurrence of such feature can lead to major headaches.

- **sockets** - seriously, sockets.
  You must understand how TCP/IP stack works, be very conscious with regards to threading, careful when interpreting the data, vigilant with streams.
  Stay away from using pure sockets, there are hundreds of libraries wrapping them and providing higher level abstractions - HTTP, FTP, NTP, SMB, e-mail...
  (e.g.
  see [Apache Commons net](http://commons.apache.org/net/)).
  You'll be amazed how hard it is to write decent HTTP client or server.
  And if you need to write a server for some proprietary protocol, definitely consider [Netty](https://netty.io/).
- **reflection** - there is no place for introspecting classes and methods in business code.
  Frameworks can't live without reflection, I can't live with.
  Reflection makes your code slower, unsafe and ugly.
  Typically AOP is just enough.
  I would even say that passing instances of [`Class<T>`](http://docs.oracle.com/javase/7/docs/api/java/lang/Class.html) around is a code smell.
- **dynamic proxies and byte code manipulation** - [`Proxy` class](http://docs.oracle.com/javase/7/docs/api/java/lang/reflect/Proxy.html) is great, but just like reflection, should be used only by the frameworks and libraries that support you.
  They are a basic building block of lightweight AOP.
  If your business application (not framework or library, even [Mockito](http://code.google.com/p/mockito/) uses these techniques!)
  requires byte code generation or manipulation (e.g.
  [ASM](http://asm.ow2.org/) or [CGLIB](http://cglib.sourceforge.net/)) - ~~you're in a deep sh\*\*t~~ I will pray for you.
- **class loaders** - everything that has anything to do with class loaders.
  You must understand them, the hierarchy, bytecode, etc. But if you write your own class loaders, it's a road to hell.
  Not that it's so complicated, but it's probably unnecessary.
  Leave it to application servers.
- **[`Object.html#clone()`](http://docs.oracle.com/javase/7/docs/api/java/lang/Object.html#clone())** - honestly, I don't remember if I ever used that method in my entire (Java developer's) life.
  I just...
  didn't...
  And I can't find any rationale behind using it.
  I either have an explicit copy constructor or better use immutable objects.
  Do you have any legitimate use cases for it?
  It seems so 1990s...
- **native methods** - there are a few in JDK, even for such small tasks like [computing sine function](http://docs.oracle.com/javase/7/docs/api/java/lang/StrictMath.html#sin(double)).
  But Java is no longer the slowest kid in the class, it's actually quite the opposite.
  Also I can't imagine what kind of logic you need that can't be achieved using standard library or 3rd-party libraries.
  Finally, native methods are quite hard to get right, and you can expect low-level, nasty errors, especially around memory management.
- **custom collections** - implementing brand new collection following all contracts defined in original JavaDoc is [surprisingly hard](http://stackoverflow.com/questions/12761532).
  Frameworks like Hibernate use special persistent collections.
  Very rarely you need a collection so specific to your requirements that none of the built-in ones are good enough.
- **[`ThreadLocal`](http://docs.oracle.com/javase/7/docs/api/java/lang/ThreadLocal.html)** - Libraries and frameworks use thread locals quite often.
  But you should never try to exploit them for two unrelated reasons.
  First of all, `ThreadLocal` is often a hidden semi-global parameter you want to sneak-in.
  This makes your code harder to reason about and test.
  Secondly, `ThreadLocal`s can easily introduce memory leaks when not cleaned up properly (see [this](https://jira.mongodb.org/browse/JAVA-130), [this](http://stackoverflow.com/questions/5292349), [this](https://issues.apache.org/jira/browse/AXIS-935) and [this](http://jira.qos.ch/browse/LOGBACK-450) and...)
- **[WeakReference](http://docs.oracle.com/javase/7/docs/api/java/lang/ref/WeakReference.html) and [SoftReference](http://docs.oracle.com/javase/7/docs/api/java/lang/ref/SoftReference.html)** - these classes are quite low-level and are great when implementing caches playing well with garbage collection.
  Luckily there are plenty of open-source caching libraries, so you don't have to write one yourself.
  Understand what these classes do, but don't use them.
- **`com.sun.*` and `sun.*` packages, especially [`sun.misc.Unsafe`](http://www.docjar.com/docs/api/sun/misc/Unsafe.html)** - stay away from these packages, just...
  don't go there.
  There is no reason to explore these proprietary, undocumented and not guaranteed to preserve backward compatibility classes.
  Just pretend they're not there.
  And [why would you use `Unsafe`](http://stackoverflow.com/questions/5574241)?

------------------------------------------------------------------------

Of course the list above is completely subjective and most likely not definitive.
I encourage you to comment and suggest, if you feel some items are in wrong place or maybe something is missing entirely.
I would like to build a summary that can be given as a reference during code review or when a project is evaluated.
