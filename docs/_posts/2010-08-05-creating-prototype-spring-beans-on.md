---
layout: post
title: Creating prototype Spring beans on demand using lookup-method
date: '2010-08-05T23:44:00.006+02:00'
author: Tomasz Nurkiewicz
tags:
- spring
- intellij idea
- cglib
modified_time: '2011-03-30T19:04:36.893+02:00'
thumbnail: /assets/img/creating-prototype-spring-beans-on/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8577147422073830592
blogger_orig_url: https://www.nurkiewicz.com/2010/08/creating-prototype-spring-beans-on.html
---

The strength of the Spring Framework is its emphasis on stateless services.
Being totally against OOP, this approach has many pragmatic advantages, with low memory consumption, no cost of pooling and multithreaded safety at the top of the list.
But sometimes you really need the context and having non-singleton beans with different state attached to each instance makes your code a lot cleaner and easier to read.
Let’s start from stateless code and do some consecutive refactorings.

Every time a new flight is entered into the system, we validate it with multiple business rules using FlightValidator class (please forgive my complete absence of domain knowledge):

```java
public class FlightValidator {

@Resource
//Many services

public boolean validate(Flight flight) {
return validateSourceAndTarget(flight) &&
isAirplaneAvailable(flight) &&
isAirportFree(flight) &&
!buyerBlackListed(flight) &&
reservationLimitReached(flight);
}

//Many more methods

}
```

There is something really disturbing in this code.
The context (Flight instance being validated) is passed over and over through subsequent method invocations.
On the other hand, because the context exists on the stack (which is thread local in the contrary to the heap), the class is thread safe by its definition.
But still the code is so awkward that having flight field accessible to every method in the class (and sacrificing thread safety) is very tempting\*.
The easiest solution is to have a new, separate instance of FlightValidator every time we need to validate a flight.
So we create FlightValidator bean with prototype scope:

```xml
<bean id="flightValidator" class="com.blogspot.nurkiewicz.lookup.FlightValidator" scope="prototype" lazy-init="true"/>
```

