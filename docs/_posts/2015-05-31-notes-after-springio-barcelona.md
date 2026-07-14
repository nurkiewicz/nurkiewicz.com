---
layout: post
title: Notes after Spring.IO Barcelona conference
date: '2015-05-31T16:09:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- 4FinanceIT
- conferences
- review
- spring
modified_time: '2015-07-29T08:20:13.829+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-6822447587657186164
blogger_orig_url: https://www.nurkiewicz.com/2015/05/notes-after-springio-barcelona.html
image:
  path: /assets/img/notes-after-springio-barcelona/hero.jpg
  alt: "Barcelona seen from Tibidabo Mountain"
---

Courtesy of my company, [4Finance IT](http://www.4financeit.com/), I attended [Spring I/O Barcelona](http://www.springio.net/) this year.
*2 days full of Spring, Groovy, Grails and Cloud*, as the conference advertises itself, is not an exaggeration.
And although I am not really that interested in Groovy and especially Grails, a lot of other talks grabbed my attention and inspired in many ways.
Let me briefly summarize what I learned and topics I will definitely explore in the nearest future.

### [Spring 4 Web Applications](http://www.springio.net/spring-4-web-applications/) by Rossen Stoyanchev

One of the coolest things that come into Spring MVC 4.2 is a [`ResponseBodyEmitter`](http://docs.spring.io/spring-framework/docs/4.2.0.BUILD-SNAPSHOT/javadoc-api/org/springframework/web/servlet/mvc/method/annotation/ResponseBodyEmitter.html), similar to `DeferredResult` but designed for asynchronous streaming of multiple values.
In 4.2 you simply return `ResponseBodyEmitter` from your controller and push data from server to clients whenever you find it convenient.
There is a specialized [`SseEmitter`](http://docs.spring.io/spring-framework/docs/4.2.0.BUILD-SNAPSHOT/javadoc-api/org/springframework/web/servlet/mvc/method/annotation/SseEmitter.html) implementation.
[Server-sent events](http://en.wikipedia.org/wiki/Server-sent_events), [webSocket](http://en.wikipedia.org/wiki/WebSocket) and [STOMP](http://en.wikipedia.org/wiki/Streaming_Text_Oriented_Messaging_Protocol) were the most important themes during this talk.
Looks like Spring MVC gets a lot of improvements in 4.2, I can't wait for the official release.
Very good presentation.

### [Modern Java Component Design with Spring 4.2](http://www.springio.net/modern-java-component-design-with-spring-4-2) by Juergen Hoeller

A quick walk-through over various injection techniques available in Spring these days.
I actually learned few interesting tricks like injecting `Optional` for beans that might not be available in application context (e.g.
not enabled by profile):

```java
@Autowired
public FooService(Optional<BarService> barService) {
    //...
}
```

Even more interestingly, it's possible to have lazy bean even when it's needed by eager beans.
You just have to remember to annotate both bean and injection point with `@Lazy`:

```java
@Lazy
@Bean
AlphaService alphaService() {
    //...
}

//Usage:

@Autowired
public BetaService(@Lazy AlphaService alphaService) {
    //...
}
```

Spring will wrap lazy bean with a proxy so that your application starts up but the initialization of `AlphaService` is delayed to first usage.
Very useful.

### [Inside an Spring Event Sourced CQRS application – or why Microservices can actually work](http://www.springio.net/inside-an-spring-event-sourced-cqrs-application-or-why-microservices-can-actually-work/) by Eugen Paraschiv

Best talk during the first day.
And luckily it wasn't that much about microservices.
I heard about Eugen Paraschiv ([@baeldung](https://twitter.com/baeldung)) before, mostly from his [blog](http://www.baeldung.com/).
In this talk he presented how event sourcing helped them to build successful application.
He makes a clear distinction between event store (I personally believe Kafka is a great piece of software for that kind of use-case) and so-called *projections* - distributed consumers of events.
Interestingly independent projections are very similar to microservices.
Event sourcing is one of these topics I would really like to try in some application one day.

### [Manage your user’s session with Spring Session](http://www.springio.net/manage-your-users-session-with-spring-session/) by David Gomez

An interesting approach to abstract yourself from HTTP session.
Rather than relying on a built-in container session management (varying in quality, performance and custom features) [Spring session](http://projects.spring.io/spring-session/) entirely and transparently replaces it with custom backend infrastructure.
By default Redis is used for clustering.
If you struggle with session replication, give Spring Session a try.
Another alternative might be [Hazelcast's web session clustering](http://hazelcast.com/use-cases/web-session-clustering/) - working in a similar way, but using Hazelcast underneath.

### [Real-time with Spring: SSE and WebSockets](http://www.springio.net/real-time-with-spring-sse-and-websockets/) by Sergi Almar

Another talk about SSE and websockets, really interesting one.
Seems like Spring MVC 4.2 will be a great playground for more reactive (there, I said it) web application that push data in real-time to clients.
I am not especially interested in front-end development, but being able to easily stream data from the server or even communicate with it bi-directionally without costly HTTP overhead sounds awesome.

### [Performance Testing Crash Course](http://www.springio.net/performance-testing-crash-course/) by Dustin Whittle

Great talk with dozens of tools worth trying.
First let me shamelessly quote few facts from [Dustin's presentation](http://www.springio.net/wp-content/uploads/2014/11/performance-testing-crash-course-dustin-whittle.pdf):

> Microsoft found that Bing searches that were 2 seconds slower resulted in a 4.3% drop in revenue per user

------------------------------------------------------------------------

> When Mozilla shaved 2.2 seconds off their landing page, Firefox downloads increased 15.4%

------------------------------------------------------------------------

> Making Barack Obama’s website 60% faster increased donation conversions by 14%

------------------------------------------------------------------------

> Amazon and Walmart increase revenue 1% for every 100ms of improvement

During the presentation I came across numerous tools that might come in handy one day: *[`ab`](http://en.wikipedia.org/wiki/ApacheBench) (it's like command-line JMeter, I'm using it during my Hystrix talks)* [Bees with Machine Guns](https://github.com/newsapps/beeswithmachineguns) (I'm not joking, it's a distributed load-test tool running in EC2) *[Locust](http://locust.io/)* [Siege](https://github.com/JoeDog/siege) *[Multi Mechanize](http://testutils.org/multi-mechanize/)* and of course [JMeter](http://jmeter.apache.org/) and [Gatling](https://github.com/gatling/gatling) were mentioned

Just like we spend a lot of time testing backend and forgetting about TDD on the front-end, similarly network and browser are often forgotten when measuring website performance.
This turns out to be a big mistake, JavaScript, DOM rendering, network latency and bandwidth - all of these greatly contribute to overall user experience.
We recently instrumented our internal web application that had performance issues just to figure out that heavyweight DOM generated by Vaadin had the biggest impact on performance.

### [Spring-Boot Microservices, Container, Kubernetes – How To](http://www.springio.net/spring-boot-microservices-container-kubernetes-how-to/) by Ray Tsang

The talk started rather lazily and off-topic so some of my friends actually left early.
Boy, how wrong were they!
Live demo of Kubernetes, including gradual rollout and canary releases was one of the most breathtaking during the conference.
It's one of these talks where you want to try just learned stuff immediately.
Kubernetes manages instances of Docker images for you, allocating resources and coordinating them on real hardware.
Very agile way of deploying services and well-delivered demo.

------------------------------------------------------------------------

BTW the software behind [Spring.IO](http://spring.io/) main website is Spring-powered and open sourced: [github.com/spring-io/sagan](https://github.com/spring-io/sagan).
I didn't have time to look at it, but seems like a much better sample Spring application compared to "Pet Store" or other artificial project.
In overall I really enjoyed the conference and I'm glad I could spend extra few days sightseeing beautiful Barcelona.
