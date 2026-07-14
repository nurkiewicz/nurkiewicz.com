---
layout: post
title: 10 reasons why I don’t like EJB3
date: '2009-08-11T20:21:00.003+02:00'
author: Tomasz Nurkiewicz
tags:
- ejb
- aop
- jpa
- web services
- spring
- junit
modified_time: '2009-11-28T19:49:01.948+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-9163354501174678450
blogger_orig_url: https://www.nurkiewicz.com/2009/08/10-reasons-why-i-dont-like-ejb3.html
---

...and prefer Spring.
After passing my SCBCD exam lately, I gathered few disadvantages of EJB3 standard, which I found especially irritating and annoying.

1\.
Whole concept of session beans is unclear to me.
Every programmer having even basic knowledge about concurrent programming knows, that single object can be safely accessed by multiple threads as long as concurrent threads do not modify the same variables (in short).
But since method arguments and local variables are local to the thread (they exist on stack), the only shared variables are object fields.
Logically, if the object has no fields (holds no state), it can be safely accessed by multiple clients at the same time.
Stateless session beans are, well...
stateless, they should not hold any state and the client should not depend on it.
So why, on earth, SLSBs are pooled and each client has its own instance a t atime?
Why in order to service N clients concurrently, application server creates N instances (or less, making some clients waiting)?
Spring beans are mostly singletons and they are used by concurrent clients with no problems.
We are enterprise developers, we know what concurrency and synchronization is – and how to avoid it, by writing thread-safe code.
What does the overhead of pool-management give us in return?

The other part are stateful session beans.
First, think about applications having web tier.
They already give you the set of tools you need: HTTP session.
Why can’t it be used instead of session beans?
Most web containers can replicate sessions, servlet specification defines notification API for passivation and activation events.
But still, HTTP session is not "enterprise" enough.
In fact, you still need to use it, at least to store the reference to SFSB (sic!)
But what about Java SE and other clients?
If you actually need server-side, short-living state, why not to use persistence?
In some cases you won’t even touch the database, as everything will happen in cache.
Or maybe other mechanism; do we really need stateful session beans as such a strong part of the specification?
In Spring I have my singleton beans and session-scoped beans, they do the job well.

