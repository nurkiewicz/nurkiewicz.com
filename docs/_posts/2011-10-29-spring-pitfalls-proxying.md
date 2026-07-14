---
layout: post
title: 'Spring pitfalls: proxying'
date: '2011-10-29T11:10:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- transactions
- aop
- scala
- spring
modified_time: '2011-11-17T19:29:51.245+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-624144439922682448
blogger_orig_url: https://www.nurkiewicz.com/2011/10/spring-pitfalls-proxying.html
---

Being a Spring framework user and enthusiast for many years I came across several misunderstandings and problems with this stack.
Also there are places where abstractions leak terribly and to effectively and safely take advantage of all the features developers need to be aware of them.
That is why I am starting a *Spring pitfalls series*.
In the first part we will take a closer look at how proxying works.

Bean proxying is an essential and one of the most important infrastructure features provided by Spring.
It is so important and low-level that for most of the time we don't even realize that it exists.
However transactions, aspect-oriented programming, advanced scoping, [@Async](http://static.springsource.org/spring/docs/current/spring-framework-reference/html/scheduling.html#scheduling-annotation-support-async)support and various other domestic use-cases wouldn't be possible without it.
So what is [proxying](http://static.springsource.org/spring/docs/current/spring-framework-reference/html/aop.html#aop-proxying)?

Here is an example: when you inject DAO into service, Spring takes DAO instances and injects it directly.
That's it.
However sometimes Spring needs to be aware of each and every call made by service (and any other bean) to DAO.
For instance if DAO is marked transactional it needs to start a transaction before call and commit or rolls back afterwards.
Of course you can do this manually, but this is tedious, error-prone and mixes concerns.
That's why we use declarative transactions on the first place.

So how does Spring implement this interception mechanism?
There are three methods from simplest to most advanced ones.
I won't discuss their advantages and disadvantages yet, we will see them soon on a concrete examples.

#### Java dynamic proxies

Simplest solution.
If DAO implements any interface, Spring will create a Java [dynamic proxy](http://www.ibm.com/developerworks/java/library/j-jtp08305/index.html) implementing that interface(s) and inject it instead of the real class.
The *real* one still exists and the proxy has reference to it, but to the outside world – the proxy is the bean.
Now every time you call methods on your DAO, Spring can intercept them, add some AOP magic and call the original method.

#### CGLIB generated classes

The downside of Java dynamic proxies is a requirement on the bean to implement at least one interface.
CGLIB works around this limitation by dynamically subclassing the original bean and adding interception logic directly by overriding every possible method.
Think of it as subclassing the original class and calling super version amongst other things:

```scala

class DAO {
  def findBy(id: Int) = //...
}

class DAO$EnhancerByCGLIB extends DAO {
  override def findBy(id: Int) = {
    startTransaction
    try {
      val result = super.findBy(id)
      commitTransaction()
      result
    } catch {
      case e =>
        rollbackTransaction()
        throw e
    }
  }
}
```

However, this pseudocode does **not**illustrate how it works in reality – which introduces yet another problem, stay tuned.
BTW all examples will be in Scala, live with that and get used to it.

#### AspectJ weaving

This is the most invasive but also the most reliable and intuitive solution from the developer perspective.
In this mode interception is applied directly to your class bytecode which means the class your JVM runs is not the same as the one you wrote.
AspectJ weaver adds interception logic by directly modifying your bytecode of your class, either during build – *compile time weaving*(*CTW*) or when loading a class – *load time weaving*(*LTW*).

If you are curious how AspectJ magic is implemented under the hood, here is a decompiled and simplified .class file compiled with AspectJ weaving beforehand:

```java

public void inInterfaceTransactional()
{
  try
  {
    AnnotationTransactionAspect.aspectOf().ajc$before$1$2a73e96c(this, ajc$tjp_2);
    throwIfNotInTransaction();
  }
  catch(Throwable throwable)
  {
    AnnotationTransactionAspect.aspectOf().ajc$afterThrowing$2$2a73e96c(this, throwable);
    throw throwable;
  }
  AnnotationTransactionAspect.aspectOf().ajc$afterReturning$3$2a73e96c(this);
}
```

With load time weaving the same transformation occurs at runtime, when the class is loaded.
As you can see there is nothing disturbing here, in fact this is exactly how you would program the transactions manually.
Side note: do you remember the times when viruses were appending their code into executable files or dynamically injecting themselves when executable was loaded by the operating system?

Knowing proxy techniques is important to understand how proxying works and how it affects your code.
Let us stick with declarative transaction demarcation example, here is our battlefield:

```scala

trait FooService {
  def inInterfaceTransactional()
  def inInterfaceNotTransactional();
}

@Service
class DefaultFooService extends FooService {

  private def throwIfNotInTransaction() {
    assume(TransactionSynchronizationManager.isActualTransactionActive)
  }

  def publicNotInInterfaceAndNotTransactional() {
    inInterfaceTransactional()
    publicNotInInterfaceButTransactional()
    privateMethod();
  }

  @Transactional
  def publicNotInInterfaceButTransactional() {
    throwIfNotInTransaction()
  }

  @Transactional
  private def privateMethod() {
    throwIfNotInTransaction()
  }

  @Transactional
  override def inInterfaceTransactional() {
    throwIfNotInTransaction()
  }

  override def inInterfaceNotTransactional() {
    inInterfaceTransactional()
    publicNotInInterfaceButTransactional()
    privateMethod();
  }
}
```

Handy throwIfNotInTransaction() method...
throws exception when not invoked within a transaction.
Who would have thought?
This method is called from various places and different configurations.
If you examine carefully how methods are invoked – this should all work.
However our developers' life tend to be brutal.
First obstacle was unexpected: [ScalaTest](http://scalatest.org/) does not support Spring integration [testing](http://static.springsource.org/spring/docs/current/spring-framework-reference/html/testing.html)via dedicated runner.
Luckily this can be easily ported with a simple trait (handles dependency injection to test cases and application context caching):

```scala

trait SpringRule extends AbstractSuite { this: Suite =>

  abstract override def run(testName: Option[String], reporter: Reporter, stopper: Stopper, filter: Filter, configMap: Map[String, Any], distributor: Option[Distributor], tracker: Tracker) {
    new TestContextManager(this.getClass).prepareTestInstance(this)
    super.run(testName, reporter, stopper, filter, configMap, distributor, tracker)
  }

}
```

Note that we are not starting and rolling back transactions like the [original](http://static.springsource.org/spring/docs/current/spring-framework-reference/html/testing.html#testing-tx)testing framework.
Not only because it would interfere with our demo but also because I find transactional tests harmful – but more on that in the future.
Back to our example, here is a smoke test.
The complete source code can be downloaded [here](https://github.com/nurkiewicz/spring-pitfalls)from [proxy-problem](https://github.com/nurkiewicz/spring-pitfalls/tree/proxy-problem)branch.
Don't complain about the lack of assertions – here we are only testing that exceptions are not thrown:

```scala

@RunWith(classOf[JUnitRunner])
@ContextConfiguration
class DefaultFooServiceTest extends FunSuite with ShouldMatchers with SpringRule{

  @Resource
  private val fooService: FooService = null

  test("calling method from interface should apply transactional aspect") {
    fooService.inInterfaceTransactional()
  }

  test("calling non-transactional method from interface should start transaction for all called methods") {
    fooService.inInterfaceNotTransactional()
  }

}
```

Surprisingly, the test fails.
Well, if you've been reading my articles for a while you shouldn't be surprised: [Spring AOP riddle](http://nurkiewicz.com/2009/08/spring-aop-riddle.html) and [Spring AOP riddle demystified](http://nurkiewicz.com/2009/09/spring-aop-riddle-demystified.html).
Actually, the Spring reference documentation explains this in [great detail](http://static.springsource.org/spring/docs/current/spring-framework-reference/html/aop.html#aop-understanding-aop-proxies), also check out [this](http://stackoverflow.com/questions/3037006)SO question.
In short – non transactional method calls transactional one but **bypassing** the transactional proxy.
Even though it seems obvious that when inInterfaceNotTransactional() calls inInterfaceTransactional() the transaction should start – it does not.
The abstraction leaks.
By the way also check out fascinating [Transaction strategies: Understanding transaction pitfalls](http://www.ibm.com/developerworks/java/library/j-ts1/index.html) article for more.

Remember our example showing how CGLIB works?
Also knowing how polymorphism works it seems like using class based proxies should help.
inInterfaceNotTransactional() now calls inInterfaceTransactional()overriden by CGLIB/Spring, which in turns calls the original classes.
**Not a chance!**
This is the real implementation in pseudo-code:

```scala

class DAO$EnhancerByCGLIB extends DAO {

  val target: DAO = ...

  override def findBy(id: Int) = {
    startTransaction
    try {
      val result = target.findBy(id)
      commitTransaction()
      result
    } catch {
      case e =>
        rollbackTransaction()
        throw e
    }
  }
}
```

Instead of subclassing and instantiating subclassed bean Spring first creates the original bean and then creates a subclass which wraps the original one (somewhat [Decorator](http://en.wikipedia.org/wiki/Decorator_pattern)pattern) in one of the post processors.
This means that – again – the self call inside bean bypasses AOP proxy around our class.
Of course using CGLIB changes how are bean behaves in few other ways.
For instance we can now inject concrete class rather than an interface, in fact the interface is not even needed and CGLIB proxying is required in this circumstances.
There are also drawbacks – constructor injection is no longer possible, see [SPR-3150](https://jira.springsource.org/browse/SPR-3150), which is a [shame](http://nurkiewicz.com/2011/09/evolution-of-spring-dependency.html).
So what about some more thorough tests?

```scala

@RunWith(classOf[JUnitRunner])
@ContextConfiguration
class DefaultFooServiceTest extends FunSuite with ShouldMatchers with SpringRule {

  @Resource
  private val fooService: DefaultFooService = null

  test("calling method from interface should apply transactional aspect") {
    fooService.inInterfaceTransactional()
  }

  test("calling non-transactional method from interface should start transaction for all called methods") {
    fooService.inInterfaceNotTransactional()
  }

  test("calling transactional method not belonging to interface should start transaction for all called methods") {
    fooService.publicNotInInterfaceButTransactional()
  }

  test("calling non-transactional method not belonging to interface should start transaction for all called methods") {
    fooService.publicNotInInterfaceAndNotTransactional()
  }

}
```

Please pick tests that will fail (pick exactly two).
Can you explain why?
Again common sense would suggest that everything should pass, but that's not the case.
You can play around yourself, see [class-based-proxy](https://github.com/nurkiewicz/spring-pitfalls/tree/class-based-proxy)branch.

We are not here to expose problems but to overcome them.
Unfortunately our tangled service class can only be fixed using heavy artillery – true AspectJ weaving.
Both compile- and load-time weaving makes the test pass.
See [aspectj-ctw](https://github.com/nurkiewicz/spring-pitfalls/tree/aspectj-ctw)and [aspectj-ltw](https://github.com/nurkiewicz/spring-pitfalls/tree/aspectj-ltw)branches accordingly.

You should now be asking yourself several question.
*Which approach should I take*(or: *do I really need to use AspectJ?*) and *why should I even bother?*
– amongst others.
I would say – in most cases simple Spring proxying will suffice.
But you absolutely have to be aware of how does the propagation work and when it doesn't.
Otherwise bad things happen.
Commits and rollbacks occurring in unexpected places, spanning unexpected amount of data, ORM [dirty checking](http://stackoverflow.com/questions/82429) not working, invisible records – believe, this things happen on wild.
And remember that topics we have covered here apply to all AOP aspects, not only transactions.
