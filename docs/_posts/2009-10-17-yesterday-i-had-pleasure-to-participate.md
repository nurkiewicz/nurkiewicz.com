---
layout: post
title: Compile- vs load-time weaving performance in Spring
date: '2009-10-17T19:57:00.007+02:00'
author: Tomasz Nurkiewicz
tags:
- conferences
- aop
- spring
- aspectj
modified_time: '2009-10-18T11:00:14.535+02:00'
thumbnail: /assets/img/yesterday-i-had-pleasure-to-participate/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-824546586682370291
blogger_orig_url: https://www.nurkiewicz.com/2009/10/yesterday-i-had-pleasure-to-participate.html
---

Yesterday I had pleasure to participate in [Java Developers’ Day](http://09.jdd.org.pl/) in Kraków, Poland.
It was a great experience to see [Mark Richards](http://wmrichards.com/) (author of [Java Message Service](http://www.amazon.com/Java-Message-Service-Mark-Richards/dp/0596522045)) and [Scott Davis](http://www.davisworld.org/) ([Groovy Recipes](http://www.amazon.com/Groovy-Recipes-Greasing-Pragmatic-Programmers/dp/0978739299)) giving a talk.
Also I really enjoyed [Wojciech Seliga](http://unimplemented.blogspot.com/) speak about code review.
He works for Atlassian and shown a bit of Crucible, but his main point was that code review is not about looking for bugs made by other developers.
It is rather an agile process of getting to know the code.

I could write much more about JDD, of course starting from "you should regret if you haven’t been there", but I am quite sure that you are already waiting for the main topic.
Let’s just say, that there is a chance that JDD will take 2 days in the next year and I will do my best to be there.

After reading my [previous post](http://nurkiewicz.com/2009/10/ddd-in-spring-made-easy-with-aspectj.html) one of my friends asked about performance of creating objects marked as @Configurable.
He wants to inject EntityManager or other custom dependencies to his JPA POJOs but is concerned about performance.
Because many thousands of objects are created manually or by Hibernate during the application life, overhead introduced by Spring aspect injecting dependencies each time new operator is called may be significant.
There is no sense in talking about performance, I will simply measure everything!

But before we start our performance comparison test: I haven’t yet explained how to enable compile-time weaving instead of load-time.
First a word of explanation: CTW weaves aspect during compilation phase when building your application using Maven.
LTW does that when the class is loaded within the JVM.
Because both approaches should weave the same aspect and produce the same code, true performance of object creation should be the same despite the weaving method.
But we will check that out too.

As you probably expect, switching from LTW to CTW is only a matter of configuration, no code must be changed.
All you need to do is remove LTW Spring agent from pom.xml (surefire plugin configuration) and references to the agent when running JVM (on server and unit tests from your IDE).
When you got rid of LTW, enable CTW in no time (pom.xml):

```xml
<plugin>
 <groupId>org.codehaus.mojo</groupId>
 <artifactId>aspectj-maven-plugin</artifactId>
 <configuration>
   <complianceLevel>1.6</complianceLevel>
   <aspectLibraries>
     <aspectLibrary>
       <groupId>org.springframework</groupId>
       <artifactId>spring-aspects</artifactId>
   </aspectLibrary>
 </aspectLibraries>
 </configuration>
 <executions>
  <execution>
    <goals>
      <goal>compile</goal>
      <goal>test-compile</goal>
    </goals>
  </execution>
</executions>
</plugin>
```

Nothing to be explained, maybe except the complianceLevel, which corresponds to your JDK version.
You must also replace:

```xml
<context:load-time-weaver/>
```

with:

```xml
<context:spring-configured/>
```

In your Spring context configuration file.

Now, when we know how to switch back and forth from LTW to CTW, let’s run some performance tests.
I used Reservation class introduced in previous posts for testing creation performance, but I added three dependencies via transient fields in this POJO:

```java
@PersistenceContext
private transient EntityManager em;

private transient TicketService ticketService;

@Resource
private transient JavaMailSender javaMailSender;
```

The TicketService is being injected using the configuration below:

```xml
<bean class="com.blogspot.nurkiewicz.reservations.Reservation" scope="prototype" lazy-init="true">
 <property name="ticketService" ref="ticketService"/>
</bean>
```

By testing three beans with different injection techniques I wanted to find out, whether the type of injection has different performance impact.

The test scenario was to first create 1000 instances of Reservation class to warm up JVM and then measure the time of creating 50 thousand instances and putting them in previously created array to partially prevent GC.
Objects were created in the following weaving environment:

- none – no weaving has been applied
- CTW (no dependencies) – CTW enabled and @Configurable annotation added to Reservation class, but no dependencies injected (@PersistenceContext, @Resource and XML configuration removed)
- CTW (EM) – CTW with EntityManager injected
- CTW (\<property\>) – CTW with dependency configured in Spring XML context file being injected
- CTW (@Resource) – CTW with dependency autowired using standard @Resource annotation
- CTW (all) – CTW with all three dependencies listed above injected
- LTW (no dependencies) – like above but using LTW
- LTW (EM) – like above but using LTW
- LTW (\<property\>) – like above but using LTW
- LTW (@Resource) – like above but using LTW
- LTW (all) – like above but using LTW

Each test creating 50K instances has been repeated 8 times with very low standard deviation.
I measured the time it took JVM to create all the instances and scaled it to the number of instances being created per second.
Bigger value is better.

Probably you start to feel bored so I skip [detailed results](http://sites.google.com/site/nurkiewicz/Home/zalaczniki/ctwltw_results.pdf) and give you this nice chart:

[![](/assets/img/yesterday-i-had-pleasure-to-participate/1.png)](/assets/img/yesterday-i-had-pleasure-to-participate/1.png)
The results are a bit surprising for me for two reasons.
First, creating objects marked as @Configurable is less than 4 times slower than creating ordinary objects using new operator.
I assumed that creating new objects on heap is so greatly optimized that adding the overhead of Spring aspect scanning the class and trying to inject dependencies to completely unknown class would be tremendous.
But even if single dependency is being injected using @Resource or XML configuration, creation time is reasonable.
In fact, 4-5 times slower when the object is created by Hibernate is something that is almost impossible to measure and see in real environment – simply database and network connectivity brings much bigger overheads, making injection time insignificant.
Also, just as I thought, there is no big difference between LTW and CTW when there comes to performance, so use whichever you like.
Or at least do not take performance into account when deciding.

The second surprise, negative this time, was the time of creating objects with injected EntityManager.
Somehow it is almost 30 times slower than normal object creation and 6 times slower than injecting other custom Spring beans.
It is not the subject of this post to find out what happens behind the scenes with EntityManager (probably Spring does some additional magic with EntityManager proxy, maybe I will investigate this in the future), but the results are disturbing.

To summarize: using @Configurable annotation and injecting your Spring beans probably won’t be performance issue in your project.
Of course my test isn’t definite and you should check this in your particular case, but the benefits of Spring injection into domain objects can’t be overestimated.
But be careful when injecting EntityManager directly to your domain objects – the performance impact is somewhat significant and when creating thousands of objects your application might slow a little bit.

Test environment: Intel Core Duo T2050 1.6 GHz, 1 GiB RAM, Windows XP SP2, JDK 1.6.0_14