2\.
Poor dependency injection.
You are only allowed to inject certain set of objects to session beans, message driven beans and interceptors.
Would you like to inject EntityManager to EntityListener (think of the new possibilities) or completely constructed collection to some bean?
Or maybe inject some non-EJB object, which is created via the factory?
Those, and many other scenarios can’t be achieved in EJB3.
Yes, but you can inject integer located in JNDI to int field, amazing!
3.
Aspect oriented programming.
During the past ten years, AOP is becoming more and more widely used.
But certainly not in EJB, where the concept of interceptors is a total misunderstanding.
First of all, you can match the interceptor to single method, all methods in a single bean or to all beans.
Do we miss something?
Thinking about matching all the methods in "\*Dao" named beans?
Or maybe all methods matching "send\*" pattern, no matter in which bean?
No can do, all or (almost) nothing.
Secondly, the whole point of aspect oriented programming is to decouple production code from aspects.
In EJB3 you can use ejb-jar.xml or [@Interceptors](http://java.sun.com/javaee/5/docs/api/javax/interceptor/Interceptors.html) annotation.
Yes, you put the information about which interceptors should be invoked directly in the target bean.
This is completely the opposite of what I expect and how it is done for instance in AspectJ.
Production code is polluted with interceptors meta-information.
If I look at the Spring support for aspect oriented programming, EJB3 interceptors look more like a joke to me.
By the way did I mention that specification only allows for around advices?
I know, this is the smallest problem.

4\.
Support for third-party technologies.
EJB3 has great support for JPA, allowing you to inject EntityManager directly to session and message driven beans.
And that’s all...
Try to send JMS message with proper resource management and error handling, same with JDBC.
Try to integrate iBATIS to your app, use any web framework, try to use almost anything – and you’ll end up with writing tons of code by hand.
EJB3 is a specification and does not provide any support for many major technologies.
This makes writing serious applications very time-consuming and error-prone, as lots of code should be either written or copy-pasted multiple times.
Surely, you can use Spring utilities in your EJB3 project (like [JmsTemplate](http://static.springsource.org/spring/docs/2.5.x/api/org/springframework/jms/core/JmsTemplate.html)), but wouldn’t it be simpler just to use one tightly integrated framework?

5\.
Scheduling asynchronous jobs.
Quartz is known for many years, Unix cron is older than me.
And what is "brand new" JSR 220 offering?
You cannot even simply start a job at specific hour of day, because if you use 24h interval, it will work properly only for half of the year (hint: DST).
Not to mention such a fancy expressions like "run it on every last Friday of the month between April and October each fifteen minutes during the night".
[TimerService](http://java.sun.com/javaee/5/docs/api/javax/ejb/TimerService.html) is deadly simple: specify direct date or delay, nothing more.
But the funniest thing about scheduling jobs is that...
you can’t do it!
New job may be scheduled only within SLSB or message driven bean’s business method.
Forget about starting new job when application starts up, it can’t be done (see point 9).
You must call some EJB, which will explicitly start the timer.
This sounds like a job for JMS: you run some business method and it schedules other activity to be run asynchronously in other thread – but it’s not.
To make matters worse, the specification even suggests to use scheduled jobs for some recovery and cleanup tasks (e.g.
because method annotated with [@PreDestroy](http://java.sun.com/javaee/5/docs/api/javax/annotation/PreDestroy.html) is NOT called on system exception, don’t ask me why).
OK, this is typical task for asynchronous jobs but hey, you cannot start them automatically.
And even if you manage to hack you application, you must first check, whether the job isn’t already started because jobs survive server crash...
and you might start the job once again.
Odd...

6\.
Lack of portability.
Some configuration parameters are just dying to be portable across different application server.
For example number of instances of enterprise beans.
But even though there is a specification, simplest activities like [invoking remote secured EJBs](http://nurkiewicz.com/2009/08/invoking-secured-remote-ejb-in-jboss-5.html) is not portable.
Not to mention JNDI names.
This means porting your application to different AS is going to be configuration nightmare, as you have to map hundreds of server-specific options, which are mostly the same, but for instance, have different names.

7\.
Distributed configuration.
I like Spring applications because all they produce is a single, portable WAR file, depending only on containers’ servlet specification.
If you use EJB3, you have external data sources, JMS queues, security configuration, etc. You are bound to AS and EAR file is just one piece of many, which must be deployed.
Sun recommends dividing your team to many roles, each having access to different parts of the app (Bean Provider, Assembler, Deployer, etc.)
I don’t buy it, as a developer I can choose JDBC connection pool provider, JMS provider – I do not depend on anybody, I have full control over my application.

8\.
No [Open Entity Manager In View](http://static.springsource.org/spring/docs/2.5.x/api/org/springframework/orm/jpa/support/OpenEntityManagerInViewFilter.html) support.
In Spring there is a concept of OpenSessionInView or OpenEntityManagerInView.
If you have ever written any web application, you are probably familiar with this pattern, sometimes prefixed with anti-.
In short, Spring manages filter which keeps Hibernates Session or JPAs EntityManager open all the time the HTTP request is being processed.
It means you can use lazy loading of persistent attributes whenever you like, especially in view and controller (not only in model layer).
In EJB3, when your entity leaves bean with transaction scoped EntityManager, it is detached from persistence context and you may no longer rely on lazy loading (in fact, JPA specification does not specify the behavior in such situation, probably some vendor dependent exception will be thrown...)
Of course, you may use EntityManager with extended persistence context, holding the transaction and persistence context as long as you want.
But this feature is only available for SFSB, while DAO classes are typical examples of stateless services, since they only dispatch calls to the persistence layer.
Additionally, having dedicated DAO bean instance for each client seems to be a big overkill.

9\.
No startup/shutdown application callbacks.
I mentioned about that in point 5.
It is obvious that you might want to call some code when your application starts up.
Obtain resources, read configuration, schedule job, or just log something interesting.
But EJB3 has no mechanism for that.
You might consider [@PostConstruct](http://java.sun.com/javaee/5/docs/api/javax/annotation/PostConstruct.html) annotated methods, but they are actually called whenever new instance of some bean is created.
And this typically happens when the first client accesses the bean and will eventually happen again for each new instance.
In Spring I have a singleton service and using the same [@PostConstruct](http://java.sun.com/javaee/5/docs/api/javax/annotation/PostConstruct.html) annotation the goal is achieved.
I can also subclass [ContextLoaderListener](http://static.springsource.org/spring/docs/2.5.x/api/org/springframework/web/context/ContextLoaderListener.html) and capture the very beginning of my app.
There are valid and elegant possibilities.

10\.
Unit testing.
In Spring I typically run micro-integration test of my bean and all other beans which are necessary to run the test.
I can also run almost whole application, mocking only the most low-level beans, like data sources.
I can also unit test single bean and inject mocks manually.
In EJB3 matters get complicated.
There is [Ejb3unit](http://ejb3unit.sourceforge.net/), which only emulates the JEE environment.
On the other hand there are some embedded containers, but would you really on them, especially if you are not embedding the same server as the production one?
Not to mention the time that is needed to run such a tool.
In most cases, it is faster for me to run mvn jetty:run (which is a complete environment for most of Spring apps) than to run unit test using embedded container...

I found Spring and EJB3 being direct rivals, covering pretty much the same area of use-cases.
I know 3.1 specification changes a lot (singletons, better scheduling), but JSR-220 is three years old and 3.1 still didn’t came out.
And I don’t want to start new holy war, especially because I also find many attractive features in Enterprise Java Beans.
The most valuable thing is absolutely zero-configuration principle.
Just add [@WebService](http://java.sun.com/javaee/5/docs/api/javax/jws/WebService.html) and [@Stateless](http://java.sun.com/javaee/5/docs/api/javax/ejb/Stateless.html) annotation to your class, compile, deploy and voilà, Java code is exposed as a web service, WSDL is generated, everything runs in stable application server environment.
Dependency injection (despite its limitations) is as simple as it could, JPA integration is great.
But after so many years of Spring framework development, it simply became more mature and flexible solution, in my humble opinion, of course.
