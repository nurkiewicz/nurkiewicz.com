---
layout: post
title: Proxies done right with Guava's AbstractInvocationHandler
date: '2013-12-23T18:50:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- guava
- multithreading
- design patterns
modified_time: '2013-12-23T18:53:15.901+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3034681858777650450
blogger_orig_url: https://www.nurkiewicz.com/2013/12/proxies-done-right-with-guavas.html
image:
  path: /assets/img/proxies-done-right-with-guavas/hero.jpg
  alt: "Snarøya"
---

Not too often but sometimes we are forced to write custom [dynamic proxy class](http://docs.oracle.com/javase/1.5.0/docs/guide/reflection/proxy.html) using [`java.lang.reflect.Proxy`](http://docs.oracle.com/javase/7/docs/api/java/lang/reflect/Proxy.html).
There is really no magic in this mechanism and it's worth knowing even you will never really use it - because Java proxies are ubiquitous in various frameworks and libraries.

The idea is quite simple: dynamically create an object that implements one or more interfaces but every time any method of these interfaces is called our custom callback handler is invoked.
This handler receives a handle to a method that was called ([`java.lang.reflect.Method`](http://docs.oracle.com/javase/7/docs/api/java/lang/reflect/Method.html) instance) and is free to behave in any way.
Proxies are often used to implement seamless mocking, caching, transactions, security - i.e. they are a foundation for AOP.

Before I explain what the purpose of [`com.google.common.reflect.AbstractInvocationHandler`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/reflect/AbstractInvocationHandler.html) from the title, let's start from a simple example.
Say we want to transparently run methods of given interface asynchronously in a thread pool.
Popular stacks like Spring (see: [`27.4.3 The @Async Annotation`](http://docs.spring.io/spring/docs/current/spring-framework-reference/html/scheduling.html#scheduling-annotation-support-async)) and Java EE (see: [`Asynchronous Method Invocation`](http://docs.oracle.com/javaee/6/tutorial/doc/gkkqg.html)) already support this using the same technique.

Imagine we have the following service:

```java
public interface MailServer {
    void send(String msg);
    int unreadCount();
}
```

Our goal is to run `send()` asynchronously so that several subsequent invocations are not blocking but queue up and are executed in external thread pool concurrently rather than in calling thread.
First we need factory code that will create a proxy instance:

```java
public class  AsyncProxy {
    public static <T> T wrap(T underlying, ExecutorService pool) {
        final ClassLoader classLoader = underlying.getClass().getClassLoader();
        final Class<T> intf = (Class<T>) underlying.getClass().getInterfaces()[0];
        return (T)Proxy.newProxyInstance(
            classLoader, 
            new Class<?>[] {intf}, 
            new AsyncHandler<T>(underlying, pool));
    }
}
```

Code above makes few bold assumptions, for example that an `underlying` object (real instance that we are proxying) implements exactly one interface.
In real life a class can of course implement multiple interfaces, so can proxies - but we simplify this a bit for educational purposes.
Now for starters we shall create no-op proxy that delegates to underlying object without any added value:

```java
class AsyncHandler<T> implements InvocationHandler {

    private static final Logger log = LoggerFactory.getLogger(AsyncHandler.class);

    private final T underlying;
    private final ExecutorService pool;

    AsyncHandler1(T underlying, ExecutorService pool) {
        this.underlying = underlying;
        this.pool = pool;
    }

    @Override
    public Object invoke(Object proxy, final Method method, final Object[] args) throws Throwable {
        return method.invoke(underlying, args);
    }

}
```

`ExecutorService pool` will be used later.
The last line is crucial - we invoke `method` on `underlying` instance with the same `args`.
At this point we can:

- invoke `underlying` or not (e.g.
  if given call is cached/memoized)
- change arguments (i.e.
  for security purposes)
- run code before/after/around/on exception
- alter result by returning different value (it must match the type of `method.getReturnType()`)
- ...and much more

In our case we will wrap `method.invoke()` with `Callable` and run it asynchronously:

```java
class AsyncHandler<T> implements InvocationHandler {

    private final T underlying;
    private final ExecutorService pool;

    AsyncHandler(T underlying, ExecutorService pool) {
        this.underlying = underlying;
        this.pool = pool;
    }

    @Override
    public Object invoke(Object proxy, final Method method, final Object[] args) throws Throwable {
        final Future<Object> future = pool.submit(new Callable<Object>() {
            @Override
            public Object call() throws Exception {
                return method.invoke(underlying, args);
            }
        });
        return handleResult(method, future);
    }

    private Object handleResult(Method method, Future<Object> future) throws Throwable {
        if (method.getReturnType() == void.class)
            return null;
        try {
            return future.get();
        } catch (ExecutionException e) {
            throw e.getCause();
        }
    }
}
```

Extra `handleResult()` method was extracted in order to properly handle non-`void` methods.
Using such a proxy is straightforward:

```java
final MailServer mailServer = new RealMailServer();

final ExecutorService pool = Executors.newFixedThreadPool(10);
final MailServer asyncMailServer = AsyncProxy.wrap(mailServer, pool);
```

Now even if `RealMailServer.send()` takes a second to complete, invoking it twice via `asyncMailServer.send()` takes no time because both invocations run asynchronously in background.

## Broken `equals()`, `hashCode()` and `toString()`

Some developers are not aware of potential issues with default `InvocationHandler` implementation.
Quoting the [official documentation](http://docs.oracle.com/javase/1.5.0/docs/guide/reflection/proxy.html):

> An invocation of the `hashCode`, `equals`, or `toString` methods declared in `java.lang.Object` on a proxy instance will be encoded and dispatched to the invocation handler's `invoke` method in the same manner as interface method invocations are encoded and dispatched, as described above.

In our case case this means that for example `toString()` is executed in the same thread pool as other methods of `MailServer`, quite surprising.
Now imagine you have a local proxy where every method invocation triggers remote call.
Dispatching `equals()`, `hashCode()` and `toString()` via network is definitely not what we want.

## Fixing with `AbstractInvocationHandler`

[`AbstractInvocationHandler`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/reflect/AbstractInvocationHandler.html) from Guava is a simple abstract class that correctly deals with issues above.
By default it dispatches `equals()`, `hashCode()` and `toString()` to `Object` class rather than passing it to invocation handler.
Refactoring from straight `InvocationHandler` to `AbstractInvocationHandler` is dead simple:

```java
import com.google.common.reflect.AbstractInvocationHandler;

class AsyncHandler<T> extends AbstractInvocationHandler {

    //...

    @Override
    protected Object handleInvocation(Object proxy, final Method method, final Object[] args) throws Throwable {
        //...
    }

    @Override
    public String toString() {
        return "Proxy of " + underlying;
    }
}
```

That's it!
I decided to override `toString()` to help debugging.
`equals()` and `hashCode()` are inherited from `Object` which is fine for the beginning.
Now please look around your code base and search for custom proxies.
If you were not using `AbstractInvocationHandler` or similar so far, chances are you introduces few subtle bugs.
