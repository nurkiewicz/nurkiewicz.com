---
layout: post
title: DDD in Spring made easy with AspectJ
date: '2009-10-07T00:03:00.003+02:00'
author: Tomasz Nurkiewicz
tags:
- aop
- spring
- ddd
- aspectj
- maven
modified_time: '2013-04-07T13:23:57.668+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3593673006013287599
blogger_orig_url: https://www.nurkiewicz.com/2009/10/ddd-in-spring-made-easy-with-aspectj.html
---

> UPDATE: Over the years I learnt that the solution provided below is not really an example of domain-driven design.
> It's more like an [*active record*](http://en.wikipedia.org/wiki/Active_record) implementation on top of Spring.
> But the technical part of the article is still relevant, so I keep it intact.

Before I start the main topic, I would like you to think for a while about the best JEE application design you can imagine.
No matter you use Spring or EJB3, as they are very similar, probably you would suggest similar approach.
Starting from the back you have:

- domain objects, which are simple POJOs mapped directly to database relations.
  POJOs are great because JavaBean-style properties are well understood be many frameworks.
-  data access layer – typically stateless services, which wrap up database access code (JDBC, Hibernate, JPA, iBatis or whatever you want) hiding its complexity and providing some level of (leaky) abstraction.
  DAOs are great because they hide nasty and awkward JDBC logic (that is why some question the need for DAOs when using JPA, but this is out of scope of this post), serving as a, more-or-less, translator between database and objects.
- business services layer – another set of stateless services, which operate on domain objects.
  Typical design introduces a graph of objects that take or return domain objects and perform some logic on them, again, typically accessing database via data access layer.
  Service layer is great because it focuses on business logic, delegating technical details to DAO layer.
- user interface – nowadays, typically via web browser.
  User interface is great because...
  just the fact it is.

Beautiful, isn’t it?
Now open your eyes, it is time for a cold shower.

Both services and DAOs are stateless, because Spring and EJB3 favors such classes - so we learnt to live with it.
On the other hand, POJOs are "logicless" – they only contain data, maintain their state without operating on it and introducing no logic.
If we think about introducing "reservation" domain object to our application, we immediately think of Reservation POJOs mapped to RESERVATIONS database table, ReservationDao, ReservationService, ReservationController, etc.

Still don’t see the problem, Java, thus OOP programmer?
How would you describe "object"?
It is some virtual being having internal (encapsulation) state and some public operations, which have explicit access to the state.
Most fundamental concept of object-based programming is to take data and procedures operating on that data together and close them tightly.
Now take a look at your best design ever, do you really need objects?
This is the dark secret of Spring, EJB3, Hibernate and other well established frameworks.
The secret, which all of us subconsciously try to forget: we are not OOP programmers anymore!

POJOs are not objects, they are simply data structures, collections of data.
Getters and setters are not true methods, actually, when was the last time you wrote them by hand?
In fact, the need to autogenerate them (and refactor, add and remove when attributes change) sometimes happen to be very frustrating.
Wouldn’t it be simpler just to use structures with public fields by default?

On the other hand, look at all those great stateless services.
They do not have any state.
Although they operate on domain objects, they are not part of them or not even aggregate them (low cohesion).
All the data is passed explicitly through the method parameters.
They aren’t objects as well – they are simply collection of procedures arbitrary gathered together on a common namespace, corresponding to class name.
In contracts, methods in OOP are also procedures behind the scenes, but having implicit access to this reference, which points to the object instance.
Whenever we call ReservationService or ReservationDao providing Reservation POJO reference explicitly as one of the arguments, we actually reinvent OOP and code it manually.

Let’s face it, we are not OOP programmers, as everything we need are structures and procedures, invented fifty years ago...
How many Java programmers are using inheritance and polymorphism in a day-to-day basis?
When was the last time you wrote object having private state without getters/setters with only few method having access to it?
When was the last time you created object with non-default constructor?

Luckily, what Spring have taken, it brings back with even more power.
The power is called AspcetJ.

