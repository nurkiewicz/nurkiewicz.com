---
layout: post
title: Spring AOP riddle
date: '2009-08-16T19:38:00.005+02:00'
author: Tomasz Nurkiewicz
tags:
- ejb
- aop
- spring
modified_time: '2009-09-20T17:12:21.951+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4947172745143790821
blogger_orig_url: https://www.nurkiewicz.com/2009/08/spring-aop-riddle.html
---

Spring support for aspect oriented programming is [very
wide](http://static.springsource.org/spring/docs/2.5.x/reference/aop.html),
but sometimes you may shoot yourself in the foot if you are not careful
enough. Consider the following service interface:

```java
public interface FoobarService {

 void foo();

 void bar();

}
```


...and its implementation:

```java
public class DefaultFoobarService implements FoobarService {

 @Override
 @Transactional
 public void foo() {
   //some code requiring active transaction
 }

 @Override
 public void bar() {
   foo();
 }
}
```


To keep things simple, assume that
`foo()` throws exception if not run in
context of active transaction. Since
`main()` is so old-school, we're going
to test both methods through test case:

```java
@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration
public class DefaultFoobarServiceTest {

 @Autowired
 private FoobarService foobarService;

 @Test
 public void testFoo() {
   foobarService.foo();
 }

 @Test
 public void testBar() {
   foobarService.bar();
 }
}
```

Assuming `testFoo()` succeeded, will
`testBar()` succeed as well? The trick
p
t is transaction propagation...
...
The problem with `bar()` method is
that it is not marked as transactional, but since it calls transactional
method `foo()`, you may expect that
`foo()` is called within a
transaction... but it's not! And since
`foo()` called from
`bar()` isn't wrapped in a
transaction, `foo()` will throw a
exception and the test will fail.
To explain this odd behavior, you must first understand how aspects
(including declarative transactions) are applied to Spring beans. When
we mark any of beans' methods with
[\@Transactional](http://static.springsource.org/spring/docs/2.5.x/api/org/springframework/transaction/annotation/Transactional.html)
annotation, Spring automatically wraps the bean in Java dynamic proxy.
This proxy intercepts all method calls from other beans and if it
encounters method marked as transactional, it performs special,
transaction related routines (linking to existing or creating new
transaction, rolling back on exception, etc.) Of course, the advice
calls original method of wrapped object during its execution (like
`foo()`). So as long as you are
running foo(), Spring handles transactions transparently and smoothly.
But think what happens when you call
`bar()` method. Method is not marked
as transactional, so even though transactional proxy will intercept the
call, it will soon discover that method does not require transaction and
simply delegate to original method
`bar()`. Then the method invokes
`foo()`. This is the place, where we
expect the transaction to be started, but wait! -- we are invoking
`foo()` method on this reference,
which points directly to the bean, not transactional aspect proxy.
Spring does not know anything about this call, since you are calling
method on Java object (POJO), not on a proxy instance wrapping this
object. Declarative transaction management won't be applied and
`foo()` will throw unexpected
exception.
The answer is pretty obvious if you understand the mechanics of Spring
AOP, because the same problem will occur in any code using aspects, not
only transactions and not only via annotations. In fact, also the same
problem has been solved in EJB by using
[SessionContext.getBusinessObject()](http://java.sun.com/javaee/5/docs/api/javax/ejb/SessionContext.html#getBusinessObject%28java.lang.Class%29)
method -- passing this is forbidden by the specification. In Spring, the
easiest way to avoid this particular bug in our code is to simply
a
otate `bar()` method as well.
* If our bean does not implement any business interface, CGLIB will be
used instead. Also, you must use `<tx:annotation-driven />` to make this
magic happen.

## UPDATE:

* More details: [Spring AOP riddle demystified](http://nurkiewicz.com/2009/09/spring-aop-riddle-demystified.html)
