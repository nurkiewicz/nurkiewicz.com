---
layout: post
title: Testing for exceptions in JUnit revised
date: '2010-09-25T21:13:00.004+02:00'
author: Tomasz Nurkiewicz
tags:
- testing
- aop
- design patterns
- tdd
- junit
modified_time: '2011-11-17T18:41:49.774+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-913626062211997442
blogger_orig_url: https://www.nurkiewicz.com/2010/09/testing-for-exceptions-in-junit-revised.html
---

In his recent [post](http://monkeyisland.pl/2010/07/26/expected-exception-in-tests) the author of fantastic mocking framework [Mockito](http://mockito.org/) collected few rules about testing exceptions.
What caught my attention is the advice to use JUnit rules (*nomen est omen*!)
for testing exceptions.
[ExpectedException](http://kentbeck.github.com/junit/javadoc/latest/org/junit/rules/ExpectedException.html) rule gathers advantages of both expected @Test attribute clarity and try-catch strictness.
Here is the example:

```java

public class DefaultFooServiceTest {

 private FooService fooService = new DefaultFooService();

 @Rule
 public ExpectedException exception = new ExpectedException();

 @Test
 public void shouldThrowNpeWhenNullName() throws Exception {
  //given
  String name = null;

  //when
  exception.expect(NullPointerException.class);
  fooService.echo(name);

  //then
 }

}
```

Szczepan claims that ExpectedException fits into *given/when/then* test template nicely.
I disagree!
Look at the code snippet above – what is the most natural place to put assertions on exception being thrown?
From the obvious reasons it must be the last line before the line that actually throws the exceptions.
So you have a choice to put assertion as the last statement in *given* block or as first in *when* block.
You are right, this is how this test should look like in an ideal world:

```java

@Test
public void shouldThrowNpeWhenNullName() throws Exception {
 //given
 String name = null;

 //when
 fooService.echo(name);

 //then
 exception.expect(NullPointerException.class);
}
```

No we’re talking!
There’s just this tiny problem with example above – we expect code in *when* block to throw an exception and put assertions afterwards in *then* block.
See the problem?
If we could somehow transparently catch the exception, store it somewhere, return normally and let assertions to run against it...
With AOP it is actually pretty easy, but I wanted to implement this feature using pure Java and with JUnit framework.
First, I will introduce @UnderTest marker annotation:

```java

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface UnderTest {
}
```

Now put this annotation above the field in your test case corresponding to class under test:

```java

@UnderTest
private FooService fooService = new DefaultFooService();
```

Although the annotation brings some value itself, marking which object is actually being tested, it is not meant for documentation and test readability, I am going to use it together with some Java reflection.
I mentioned that AOP would solve our problems.
JUnit 4.7 ships with AOP-like mechanism called [rules](http://kentbeck.github.com/junit/javadoc/latest/org/junit/rules/MethodRule.html).
By writing a rule (ExpectedException is an example of a JUnit built-in rule) you simply create an interceptor around every test method.
With this interceptor you can, for instance, run test method in separate thread, do some setup and cleanup, etc. My custom rule will do two things:

- wrap class under test in Java proxy to catch every exception, store it and return normally
- verify thrown exception against assertions introduced in *then* block

Skeleton of the rule code is as follows:

```java

package com.blogspot.nurkiewicz.junit.exceptionassert;

public class ExceptionAssert implements MethodRule {

 @Override
 public Statement apply(Statement base, FrameworkMethod method, Object testCase) {
  this.testCase = testCase;
  return new ExceptionAssertStatement(base);
 }

 private class ExceptionAssertStatement extends Statement {

  private final Statement base;

  private Throwable exceptionThrownFromClassUnderTest;
  private Field underTestField;

  public ExceptionAssertStatement(Statement base) {
   this.base = base;
   underTestField = findClassUnderTestField(testCase);
  }

  @Override
  public void evaluate() throws Throwable {
   final Object originalClassUnderTest = wrapClassUnderTest(testCase);
   try {
    base.evaluate();
   } finally {
    setUnderTestField(originalClassUnderTest);
   }
   verifyException();
  }

}
```

ExceptionAssertStatement is an example of [Decorator](http://en.wikipedia.org/wiki/Decorator_pattern) pattern: it takes original Statement instance (representing test method execution) and replaces it with wrapped (decorated) custom class, also implementing Statement.
ExceptionAssertStatement adds some additional logic and calls original’s statement evaluate() method.
This additional logic is pretty straightforward:

- first, take class under test and wrap it (wrapping again!)
  in a proxy
- execute the test method (evaluate())
- (revert to original class under test)
- when test method exits, verify exception throw from class under test (if any)

The last interesting piece is the proxy wrapping class under test itself:

```java

private Object wrapWithProxy(final Object classUnderTest) {
 return Proxy.newProxyInstance(classUnderTest.getClass().getClassLoader(), new Class[]{underTestField.getType()}, new InvocationHandler() {
  @Override
  public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
   try {
    return method.invoke(classUnderTest, args);
   } catch (InvocationTargetException e) {
    exceptionThrownFromClassUnderTest = e.getCause();
    return null;
   }
  }
 });
}
```

Nothing fancy: if class under test throws an exception, store it somewhere and return normally.
Not that hard.
Enough of the internals, let’s look at our brand new rule in action:

```java

public class DefaultFooServiceTest {

 @UnderTest
 private FooService fooService = new DefaultFooService();

 @Rule
 public ExceptionAssert exception = new ExceptionAssert();

 @Test
 public void shouldReturnHelloString() throws Exception {
  //given
  String name = "Tomek";

  //when
  final String result = fooService.echo(name);

  //then
  assertEquals("Hello, Tomek!", result);
 }

 @Test
 public void shouldThrowNpeWhenNullName() throws Exception {
  //given
  String name = null;

  //when
  fooService.echo(name);

  //then
  exception.expect(NullPointerException.class);
 }

 @Test
 public void shouldThrowIllegalArgumentWhenNameJohn() throws Exception {
  //given
  String name = "John";

  //when
  fooService.echo(name);

  //then
  exception.expect(IllegalArgumentException.class)
    .expectMessage("Name: 'John' is not allowed");
 }

}
```

First test method does not expect any exception to be thrown – it if will, test will fail.
Second test expects NullPointerException.
Please note that if the exception will be thrown from any other line than fooService.echo() (or fooService.echo() won’t throw NullPointerException), test will fail.
The last test shows that you can also assert exception message as well.

Few things are still missing in [0.0.1](http://github.com/nurkiewicz/junit-exception-assert-rule/downloads) "version", mainly proxying classes (CGLIB, anyone?); also, some syntactic sugar together with DSL-like ([FEST](http://code.google.com/p/fest)-like) assertions could be introduced:

```java

@Test
public void shouldThrowIllegalArgumentWhenNameJohn() throws Exception {
 //given
 String name = "John";

 //when
 fooService.echo(name);

 //then
 expect(IllegalArgumentException.class)
   .withMessage("Name: 'John' is not allowed");
}
```

Also I had to copy&paste big parts of JUnit’s ExpectedException, as most obvious inheritance was not possible due to private constructor.
But still, take a look at ExceptionAssert rule and see for yourself how readable exception testing can be.
As always, source code can be cloned and downloaded from my GitHub [account](http://github.com/nurkiewicz/junit-exception-assert-rule).
Any comments and contributions are welcome!