In my [last post](http://nurkiewicz.com/2009/09/state-pattern-introducing-domain-driven.html) I created Reservation entity having three business methods: accept(), charge() and cancel().
It looks really good to have business methods concerning domain object placed directly in that object.
Instead of calling reservationService.accept(reservation), we simply run reservation.accept(), which is much more intuitive and less noisy.
Even better, what about writing:

```java
Reservation res = new Reservation()
//...
res.persist()
```

instead of calling DAO or EntityManager directly?
I don’t know much about domain-driven design, but I found this fundamental refactoring to be the first gate you must walk through to enter the DDD world (and go back to OOP as well).

So, if having business methods directly on domain objects is so great, why not everybody’s doing it?
The answer is very straightforward and down-to-earth – because they don’t know how!
Reservations’ accept() method will eventually need to delegate some logic to external services, like accounting or sending e-mails.
Naturally, this logic is not part of Reservation domain object and should be implemented elsewhere (high cohesion).
But most Spring programmers don’t know how or are scared of injecting other services to domain objects.
When all services are managed by Spring, everything is simple.
But when Hibernate creates domain objects itself or the object is created using new operator, Spring has no knowledge of this instance and cannot handle dependency injection.
So how would Reservation POJO obtain Spring beans or EntityManager encapsulating necessary logic?

...

First, add [@Configurable](http://static.springsource.org/spring/docs/2.5.x/api/org/springframework/beans/factory/annotation/Configurable.html) annotation to your domain object:

```java
@Configurable
@Entity
public class Reservation implements Serializable {
  //...
}
```

This tells Spring that Reservation POJO should be managed by Spring.
But, as mentioned above, Spring has no knowledge of Reservation instances being created, so it has no occasion to autowire and inject dependencies.
This is where AspectJ comes in.
All you need to do is to add:

```xml
<context:load-time-weaver/>
```

To your Spring XML descriptor.
This extremely short XML snippet tells Spring that it should use AspectJ load-time weaving (LTW).
Now, when you run you application:

java.lang.IllegalStateException: ClassLoader \[org.apache.catalina.loader.WebappClassLoader\] does NOT provide an 'addTransformer(ClassFileTransformer)' method.
Specify a custom LoadTimeWeaver or start your Java virtual machine with Spring's agent: -javaagent:spring-agent.jar
at org.springframework.context.weaving.DefaultContextLoadTimeWeaver.setBeanClassLoader(DefaultContextLoadTimeWeaver.java:82)
at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.initializeBean(AbstractAutowireCapableBeanFactory.java:1322)
at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.doCreateBean(AbstractAutowireCapableBeanFactory.java:473)
...
59 more

It will fail...
Java is not magic, so before we proceed, few words of explanation – don’t be impatient.
Adding XML snippet above does not solve anything.
It simply tells Spring that we are using AspectJ LTW.
But when application starts up, it does not find AspectJ and tells us about it decently.
What happens if we add -javaagent:spring-agent.jar to our JVM command line parameters as suggested?
This Java agent is simply a plugin to JVM that overrides loading of every class.
When Reservation class is loaded for the first time, agent discovers @Configurable annotation and applies some special AspectJ aspect to this class.

To be more precise: bytecode of Reservation class is being modified, overriding all constructors and deserialization routines.
Thanks to this modification, whenever new Reservation class is being instantiated, apart from normal initialization, those additional routines added by the Spring-provided aspect perform dependency injection.
So since now enhanced Reservation class is Spring-aware.
It does not matter whether reservation has been created by Hibernate, Struts2 or using new operator.
Hidden aspect code always takes care of calling Spring ApplicationContext and ask it to inject all dependencies to domain object.
Let us take it for a test drive:

```java
@Configurable
@Entity
public class Reservation implements Serializable {

  @PersistenceContext
  private transient EntityManager em;

  @Transactional
  public void persist() {
      em.persist(this);
  }
//...
}
```

This is not a mistake – I injected EntityManger from JPA specification directly to domain object.
I also put @Transactional annotation over persist() method.
This is not possible in ordinary Spring, but since we used @Configurable annotation and AspectJ LTW, code below is completely valid and works as expected, issuing SQL and committing transaction against the database:

```java
Reservation res = new Reservation()
//...
res.persist()
```

Of course, you can also inject regular dependencies (other Spring beans) to your domain objects.
You have choice of using autowiring ([@Autowire](http://static.springsource.org/spring/docs/2.5.x/api/org/springframework/beans/factory/annotation/Autowired.html) or even better [@Resource](http://java.sun.com/javaee/5/docs/api/javax/annotation/Resource.html) annotations) or setting properties manually.
The latter approach gives you more control, but forces you to add setter for Spring bean in domain object and define another bean corresponding to domain object:

```xml
<bean class=" com.blogspot.nurkiewicz.reservations.Reservation ">
  <!-- ... -->
</bean>
```

Please note that I haven’t provided name/id for this bean.
If I would, the same name should be passed to @Configurable annotation.

Everything works like a charms, but how to use this amazing feature in your real life work?
First of all, you must setup your unit tests to use Java agent.
In IntelliJ IDEA I simply added:

-javaagent:D:/my/maven/repository/org/springframework/spring-agent/2.5.6/spring-agent-2.5.6.jar

to VM parameters text field in JUnit run configuration.
If you add this to default ("Edit defaults" button), this parameter will be applied to every new unit test you run.
But configuring IDE is not as much important as configuring your build tool (hopefully maven).
First of all you must ensure that Spring Java agent is downloaded and available.
Thanks to maven dependency resolution, this can be easily achieved by adding dependency:

```xml
<dependency>
      <groupId>org.springframework</groupId>
      <artifactId>spring-agent</artifactId>
      <version>2.5.6</version>
      <scope>test</scope>
</dependency>
```

The JAR is not actually needed by test code, but by adding this dependency we guarantee that it is downloaded before tests run.
Then, simple tweak in surefire plugin configuration:

```xml
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-surefire-plugin</artifactId>
  <configuration>
      <forkMode>always</forkMode>
      <argLine>
          -javaagent:${settings.localRepository}/org/springframework/spring-agent/2.5.6/spring-agent-2.5.6.jar
      </argLine>
  </configuration>
</plugin>
```

Really simple – location of spring-agent.jar can be safely constructed using maven repository path.
Also forkMode must be set in order to reload classes (and cause LTW to happen) each test is executed.
I think configuring your app server and/or startup scripts does not need any further explanation.

That is all about Spring and AspectJ integration via load-time weaving.
Few simple configuration steps and a whole new world of domain-driven design welcomes.
Our domain model is no longer weak, entities are "smart" and business code is more intuitive.
And last but not least – your code would be back object-oriented, not procedural.

Of course, you might not like load-time weaving, as it interferes with JVM class loading.
There is another approach, called compile-time weaving, which weaves aspects on compile time rather than class loading time.
Both methods have pros and cons, I will try to compare both of them in the future.
