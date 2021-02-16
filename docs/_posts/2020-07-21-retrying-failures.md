---
title: "#9: Retrying failures"
permalink: /9
tags: ddos fault-tolerance
description: >
    I find it quite fascinating how many failures in complex systems could be avoided if we simply... tried again.
    So how so you retry effectively, so that your systems are much more fault-tolerant and less brittle?

---

{% include player.html episode_id="6QZVGv2RqHRoUvwCSjndPR" %}

{{ page.description }}

First, let's discuss the different types of failures.
Some errors can be retried immediately.
For example if you hit an unhealthy instance of a service behind a load balancer.
Making the same request one more time may route to a different, healthy service.
Under such circumstances it's worth retrying immediately after failure.

Other failures may occur if your dependency is having a very short hiccup.
Maybe a surge of traffic or garbage collection pause happened downstream.
From your perspective, the service is not responding or failing.
Retrying immediately may not lead to success because the underlying condition hasn't finished.
Therefore, it's a good idea to wait just a little bit, say 50 milliseconds, before making a retry attempt.

Some failures are more long-term.
For example, the system you're trying to reach is restarting.
Some platforms are notorious for long startup times.
Waiting just a few hundred milliseconds is not enough, an application may need several seconds to boot.
In such cases, retries should be less frequent, maybe every few seconds.

Now here's the tricky part: most of the time you have no idea which type of failure you are dealing with.
You just got an exception and mapping it to what happened is really tedious.
In other words, you have no idea whether retrying immediately is the right thing to do, or maybe short or long delays between retries are appropriate?
So you must guess, or adapt, to sound more scientific.
Unless you are 100% sure what kind of failure are you dealing with, use the following algorithm:

1. The first retry is almost instantaneous, just in case the failure was temporary and short-lived
2. The next attempt is after some delay, say 50 milliseconds. Chances are the problem will fix itself right away
3. Subsequent retries should have delays growing by a factor of, let's say 2. So 50 ms, then 100 ms, 200 ms, 400 ms, etc. This is called exponential back-off.

Why should the delays between retries grow?
After all, maybe our dependency is now healthy but we keep waiting several seconds for the next attempt?
It's tempting to keep retrying very frequently.
This, however, has some drawbacks.
First of all, you are generating lots of network traffic and waste precious CPU resources on both ends.
But more importantly, imagine your dependency just received a lot of requests and responds slower.
The service actually works just fine, but failed to deliver a response in a certain time.
You might encounter a failure due to timeout.
So you retry.
However, each retry is another request that floods your dependency.
Retrying frequently only makes the situation worse.
Instead, if your retries are less and less frequent over time, you give your dependency some time to heal.

Last but not least, there is an interesting phenomenon that may occur when multiple systems are observing failure in one component, for example a database.
Even though all clients are unrelated to each other, all of them observe the same failure at the same time.
For example when database restarts.
So all clients schedule a retry after some fixed time.
At this point there are no requests at all and database boots up.
However, retry happens independently in all systems at the same time.
The database can't keep up with such load and either rejects most of them or collapses, restarting one more time.
So all clients schedule one more retry, also after some fixed, longer amount of time.
The situation repeats, the database is under constant DDoS attack.
An attack that we accidentally created ourselves.
The solution is rather simple: add a little bit of randomness to each delay so that retries are smoothed across time.
Your dependencies can cope with a smooth load much better than sudden bursts of traffic.

# More materials

* [Retry Design Pattern with Istio](https://samirbehara.com/2019/06/05/retry-design-pattern-with-istio/)
* [`spring-retry` for Java](https://github.com/spring-projects/spring-retry)
* [Retry in Resilience4J](https://resilience4j.readme.io/docs/retry)

{% include post-footer.md %}