Now, every time there is a need for flight validation, we should ask Spring to create a new instance of FlightValidator (imagine the class has multiple dependencies on other beans, has some aspects woven, etc. – we can’t simply use new operator).
The easiest way to do this is to implement [BeanFactoryAware](http://static.springsource.org/spring/docs/3.0.x/javadoc-api/org/springframework/beans/factory/BeanFactoryAware.html) and use injected [BeanFactory](http://static.springsource.org/spring/docs/3.0.x/javadoc-api/org/springframework/beans/factory/BeanFactory.html) to fetch any bean from the client code:

```java
public class SomeSpringBean implements BeanFactoryAware {
private BeanFactory beanFactory;

@Override
public void setBeanFactory(BeanFactory beanFactory) throws BeansException {
this.beanFactory = beanFactory;
}

//client code:
FlightValidator validator = beanFactory.getBean("flightValidator", FlightValidator.class);

}
```

Every time the code in line 10 is executed, new instance (prototype scope) of FlightValidator is created and returned.
Maybe the goal is achieved, but the solution is pretty cumbersome.
Not only we tie ourselves with the Spring API, but also we fetch bean by name (which is very verbose).
Last but not least, prior to Spring 3.0 the getBean() always returned Object instance, forcing client code to downcast the result.

I used this pattern several times, always being disgusted.
But then, by accident, I found [lookup-method](http://static.springsource.org/spring/docs/3.0.x/spring-framework-reference/html/beans.html#beans-factory-lookup-method-injection) feature in Spring docs.
BTW Spring documentation is a gift...
and a curse (like [detective Monk](http://www.imdb.com/title/tt0312172/quotes) used to say) - so exhaustive and comprehensive that it’s hard to read it and get to know with everything.
But back to Spring – the idea behind the lookup method is to drop BeanFactoryAware interface and simply create abstract no-arg method that returns bean of type we are willing to create (i.e.
FlightValidator).
Now the best part: we just tell Spring declaratively we want this abstract method to create FlightValidator instance every time it is called and Spring will implement this method at runtime (using [CGLIB](http://cglib.sourceforge.net/)) for us!
Just look how easy it is comparing to BeanFactory approach:

```java
public abstract class SomeSpringBean {

protected abstract FlightValidator createValidator();

//client code somewhere in the class:
FlightValidator validator = createValidator();
}
```

```xml
<bean id="flightValidator" class="com.blogspot.nurkiewicz.lookup.FlightValidator" scope="prototype" lazy-init="true"/>

<bean id="someBean" class="com.blogspot.nurkiewicz.lookup.SomeSpringBean">
<lookup-method name="createValidator" bean="flightValidator"/>
</bean>
```

The 4th line of Spring XML is essential.
We basically say: *hey, createValidator method is abstract and every time it is called, return new instance (using lookup-method and BeanFactory with singleton beans doesn’t make any sense) of bean named flightValidator*.
And Spring is clever enough to harness CGLIB and dynamically implement createValidator() method instead of trying to instantiate abstract class.
Pretty awesome!

This approach looks much nicer, does not involve the Spring API or force us to hardcode bean name in Java code.
Now, when we have a fresh new instance of FlightValidator, we can perform some refactorings to take advantage of class instance variables:

```java
private Flight flight;

public boolean validate(Flight flight) {
this.flight = flight;
return validateSourceAndTarget() &&
isAirplaneAvailable() &&
isAirportFree() &&
!buyerBlackListed() &&
reservationLimitReached();
}
```

First, we assign flight to a private field available for all validating methods.
Now, every method can access this field and there’s no need for passing arguments all over.
But sadly, it is just the beginning.
One day we had to make all validating methods publicly accessible in order to call them separately.
But now we need some way to initialize flight field and we certainly don’t want to go back to flight parameter in every method and flight field assignment at the beginning of each one.
There is another accidental disadvantage of our solution: if particular instance of FlightValidator leaks to some other thread, this thread can call validate() method with other Flight causing race condition.
If only we could make FlightValidator immutable by passing flight only once, binding FlightValidator permanently with this flight and being able to easily call every public validation method...

```java
private final Flight flight;

public FlightValidator(Flight flight) {
this.flight = flight;
}

public boolean validate() {
return validateSourceAndTarget() &&
isAirplaneAvailable() &&
isAirportFree() &&
!buyerBlackListed() &&
reservationLimitReached();
}
```

This is it!
Our Holy Object Oriented Grail!
Compiler forces us to pass valid flight instance (you may add validation to assert that) and after the FlightValidator is created, it will always reference the same flight.
API is simple, class is thread safe, everybody is happy...
Except our favorite framework...
According to the documentation, lookup method discussed above mustn’t have any arguments.
But suppose I don’t read the docs and simply add Flight parameter to lookup method and expect the magic to happen:

```java
protected abstract FlightValidator createValidator(Flight flight);
```

I thought to myself that Spring will transparently pass lookup method parameter(s) to the FlightValidator constructor matching its declaration – and we have just created such a constructor.
I run the application and it starts fine, but when I try to call lookup method I get:

```text
java.lang.AbstractMethodError: com.blogspot.nurkiewicz.lookup.SomeSpringBean.createValidator(Lcom/blogspot/nurkiewicz/lookup/Flight;)Lcom/blogspot/nurkiewicz/lookup/FlightValidator;
```

Seems like Spring ignored lookup method with arguments and simply didn’t implement it using CGLIB.
I would expect context startup to fail or at least warning that lookup won’t work (I even created [SPR-7426](https://jira.springframework.org/browse/SPR-7426)) but sadly only unit tests can prevent you from such a mistake.
And IntelliJ IDEA:

[![](/assets/img/creating-prototype-spring-beans-on/1.png)](/assets/img/creating-prototype-spring-beans-on/1.png)

We might work around this limitation and create some sort of init(Flight flight) method instead of constructor.
But what if we forget to call this method or call it twice?
Thread safety, immutability and consistency are lost...
Spring does not allow us to parameterize creation of prototype beans created by lookup method but come on, it’s open source and I am a programmer, I wouldn’t sleep at night if I at least didn’t try...

#### Patching Spring...

The stacktrace following [AbstractMethodError](http://download-llnw.oracle.com/javase/6/docs/api/java/lang/AbstractMethodError.html) didn’t help me but after turning on verbose Spring logging I immediately spotted [org.springframework.beans.factory.support.CglibSubclassingInstantiationStrategy](http://static.springsource.org/spring/docs/3.0.x/javadoc-api/org/springframework/beans/factory/support/CglibSubclassingInstantiationStrategy.html) class that is responsible for dynamic creation of abstract lookup method code and other features using CGLIB.
But first I had to discover why my parameterized lookup method is ignored by this mechanism.
After few minutes of studying I came across [org.springframework.beans.factory.support.LookupOverride](http://static.springsource.org/spring/docs/3.0.x/javadoc-api/org/springframework/beans/factory/support/LookupOverride.html) class with method:

```java
@Override
public boolean matches(Method method) {
return (method.getName().equals(getMethodName()) && method.getParameterTypes().length == 0);
}
```

So I changed too rigorous constraint and removed no arguments condition:

```java
@Override
public boolean matches(Method method) {
return method.getName().equals(getMethodName());
}
```

I quickly run my unit tests and now Spring generated code for my abstract lookup method (AbstractMethodError is gone) but still framework tries to instantiate FlightValidator bean using no-arg constructor, ignoring lookup method parameters.
First success, another challenge.

Half hour later I finally make out how CGLIB works and how Spring uses it.
I’ll skip CGLIB tutorial (maybe we’ll come back to this great library later), enough is to say that every time we call lookup abstract method, CGLIB synthesized class calls provided callback method, that for lookup method looks like this (excerpt from LookupOverrideMethodInterceptor inner class in org.springframework.beans.factory.support.CglibSubclassingInstantiationStrategy.CglibSubclassCreator):

```java
public Object intercept(Object obj, Method method, Object[] args, MethodProxy mp) throws Throwable {
LookupOverride lo = (LookupOverride) beanDefinition.getMethodOverrides().getOverride(method);
return owner.getBean(lo.getBeanName());
}
```

Third line is crucial.
We take bean name defined in Spring XML and fetch it from BeanFactory named owner.
But hey, what is that, args array argument?!?
And take a look at overloaded [getBean(String name, Object... args)](http://static.springsource.org/spring/docs/3.0.x/javadoc-api/org/springframework/beans/factory/BeanFactory.html#getBean%28java.lang.String,%20java.lang.Object...%29) method, ready to be used!
I’ll give it a try and see what happens:

```java
public Object intercept(Object obj, Method method, Object[] args, MethodProxy mp) throws Throwable {
LookupOverride lo = (LookupOverride) beanDefinition.getMethodOverrides().getOverride(method);
return owner.getBean(lo.getBeanName(), args);
}
```

Can you spot the difference?
I run unit tests and can’t believe my own eyes – it works!
It’s amazing, I only changed – not even added, changed!
– two lines of code and unlocked this great feature.
Now I can pass arbitrary set of parameters to the lookup method and they are going to be passed straight to the constructor of newly created object.
Finally the lookup method idea makes sense – create new, fully customized and initialized object every time you request it.
No need for further setup and danger of data inconsistency.
Long live the Spring Framework!

If you like this feature, I opened [SPR-7431](https://jira.springframework.org/browse/SPR-7431) ticket, watch it and vote for it.

\* one might argue that validate() should actually be a method of Flight and is an example of [Feature Envy](https://industriallogic.com/gh/submit?Action=PageAction&album=recognizingSmells&path=recognizingSmells/moreUncommonSmells/featureEnvyExample&devLanguage=Java) (see [Martin Fowlers](http://martinfowler.com/)’ [book](http://www.amazon.com/gp/product/0201485672?ie=UTF8&tag=javaandneighb-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=0201485672)) code smell.
I already [discussed](http://nurkiewicz.com/2009/10/ddd-in-spring-made-easy-with-aspectj.html) how to get rid of this smell using Spring
