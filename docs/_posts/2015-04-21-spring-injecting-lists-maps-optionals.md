---
layout: post
title: 'Spring: injecting lists, maps, optionals and getBeansOfType() pitfalls'
date: '2015-04-21T00:07:00.001+02:00'
author: Tomasz Nurkiewicz
tags:
- spring
modified_time: '2015-04-21T00:16:42.146+02:00'
thumbnail: /assets/img/spring-injecting-lists-maps-optionals/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2217182590205295943
blogger_orig_url: https://www.nurkiewicz.com/2015/04/spring-injecting-lists-maps-optionals.html
---

If you use Spring framework for more than a week you are probably aware of this feature.
Suppose you have more than one bean implementing a given interface.
Trying to autowire just one bean of such interface is doomed to fail because Spring has no idea which particular instance you need.
You can work around that by using `@Primary` annotation to designate exactly one "*most important*" implementation that will have priority over others.
But there are many legitimate use cases where you want to inject **all** beans implementing said interface.
For example you have multiple validators that all need to be executed prior to business logic or several algorithm implementations that you want to exercise at the same time.
Auto-discovering all implementations at runtime is a fantastic illustration of [*Open/closed principle*](http://en.wikipedia.org/wiki/Open/closed_principle): you can easily add new behavior to business logic (validators, algorithms, strategies - *open* for extension) without touching the business logic itself (*closed* for modification).

Just in case I will start with a quick introduction, feel free to jump straight to subsequent sections.
So let's take a concrete example.
Imagine you have a `StringCallable` interface and multiple implementations:

```java
interface StringCallable extends Callable<String> { }

@Component
class Third implements StringCallable {
    @Override
    public String call() {
        return "3";
    }

}

@Component
class Forth implements StringCallable {
    @Override
    public String call() {
        return "4";
    }

}

@Component
class Fifth implements StringCallable {
    @Override
    public String call() throws Exception {
        return "5";
    }
}
```

Now we can inject `List<StringCallable>`, `Set<StringCallable>` or even `Map<String, StringCallable>` (`String` represents bean name) to any other class.
To simplify I'm injecting to a test case:

```java
@SpringBootApplication public class Bootstrap { }

@ContextConfiguration(classes = Bootstrap)
class BootstrapTest extends Specification {

    @Autowired
    List<StringCallable> list;

    @Autowired
    Set<StringCallable> set;

    @Autowired
    Map<String, StringCallable> map;

    def 'injecting all instances of StringCallable'() {
        expect:
            list.size() == 3
            set.size() == 3
            map.keySet() == ['third', 'forth', 'fifth'].toSet()
    }

    def 'enforcing order of injected beans in List'() {
        when:
            def result = list.collect { it.call() }
        then:
            result == ['3', '4', '5']
    }

    def 'enforcing order of injected beans in Set'() {
        when:
            def result = set.collect { it.call() }
        then:
            result == ['3', '4', '5']
    }

    def 'enforcing order of injected beans in Map'() {
        when:
            def result = map.values().collect { it.call() }
        then:
            result == ['3', '4', '5']
    }

}
```

So far so good, but only first test passes, can you guess why?

```text
Condition not satisfied:

result == ['3', '4', '5']
|      |
|      false
[3, 5, 4]
```

After all, why did we make an assumption that beans will be injected in the same order as they were...
declared?
Alphabetically?
Luckily one can enforce the order with [`Ordered`](http://docs.spring.io/spring/docs/current/javadoc-api/org/springframework/core/Ordered.html) interface:

```java
interface StringCallable extends Callable<String>, Ordered {
}

@Component
class Third implements StringCallable {
    //...

    @Override public int getOrder() {
        return Ordered.HIGHEST_PRECEDENCE;
    }
}

@Component
class Forth implements StringCallable {
    //...

    @Override public int getOrder() {
        return Ordered.HIGHEST_PRECEDENCE + 1;
    }
}

@Component
class Fifth implements StringCallable {
    //...

    @Override public int getOrder() {
        return Ordered.HIGHEST_PRECEDENCE + 2;
    }
}
```

Interestingly, even though Spring internally injects `LinkedHashMap` and `LinkedHashSet`, only `List` is properly ordered.
I guess it's not documented and least surprising.
To end this introduction, in Java 8 you can also inject `Optional<MyService>` which works as expected: injects a dependency only if it's available.
Optional dependencies can appear e.g. when using profiles extensively and some beans are not bootstrapped in some profiles.

# [Composite pattern](http://en.wikipedia.org/wiki/Composite_pattern)

Dealing with lists is quite cumbersome.
Most of the time you want to iterate over them so in order to avoid duplication it's useful to encapsulate such list in a dedicated wrapper:

```java
@Component
public class Caller {

    private final List<StringCallable> callables;

    @Autowired
    public Caller(List<StringCallable> callables) {
        this.callables = callables;
    }

    public String doWork() {
        return callables.stream()
                .map(StringCallable::call)
                .collect(joining("|"));
    }

}
```

Our wrapper simply calls all underlying callables one after another and joins their results:

```java
@ContextConfiguration(classes = Bootstrap)
class CallerTest extends Specification {

    @Autowired
    Caller caller

    def 'Caller should invoke all StringCallbles'() {
        when:
            def result = caller.doWork()
        then:
            result == '3|4|5'
    }

}
```

It's somewhat controversial, but often this wrapper implements the same interface as well, effectively implementing *composite* classic design pattern:

```java
@Component
@Primary
public class Caller implements StringCallable {

    private final List<StringCallable> callables;

    @Autowired
    public Caller(List<StringCallable> callables) {
        this.callables = callables;
    }

    @Override
    public String call() {
        return callables.stream()
                .map(StringCallable::call)
                .collect(joining("|"));
    }

}
```

Thanks to `@Primary` we can simply autowire `StringCallable` everywhere as if there was just one bean while in fact there are multiple and we inject composite.
This is useful when refactoring old application as it preserves backward compatibility.

Why am I even starting with all these basics?
If you look very closely, code snippet above introduces chicken and egg problem: an instance of `StringCallable` requires all instances of `StringCallable`, so technically speaking `callables` list should include `Caller` as well.
But `Caller` is currently being created, so it's impossible.
This makes a lot of sense and luckily Spring recognizes this special case.
But in more advanced scenarios this can bite you.
Further down the road a new developer introduced *this*:

```java
@Component
public class EnterpriseyManagerFactoryProxyHelperDispatcher {

    private final Caller caller;

    @Autowired
    public EnterpriseyManagerFactoryProxyHelperDispatcher(Caller caller) {
        this.caller = caller;
    }
}
```

Nothing wrong so far, except the class name.
But what happens if one of the `StringCallables` has a dependency on it?

```java
@Component
class Fifth implements StringCallable {

    private final EnterpriseyManagerFactoryProxyHelperDispatcher dispatcher;

    @Autowired
    public Fifth(EnterpriseyManagerFactoryProxyHelperDispatcher dispatcher) {
        this.dispatcher = dispatcher;
    }

}
```

We now created a circular dependency, and because we inject via constructors (as it was always meant to be), Spring slaps us in the face on startup:

```text
UnsatisfiedDependencyException:
    Error creating bean with name 'caller' defined in file ...
UnsatisfiedDependencyException: 
    Error creating bean with name 'fifth' defined in file ...
UnsatisfiedDependencyException: 
    Error creating bean with name 'enterpriseyManagerFactoryProxyHelperDispatcher' defined in file ...
BeanCurrentlyInCreationException: 
    Error creating bean with name 'caller': Requested bean is currently in creation: 
        Is there an unresolvable circular reference?
```

Stay with me, I'm building the climax here.
This is clearly a bug, that can unfortunately be fixed with field injection (or setter for that matter):

```java
@Component
public class Caller {

    @Autowired
    private List<StringCallable> callables;

    public String doWork() {
        return callables.stream()
                .map(StringCallable::call)
                .collect(joining("|"));
    }

}
```

By decoupling bean creation from injection (impossible with constructor injection) we can now create a circular dependency graph, where `Caller` holds an instance of `Fifth` class which references `Enterprisey...`, which in turns references back to the same `Caller` instance.
Cycles in dependency graph are a design smell, leading to unmaintainable graph of spaghetti relationships.
Please avoid them and if constructor injection can entirely prevent them, that's even better.

# Meeting `getBeansOfType()`

Interestingly there is another solution that goes straight to Spring guts: [`ListableBeanFactory.getBeansOfType()`](http://docs.spring.io/spring/docs/current/javadoc-api/org/springframework/beans/factory/ListableBeanFactory.html#getBeansOfType-java.lang.Class-):

```java
@Component
public class Caller {

    private final List<StringCallable> callables;

    @Autowired
    public Caller(ListableBeanFactory beanFactory) {
        callables = new ArrayList<>(beanFactory.getBeansOfType(StringCallable.class).values());
    }

    public String doWork() {
        return callables.stream()
                .map(StringCallable::call)
                .collect(joining("|"));
    }

}
```

[![](/assets/img/spring-injecting-lists-maps-optionals/1.png)](/assets/img/spring-injecting-lists-maps-optionals/1.png)

Problem solved?
Quite the opposite!
`getBeansOfType()` will silently skip (well, there is `TRACE` and `DEBUG` log...)
beans under creation and only returns those already existing.
Therefor `Caller` was just created and container started successfully, while it no longer references `Fifth` bean.
You might say I asked for it because we have a circular dependency so weird things happens.
But it's an inherent feature of `getBeansOfType()`.
In order to understand why **using `getBeansOfType()` during container startup is a bad idea**, have a look at the following scenario (unimportant code omitted):

```java
@Component
class Alpha {

    static { log.info("Class loaded"); }

    @Autowired
    public Alpha(ListableBeanFactory beanFactory) {
        log.info("Constructor");
        log.info("Constructor (beta?):  {}", beanFactory.getBeansOfType(Beta.class).keySet());
        log.info("Constructor (gamma?): {}", beanFactory.getBeansOfType(Gamma.class).keySet());
    }

    @PostConstruct
    public void init() {
        log.info("@PostConstruct (beta?):  {}", beanFactory.getBeansOfType(Beta.class).keySet());
        log.info("@PostConstruct (gamma?): {}", beanFactory.getBeansOfType(Gamma.class).keySet());
    }

}

@Component
class Beta {

    static { log.info("Class loaded"); }

    @Autowired
    public Beta(ListableBeanFactory beanFactory) {
        log.info("Constructor");
        log.info("Constructor (alpha?): {}", beanFactory.getBeansOfType(Alpha.class).keySet());
        log.info("Constructor (gamma?): {}", beanFactory.getBeansOfType(Gamma.class).keySet());
    }

    @PostConstruct
    public void init() {
        log.info("@PostConstruct (alpha?): {}", beanFactory.getBeansOfType(Alpha.class).keySet());
        log.info("@PostConstruct (gamma?): {}", beanFactory.getBeansOfType(Gamma.class).keySet());
    }

}

@Component
class Gamma {

    static { log.info("Class loaded"); }

    public Gamma() {
        log.info("Constructor");
    }

    @PostConstruct
    public void init() {
        log.info("@PostConstruct");
    }
}
```

The log output reveals how Spring internally loads and resolves classes:

```text
Alpha: | Class loaded
Alpha: | Constructor
Beta:  | Class loaded
Beta:  | Constructor
Beta:  | Constructor (alpha?): []
Gamma: | Class loaded
Gamma: | Constructor
Gamma: | @PostConstruct
Beta:  | Constructor (gamma?): [gamma]
Beta:  | @PostConstruct (alpha?): []
Beta:  | @PostConstruct (gamma?): [gamma]
Alpha: | Constructor (beta?):  [beta]
Alpha: | Constructor (gamma?): [gamma]
Alpha: | @PostConstruct (beta?):  [beta]
Alpha: | @PostConstruct (gamma?): [gamma]
```

Spring framework first loads `Alpha` and tries to instantiate a bean.
However when running `getBeansOfType(Beta.class)` it discovers `Beta` so proceeds with loading and instantiating that one.
Inside `Beta` we can immediately spot the problem: when `Beta` asks for `beanFactory.getBeansOfType(Alpha.class)` it gets no results (`[]`).
Spring will silently ignore `Alpha`, because it's currently under creation.
Later everything is as expected: `Gamma` is loaded, constructed and injected, `Beta` sees `Gamma` and when we return to `Alpha`, everything is in place.
Notice that even moving `getBeansOfType()` to `@PostConstruct` method doesn't help - these callbacks aren't executed in the end, when all beans are instantiated - but while the container starts up.

# Suggestions

`getBeansOfType()` is rarely needed and turns out to be unpredictable if you have cyclic dependencies.
Of course you should avoid them in the first place and if you properly inject dependencies via collections, Spring can predictably handle the lifecycle of all beans and either wire them correctly or fail at runtime.
In presence of circular dependencies betweens beans (sometimes accidental or very long in terms of nodes and edges in dependency graph) `getBeansOfType()` can yield different results depending on factors we have no control over, like CLASSPATH order.

PS: Kudos to [Jakub Kubryński](http://www.kubrynski.com/) for troubleshooting `getBeansOfType()`.
