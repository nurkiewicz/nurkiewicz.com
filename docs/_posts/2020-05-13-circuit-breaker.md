---
title: '#1: Circuit Breaker'
permalink: /1
tags: resilience4j hystrix polly akka ruby
description: Circuit breaker is a design pattern that prevents cascading failures in distributed systems.
---

{% include player.html episode_id="1vNMXp4pCNzty1o0L7UkP2" %}

{{ page.description }}

More details: [https://microservices.io/patterns/reliability/circuit-breaker.html](https://microservices.io/patterns/reliability/circuit-breaker.html) and [https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker](https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker).

## Circuit breaker implementations:

* [Resilience4j](https://github.com/resilience4j/resilience4j) (Java)
* [Polly](http://www.thepollyproject.org/) (.NET)
* [rubyist/circuitbreaker](https://github.com/rubyist/circuitbreaker) (Go)
* [Scala/Akka](https://doc.akka.io/docs/akka/current/common/circuitbreaker.html)
* [circuit-breaker-js](https://github.com/yammer/circuit-breaker-js) (JavaScript)


This episode was originally twice as long.
If you wish to hear full, director's cut version, check out [my mailing list](https://256.nurkiewicz.com/newsletter).
I will also notify you about new episodes and add some extra content.

## Also listen to

* [#2: Service Mesh](2) - often includes circuit breaker so you don't have to include it yourself in your application

{% include newsletter-input.md %}