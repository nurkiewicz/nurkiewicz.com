---
layout: post
title: 'Dependency injection: syntax sugar over function composition'
date: '2015-08-31T19:36:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- scala
- spring
- functional programming
- Haskell
modified_time: '2015-12-20T13:49:59.369+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8955559170984561270
blogger_orig_url: https://www.nurkiewicz.com/2015/08/dependency-injection-syntax-sugar-over.html
---

Quoting [Dependency Injection Demystified](http://www.jamesshore.com/Blog/Dependency-Injection-Demystified.html):

> "Dependency Injection" is a 25-dollar term for a 5-cent concept.

\*James Shore, 22 Mar, 2006

Dependency injection, as much as it is important when writing testable, composable and well-structured applications, means nothing more than having objects with constructors.
In this article I want to show you how dependency injection is basically just a syntax sugar that hides [function currying](https://en.wikipedia.org/wiki/Currying) and composition.
Don't worry, we'll go very slowly trying to explain why these two concepts are very much a like.

## Setters, annotations and constructors

Spring bean or EJB is a Java object.
However if you look closely most beans are actually stateless after creation.
Calling methods on Spring bean rarely modifies the state of that bean.
Most of the time beans are just convenient namespaces for a bunch of procedures working in similar context.
We don't modify the state of `CustomerService` when calling `invoice()`, we merely delegate to another object, which will eventually call database or web service.
This is already far from object-oriented programming (what I discussed [here](http://www.nurkiewicz.com/2009/10/ddd-in-spring-made-easy-with-aspectj.html)).
So essentially we have procedures (we'll get into functions later) in multi-level hierarchy of namespaces: packages and classes they belong to.
Typically these procedures call other procedures.
You might say they call methods on bean's dependencies, but we already learned that beans are a lie, these are just groups of procedures.

That being said let's see how you can configure beans.
In my career I had episodes with setters (and tons of `<property name="...">` in XML), `@Autowired` on fields and finally constructor injection.
See also: [Why injecting by constructor should be preffered?](http://pillopl.github.io/constructor-injection/).
So what we typically have is an object that has immutable references to its dependencies:

```java
@Component
class PaymentProcessor {

    private final Parser parser;
    private final Storage storage;

    @Autowired
    public PaymentProcessor(Parser parser, Storage storage) {
        this.parser = parser;
        this.storage = storage;
    }

    void importFile(Path statementFile) throws IOException {
            try(Stream lines = Files.lines(statementFile)) {
                lines
                        .map(parser::toPayment)
                        .forEach(storage::save);
            }
    }

}


@Component
class Parser {
    Payment toPayment(String line) {
        //om-nom-nom...
    }
}


@Component
class Storage {

    private final Database database;

    @Autowired
    public Storage(Database database) {
        this.database = database;
    }

    public UUID save(Payment payment) {
        return this.database.insert(payment);
    }
}


class Payment {
    //...
}
```

Take a file with bank statements, parse each individual line into `Payment` object and store it.
As boring as you can get.
Now let's refactor a little bit.
First of all I hope you are aware that object-oriented programming is a lie.
Not because it's just a bunch of procedures in namespaces so-called classes (I hope you are not writing software this way).
But because objects are implemented as procedures with implicit `this` parameter, when you see: `this.database.insert(payment)` it is actually compiled into something like this: `Database.insert(this.database, payment)`.
Don't believe me?

```bash
$ javap -c Storage.class 
...
  public java.util.UUID save(com.nurkiewicz.di.Payment);
    Code:
       0: aload_0
       1: getfield      #2                  // Field database:Lcom/nurkiewicz/di/Database;
       4: aload_1
       5: invokevirtual #3                  // Method com/nurkiewicz/di/Database.insert:(Lcom/nurkiewicz/di/Payment;)Ljava/util/UUID;
       8: areturn
```

OK, if you are normal, this is no proof for you, so let me explain.
`aload_0` (representing `this`) followed by `getfield #2` pushes `this.database` to operand stack.
`aload_1` pushes first method parameter (`Payment`) and finally `invokevirtual` calls *procedure* `Database.insert` (there is some polymorphism involved here, irrelevant in this context).
So we actually invoked two-parameter procedure, where first parameter was filled automatically by compiler and is named...
`this`.
On the callee side `this` is valid and points to `Database` instance.

# Forget about objects

Let's make all of this more explicit and forget about objects:

```java
class ImportDependencies {

    public final Parser parser;
    public final Storage storage;
    
    //...

}

static void importFile(ImportDependencies thiz, Path statementFile) throws IOException {
    Files.lines(statementFile)
            .map(thiz.parser::toPayment)
            .forEach(thiz.storage::save);
}
```

That's mad!
Notice that `importFile` *procedure* is now outside `PaymentProcessor`, which I actually renamed to `ImportDependencies` (pardon `public` modifier for fields).
`importFile` can be `static` because all dependencies are explicitly given in `thiz` container, not implicit using `this` and instance variables - and can be implemented anywhere.
Actually we just refactored to what already happens behind the scenes during compilation.
At this stage you might be wondering why we need an extra container for dependencies rather than just passing them directly.
Sure, it's pointless:

```java
static void importFile(Parser parser, Storage storage, Path statementFile) throws IOException {
    Files.lines(statementFile)
            .map(parser::toPayment)
            .forEach(storage::save);
}
```

Actually some people prefer passing dependencies explicitly to business methods like above, but that's not the point.
It's just another step in the transformation.

# Currying

For the next step we need to rewrite our function into Scala:

```java
object PaymentProcessor {

  def importFile(parser: Parser, storage: Storage, statementFile: Path) {
    val source = scala.io.Source.fromFile(statementFile.toFile)
    try {
      source.getLines()
        .map(parser.toPayment)
        .foreach(storage.save)
    } finally {
      source.close()
    }
  }

}
```

It's functionally equivalent, so not much to say.
Just notice how `importFile()` belongs to `object`, so it's somewhat similar to `static` methods on a singleton in Java.
Next we'll [group parameters](http://docs.scala-lang.org/tutorials/tour/currying.html):

```java
def importFile(parser: Parser, storage: Storage)(statementFile: Path) { //...
```

This makes all the difference.
Now you can either supply all dependencies all the time or better, do it just once:

```java
val importFileFun: (Path) => Unit = importFile(parser, storage)

//...

importFileFun(Paths.get("/some/path"))
```

Line above can actually be part of container setup, where we bind all dependencies together.
After setup we can use `importFileFun` anywhere, being clueless about other dependencies.
All we have is a function `(Path) => Unit`, just like `paymentProcessor.importFile(path)` in the very beginning.

# Functions all the way down

We still use objects as dependencies, but if you look carefully, we need neither `parser` nor `storage`.
What we really need is a *function*, that can parse (`parser.toPayment`) and a *function* that can store (`storage.save`).
Let's refactor again:

```java
def importFile(parserFun: String => Payment, storageFun: Payment => Unit)(statementFile: Path) {
  val source = scala.io.Source.fromFile(statementFile.toFile)
  try {
    source.getLines()
      .map(parserFun)
      .foreach(storageFun)
  } finally {
    source.close()
  }
}
```

Of course we can do the same with Java 8 and lambdas, but syntax is more verbose.
We can provide any function for parsing and storage, for example in tests we can easily create stubs.
Oh, and BTW, we just transformed from object-oriented Java to function composition and no objects at all.
Of course there are still side effects, e.g. loading file and storing, but let's leave it like that.
Or, to make similarity between dependency injection and function composition even more striking, check out equivalent program in Haskell:

```java
let parseFun :: String -> Payment
let storageFun :: Payment -> IO ()
let importFile :: (String -> Payment) -> (Payment -> IO ()) -> FilePath -> IO ()

let simpleImport = importFile parseFun storageFun
// :t simpleImport
// simpleImport :: FilePath -> IO ()
```

First of all `IO` monad is required to manage side effects.
But do you see how `importFile` higher order function takes three parameters, but we can supply just two and get `simpleImport`?
This is what we call dependency injection in Spring or EJB for that matter.
But without syntax sugar.

PS: [Webucator](https://www.webucator.com/java-training/index.cfm) did a [video based on this article](https://www.youtube.com/watch?v=he_9E0ayRws).
Thanks!
