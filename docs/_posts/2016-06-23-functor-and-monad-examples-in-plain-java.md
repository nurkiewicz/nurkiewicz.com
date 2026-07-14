---
layout: post
title: Functor and monad examples in plain Java
date: '2016-06-23T23:06:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- functor
- monad
- functional programming
- rxjava
modified_time: '2017-04-28T09:58:24.078+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2187061199898399594
blogger_orig_url: https://www.nurkiewicz.com/2016/06/functor-and-monad-examples-in-plain-java.html
---

This article was initially an appendix in our [Reactive Programming with RxJava](http://amzn.to/28NV8eJ) book.
However introduction to monads, albeit very much related to reactive programming, didn't suit very well.
So I decided to take it out and publish separately as a blog post.
I am aware that "*my very own, half correct and half complete explanation of monads*" is the new "*Hello, world*" on programming blogs.
Yet the article looks at functors and monads from a specific angle of Java data structures and libraries.
Thus I thought it's worthwhile sharing.

RxJava was designed and built on top of very fundamental concepts like *functors* , *monoids* and *monads* .
Even though Rx was modeled initially for imperative C# language and we are learning about RxJava, working on top of similarly imperative language, the library has its roots in functional programming.
You should not be surprised after you realize how compact RxJava API is.
There are pretty much just a handful of core classes, typically immutable, and everything is composed using mostly pure functions.

With a recent rise of functional programming (or functional style), most commonly expressed in modern languages like Scala or Clojure, monads became a widely discussed topic.
There is a lot of folklore around them:

A monad is a monoid in the category of endofunctors, what's the problem?
[*James Iry*](http://james-iry.blogspot.com/2009/05/brief-incomplete-and-mostly-wrong.html)

The curse of the monad is that once you get the epiphany, once you understand - "oh that's what it is" - you lose the ability to explain it to anybody.
[*Douglas Crockford*](https://www.youtube.com/watch?v=dkZFtimgAcM)

The vast majority of programmers, especially those without functional programming background, tend to believe monads are some arcane computer science concept, so theoretical that it can not possibly help in their programming career.
This negative perspective can be attributed to dozens of articles and blog posts being either too abstract or too narrow.
But it turns out that monads are all around us, even is standard Java library, especially since Java Development Kit (JDK) 8 (more on that later).
What is absolutely brilliant is that once you understand monads for the first time, suddenly several unrelated classes and abstractions, serving entirely different purposes, become familiar.

Monads generalize various seemingly independent concepts so that learning yet another incarnation of monad takes very little time.
For example you do not have to learn how `CompletableFuture` works in Java 8, once you realize it is a monad, you know precisely how it works and what can you expect from its semantics.
And then you hear about RxJava which sounds so much different but because `Observable` is a monad, there is not much to add.
There are numerous other examples of monads you already came across without knowing that.
Therefore this section will be a useful refresher even if you fail to actually use RxJava.

# Functors

Before we explain what a monad is, let's explore simpler construct called a *functor* .
A functor is a typed data structure that encapsulates some value(s).
From syntactic perspective a functor is a container with the following API:

```java
import java.util.function.Function;

interface Functor<T> {
    
    <R> Functor<R> map(Function<T, R> f);
    
}
```

But mere syntax is not enough to understand what functor is.
The only operation that functor provides is `map()` that takes a function `f`.
This function receives whatever is inside a box, transforms it and wraps the result as-is into a second functor.
Please read that carefully.
`Functor<T>` is always an immutable container, thus `map` never mutates original object it was executed on.
Instead it returns the result (or results - be patient) wrapped in a brand new functor, possibly of different type `R`.
Additionally functors should not perform any actions when identity function is applied, that is `map(x -> x)`.
Such a pattern should always return either the same functor or an equal instance.

Often `Functor<T>` is compared to a box holding instance of `T` where the only way of interacting with this value is by transforming it.
However there is no idiomatic way of unwrapping or escaping from the functor.
The value(s) always stay within the context of functor.
Why are functors useful?
They generalize multiple common idioms like collections, promises, optionals, etc. with a single, uniform API that works across all of them.
Let me introduce a couple of functors to make you more fluent with this API:

```java
interface Functor<T,F extends Functor<?,?>> {
    <R> F map(Function<T,R> f);
}

class Identity<T> implements Functor<T,Identity<?>> {

    private final T value;

    Identity(T value) { this.value = value; }

    public <R> Identity<R> map(Function<T,R> f) {
        final R result = f.apply(value);
        return new Identity<>(result);
    }
    
}
```

An extra `F` type parameter was required to make `Identity` compile.
What you saw in the preceding example was the simplest functor just holding a value.
All you can do with that value is transforming it inside `map` method, but there is no way to extract it.
This is considered beyond the scope of pure functor.
The only way to interact with functor is by applying sequences of type-safe transformations:

```java
Identity<String> idString = new Identity<>("abc");
Identity<Integer> idInt = idString.map(String::length);
```

Or fluently, just like you compose functions:

```java
Identity<byte[]> idBytes = new Identity<>(customer)
        .map(Customer::getAddress)
        .map(Address::street)
        .map((String s) -> s.substring(0, 3))
        .map(String::toLowerCase)
        .map(String::getBytes);
```

From this perspective mapping over a functor is not much different than just invoking chained functions:

```java
byte[] bytes = customer
        .getAddress()
        .street()
        .substring(0, 3)
        .toLowerCase()
        .getBytes();
```

Why would you even bother with such verbose wrapping that not only does not provide any added value, but also is not capable of extracting the contents back?
Well, it turns out you can model several other concepts using this raw functor abstraction.
For example `java.util.Optional<T>` starting from Java 8 is a functor with `map()` method.
Let us implement it from scratch:

```java
class FOptional<T> implements Functor<T,FOptional<?>> {

    private final T valueOrNull;

    private FOptional(T valueOrNull) {
        this.valueOrNull = valueOrNull;
    }

    public <R> FOptional<R> map(Function<T,R> f) {
        if (valueOrNull == null)
            return empty();
        else
            return of(f.apply(valueOrNull));
    }

    public static <T> FOptional<T> of(T a) {
        return new FOptional<T>(a);
    }

    public static <T> FOptional<T> empty() {
        return new FOptional<T>(null);
    }

}
```

Now it becomes interesting.
An `FOptional<T>` functor *may* hold a value, but just as well it might be empty.
It's a type-safe way of encoding `null`.
There are two ways of constructing `FOptional` - by supplying a value or creating `empty()` instance.
In both cases, just like with `Identity`, `FOptional` is immutable and we can only interact with the value from inside.
What differs `FOptional` is that the transformation function `f` may not be applied to any value if it is empty.
This means functor may not necessarily encapsulate exactly one value of type `T`.
It can just as well wrap arbitrary number of values, just like `List`...
functor:

```java
import com.google.common.collect.ImmutableList;

class FList<T> implements Functor<T, FList<?>> {

    private final ImmutableList<T> list;

    FList(Iterable<T> value) {
        this.list = ImmutableList.copyOf(value);
    }

    @Override
    public <R> FList<?> map(Function<T, R> f) {
        ArrayList<R> result = new ArrayList<R>(list.size());
        for (T t : list) {
            result.add(f.apply(t));
        }
        return new FList<>(result);
    }
}
```

The API remains the same: you take a functor in a transformation `T -> R` - but the behavior is much different.
Now we apply a transformation on each and every item in the `FList`, declaratively transforming whole list.
So if you have a list of `customers` and you want a list of their streets, it's as simple as:

```java
import static java.util.Arrays.asList;

FList<Customer> customers = new FList<>(asList(cust1, cust2));

FList<String> streets = customers
        .map(Customer::getAddress)
        .map(Address::street);
```

It's no longer as simple as saying `customers.getAddress().street()`, you can't invoke `getAddress()` on a collection of customers, you must invoke `getAddress()` on each individual customer and then place it back in a collection.
By the way Groovy found this pattern so common that it actually has a syntax sugar for that: `customer*.getAddress()*.street()`.
This operator, known as spread-dot, is actually a `map` in disguise.
Maybe you are wondering why I iterate over `list` manually inside `map` rather than using `Stream`s from Java 8: `list.stream().map(f).collect(toList())`?
Does this ring a bell?
What if I told you `java.util.stream.Stream<T>` in Java is a functor as well?
And by the way, also a monad?

Now you should see the first benefits of functors - they abstract away the internal representation and provide consistent, easy to use API over various data structures.
As the last example let me introduce *promise* functor, similar to `Future`.
`Promise` "promises" that a value will become available one day.
It is not yet there, maybe because some background computation was spawned or we are waiting for external event.
But it will appear some time in the future.
The mechanics of completing a `Promise<T>` are not interesting, but the functor nature is:

```java
Promise<Customer> customer = //...
Promise<byte[]> bytes = customer
        .map(Customer::getAddress)
        .map(Address::street)
        .map((String s) -> s.substring(0, 3))
        .map(String::toLowerCase)
        .map(String::getBytes);
```

Looks familiar?
That is the point!
The implementation of `Promise` functor is beyond the scope of this article and not even important.
Enough to say that we are very close to implementing `CompletableFuture` from Java 8 and we almost discovered `Observable` from RxJava.
But back to functors.
`Promise<Customer>` does not hold a value of `Customer` just yet.
It promises to have such value in the future.
But we can still map over such functor, just like we did with `FOptional` and `FList` - the syntax and semantics are exactly the same.
The behavior follows what the functor represents.
Invoking `customer.map(Customer::getAddress)` yields `Promise<Address>` which means `map` is non-blocking.
`customer.map()` will *not* wait for the underlying `customer` promise to complete.
Instead it returns another promise, of different type.
When upstream promise completes, downstream promise applies a function passed to `map()` and passes the result downstream.
Suddenly our functor allows us to pipeline asynchronous computations in a non-blocking manner.
But you do not have to understand or learn that - because `Promise` is a functor, it must follow syntax and laws.

There are many other great examples of functors, for example representing value or error in a compositional manner.
But it is high time to look at monads.

# From functors to monads

I assume you understand how functors work and why are they a useful abstraction.
But functors are not that universal as one might expect.
What happens if your transformation function (the one passed as an argument to `map()`) returns functor instance rather than simple value?
Well, functor is just a value as well, so nothing bad happens.
Whatever was returned is placed back in a functor so all behaves consistently.
However imagine you have this handy method for parsing `String`s:

```java
FOptional<Integer> tryParse(String s) {
    try {
        final int i = Integer.parseInt(s);
        return FOptional.of(i);
    } catch (NumberFormatException e) {
        return FOptional.empty();
    }
}
```

Exceptions are side-effects that undermine type system and functional purity.
In pure functional languages there is no place for exceptions, after all we never heard about throwing exceptions during math classes, right?
Errors and illegal conditions are represented explicitly using values and wrappers.
For example `tryParse()` takes a `String` but does not simply return an `int` or silently throw an exception at runtime.
We explicitly tell, through the type system, that `tryParse()` can fail, there is nothing exceptional or erroneous in having a malformed string.
This semi-failure is represented by optional result.
Interestingly Java has checked exceptions, the ones that must be declared and handled, so in some sense Java is purer in that regard, it does not hide side-effects.
But for better or worse checked exceptions are often discouraged in Java, so let's get back to `tryParse()`.
It seems useful to compose `tryParse` with `String` already wrapped in `FOptional`:

```java
FOptional<String> str = FOptional.of("42");
FOptional<FOptional<Integer>> num = str.map(this::tryParse);
```

That should not come as a surprise.
If `tryParse()` would return an `int` you would get `FOptional<Integer> num`, but because `map()` function returns `FOptional<Integer>` itself, it gets wrapped twice into awkward `FOptional<FOptional<Integer>>`.
Please look carefully at the types, you must understand why we got this double wrapper here.
Apart from looking horrible, having a functor in functor ruins composition and fluent chaining:

```java
FOptional<Integer> num1 = //...
FOptional<FOptional<Integer>> num2 = //...

FOptional<Date> date1 = num1.map(t -> new Date(t));

//doesn't compile!
FOptional<Date> date2 = num2.map(t -> new Date(t));
```

Here we try to map over the contents of `FOptional` by turning `int` into +Date+.
Having a function of `int -> Date` we can easily transform from `Functor<Integer>` to `Functor<Date>`, we know how it works.
But in case of `num2` situation becomes complicated.
What `num2.map()` receives as input is no longer an `int` but an `FOoption<Integer>` and obviously `java.util.Date` does not have such a constructor.
We broke our functor by double wrapping it.
However having a function that returns a functor rather than simple value is so common (like `tryParse()`) that we can not simply ignore such requirement.
One approach is to introduce a special parameterless `join()` method that "flattens" nested functors:

```java
FOptional<Integer> num3 = num2.join()
```

It works but because this pattern is so common, special method named `flatMap()` was introduced.
`flatMap()` is very similar to `map` but expects the function received as an argument to return a functor - or *monad* to be precise:

```java
interface Monad<T,M extends Monad<?,?>> extends Functor<T,M> {
    M flatMap(Function<T,M> f);
}
```

We simply concluded that `flatMap` is just a syntactic sugar to allow better composition.
But `flatMap` method (often called `bind` or `>>=` from Haskell) makes all the difference since it allows complex transformations to be composed in a pure, functional style.
If `FOptional` was an instance of monad, parsing suddenly works as expected:

```java
FOptional<String> num = FOptional.of("42");
FOptional<Integer> answer = num.flatMap(this::tryParse);
```

Monads do not need to implement `map`, it can be implemented on top of `flatMap()` easily.
As a matter of fact `flatMap` is the essential operator that enables a whole new universe of transformations.
Obviously just like with functors, syntactic compliance is not enough to call some class a monad, the `flatMap()` operator has to follow monad laws, but they are fairly intuitive like associativity of `flatMap()` and identity.
The latter requires that `m(x).flatMap(f)` is the same as `f(x)` for any monad holding a value `x` and any function `f`.
We are not going to dive too deep into monad theory, instead let's focus on practical implications.
Monads shine when their internal structure is not trivial, for example `Promise` monad that will hold a value in the future.
Can you guess from the type system how `Promise` will behave in the following program?
First all methods that can potentially take some time to complete return a `Promise`:

```java
import java.time.DayOfWeek;


Promise<Customer> loadCustomer(int id) {
    //...
}

Promise<Basket> readBasket(Customer customer) {
    //...
}

Promise<BigDecimal> calculateDiscount(Basket basket, DayOfWeek dow) {
    //...
}
```

We can now compose these functions as if they were all blocking using monadic operators:

```java
Promise<BigDecimal> discount = 
    loadCustomer(42)
        .flatMap(this::readBasket)
        .flatMap(b -> calculateDiscount(b, DayOfWeek.FRIDAY));
```

This becomes interesting.
`flatMap()` must preserve monadic type therefor all intermediate objects are `Promise`s.
It is not just about keeping the types in order - preceding program is suddenly fully asynchronous!
`loadCustomer()` returns a `Promise` so it does not block.
`readBasket()` takes whatever the `Promise` has (will have) and applies a function returning another `Promise` and so on and so forth.
Basically we built an asynchronous pipeline of computation where the completion of one step in background automatically triggers next step.

# Exploring `flatMap()`

It is very common to have two monads and combining the value they enclose together.
However both functors and monads do not allow direct access to their internals, which would be impure.
Instead we must carefully apply transformation without escaping the monad.
Imagine you have two monads and you want to combine them:

```java
import java.time.LocalDate;
import java.time.Month;


Monad<Month> month = //...
Monad<Integer> dayOfMonth = //...

Monad<LocalDate> date = month.flatMap((Month m) ->
        dayOfMonth
                .map((int d) -> LocalDate.of(2016, m, d)));
```

Please take your time to study the preceding pseudo-code.
I don't use any real monad implementation like `Promise` or `List` to emphasize the core concept.
We have two independent monads, one of type `Month` and the other of type `Integer`.
In order to build `LocalDate` out of them we must build a nested transformation that has access to the internals of both monads.
Work through the types, especially making sure you understand why we use `flatMap` in one place and `map()` in the other.
Think how you would structure this code if you had a third `Monad<Year>` as well.
This pattern of applying a function of two arguments (`m` and `d` in our case) is so common that in Haskell there is special helper function called `liftM2` that does exactly this transformation, implemented on top of `map` and `flatMap`.
In Java pseudo-syntax it would look somewhat like this:

```java
Monad<R> liftM2(Monad<T1> t1, Monad<T2> t2, BiFunction<T1, T2, R> fun) {
    return t1.flatMap((T1 tv1) ->
            t2.map((T2 tv2) -> fun.apply(tv1, tv2))
    );
}
```

You don't have to implement this method for every monad, `flatMap()` is enough, moreover it works consistently for all monads.
`liftM2` is extremely useful when you consider how it can be used with various monads.
For example `liftM2(list1, list2, function)` will apply `function` on every possible pair of items from `list1` and `list2` (Cartesian product).
On the other hand for optionals it will apply a function only when both optionals are non-empty.
Even better, for `Promise` monad a function will be executed asynchronously when both `Promise`s are completed.
This means we just invented a simple synchronization mechanism (`join()` in fork-join algorithms) of two asynchronous steps.

Another useful operator that we can easily build on top of `flatMap()` is `filter(Predicate<T>)` which takes whatever is inside a monad and discards it entirely if it does not meet certain predicate.
In a way it is similar to `map` but rather than 1-to-1 mapping we have 1-to-0-or-1.
Again `filter()` has the same semantics for every monad but quite amazing functionality depending on which monad we actually use.
Obviously it allows filtering out certain elements from a list:

```java
FList<Customer> vips = 
    customers.filter(c -> c.totalOrders > 1_000);
```

But it works just as well e.g. for optionals.
In that case we can transform non-empty optional into an empty one if the contents of optional does not meet some criteria.
Empty optionals are left intact.

# From list of monads to monad of list

Another useful operator that originates from `flatMap()` is `sequence()`.
You can easily guess what it does simply by looking at type signature:

```java
Monad<Iterable<T>> sequence(Iterable<Monad<T>> monads)
```

Often we have a bunch of monads of the same type and we want to have a single monad of a list of that type.
This might sounds abstract to you, but it is impressively useful.
Imagine you wanted to load a few customers from the database concurrently by ID so you used `loadCustomer(id)` method several times for different IDs, each invocation returning `Promise<Customer>`.
Now you have a list of `Promise`s but what you really want is a list of customers, e.g. to be displayed in the web browser.
`sequence()` (in RxJava `sequence()` is called `concat()` or `merge()`, depending on use-case) operator is built just for that:

```java
FList<Promise<Customer>> custPromises = FList
    .of(1, 2, 3)
    .map(database::loadCustomer);

Promise<FList<Customer>> customers = custPromises.sequence();

customers.map((FList<Customer> c) -> ...);
```

Having an `FList<Integer>` representing customer IDs we `map` over it (do you see how it helps that `FList` is a functor?)
by calling `database.loadCustomer(id)` for each ID.
This leads to rather inconvenient list of `Promise`s.
`sequence()` saves the day, but once again this is not just a syntactic sugar.
Preceding code is fully non-blocking.
For different kinds of monads `sequence()` still makes sense, but in a different computational context.
For example it can change a `FList<FOptional<T>>` into `FOptional<FList<T>>`.
And by the way, you can implement `sequence()` (just like `map()`) on top of `flatMap()`.

This is just the tip of the iceberg when it comes to usefulness of `flatMap()` and monads in general.
Despite coming from rather obscure category theory, monads proved to be extremely useful abstraction even in object-oriented programming languages such as Java.
Being able to compose functions returning monads is so universally helpful that dozens of unrelated classes follow monadic behavior.

Moreover once you encapsulate data inside monad, it is often hard to get it out explicitly.
Such operation is not part of the monad behavior and often leads to non-idiomatic code.
For example `Promise.get()` on `Promise<T>` can technically return `T`, but only by blocking, whereas all operators based on `flatMap()` are non-blocking.
Another example is `FOptional.get()` that can fail because `FOptional` may be empty.
Even `FList.get(idx)` that peeks particular element from a list sounds awkward because you can replace `for` loops with `map()` quite often.

I hope you now understand why monads are so popular these days.
Even in object-oriented(-ish) language like Java they are quite useful abstraction.
