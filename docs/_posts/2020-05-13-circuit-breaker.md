---
category: podcast
title: '#1: Circuit Breaker'
permalink: /1
tags: resilience4j hystrix polly akka ruby
description: Circuit breaker is a design pattern that prevents cascading failures in distributed systems.
---

{% include player.html episode_id="1vNMXp4pCNzty1o0L7UkP2" %}

# Transcript

Circuit breaker is a mechanism that sits in between your system and its dependencies
When external dependencies like APIs or databases work, circuit breaker is transparent and simply does nothing.
However, when they start to malfunction and when they do it too frequently circuit breaker kicks in and opens and you can no longer access external API.
Instead your system fails immediately
Imagine your external dependency just fails constantly.
That's not that bad, it can get much worse.
For example, when your external dependency is really slow and you constantly hit timeouts.
When an external dependency becomes really slow, your own system becomes slow as well because you have to wait for that dependency.
And if you are a dependency on another system then that another system becomes slow as well.
So it's much better to fail immediately rather than constantly waiting for a broken dependency.
If you observed timeouts for the last five seconds there's a very small chance that the timeout will stop occurring in the nearest future.
So that's where the circuit breaker kicks in.
It cuts off this external dependency and you get a failure immediately.
From that perspective your system still fails but at least it fails in a predictable way

It's also beneficial for the server.
What could be the cause of the external dependency to time out suddenly?
Well, for example, it has a very long GC pause or maybe it's restarting or maybe it received a lot of traffic and it cannot keep up with it.
If you just keep slamming this external dependency with more and more requests then you're not giving that dependency time to recover.
However, then your circuit breaker kicks in.
When it opens, the dependency has a little bit of time to heal itself.
Maybe restart or maybe warm up some caches is whatever circuit breaker.
Can be in one of three states.
When it's closed it's transparent.
When it's open you are not calling external dependency.
Instead you get a failure immediately.
There's a third state that's actually crucial for how circuit breaker operates.
It's called half-open.
In the half-open state circuit breaker behaves as if it was open.
However, exactly one request every second or every ten seconds is actually passed to the broken dependency just in case that dependency fixed itself.
If the dependency is fixed, so if this single request, this probe, succeeded, the circuit breaker automatically closes.
However, if this request failed then circuit breaker assumes that your dependency is still broken and it just keeps failing immediately without even touching it.

Should you use the circuit breaker?
Well, if you think you don't have a distributed system, you just have a single service and there's no point in shielding yourself from the failures of external services, you might be wrong.
Because most likely you're using a database, most likely you're using some sort of payment API or whatever.
And in that case you still don't want your system to break if the external dependency breaks.
Another benefit is that, as already mentioned, you give some space for an external dependency to recover.
Your system is more likely to self heal itself.
Another benefit of a circuit breaker is that very often it automatically throttles traffic if there are too many requests.
What happens when you see a web page that's just too slow?
Well, if you are very patient you just wait for it until it comes up into your browser.
Or you hit _Refresh_.
When you hit refresh you actually make a second request and a second request most likely puts even more pressure on your system.
So your system becomes even slower.
So you hit _Refresh_ one more time and one more time and that's a cascading failure as well.
When a circuit breaker sees such excessive traffic it can actually block some requests or reject them immediately.
This is also very good behavior.

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


