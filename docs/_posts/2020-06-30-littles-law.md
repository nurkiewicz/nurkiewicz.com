---
title: "#6: Little's law"
permalink: /6
tags: little nodejs tomcat
description: Little's law is an astounding equation that's dead simple, yet it can bring an amazing insight into what your distributed system is capable of.

---

{% include player.html episode_id="4JCnxbwVGdF7KHWVIkpFZs" %}

{{ page.description }}

But first, let's go to a grocery store.
Imagine there is a single clerk that, on average, procesess one customer in four minutes.
It's fairly obvious that he can serve: sixty minutes divided by four - fifteen customers per hour.
This is the arrival rate that is sustainable.
If surving a single customer would take three minutes instead of four, then the math is simple.
Sixty divided by three.
It makes twenty customers per hour.
As you can see, the faster clerk is capable of handling customers, the more customer he or she can handle in a given unit of time.
Like one hour.
Allright?
Fairly obvious.

But what if we add a second clerk?
We assume he or she has equal throughput, measured by the average time it takes to serve a single customer.
The throughput of our system suddenly doubled.
That, again, under the assumption that clerks are independents of each other
There is no synchronization needed between them.
Also there is no shared resource that they have to wait for.
Each clerk has his/her own register.
So it's no longer twenty customer per hour, but forty customers per hours.
You can probably guess that adding a third clerk increases the store's throughput as well.
It should be easy to figure out that the overall throughput is equal to the throughput of a single clerk, multipled by the number of clerks.
Under above assumptions.

Believe it or not, this is Little's Law in its whole glory.
Little's Law essentially says that the number of customers we can serve per hour is proportional to the number of clerks.
But it's also inversely proportional to the average processing time.
The more time it takes to serve one customer, the less throughput we get.
Number of workers divided by average transaction time.
That's it!

Let's go back to distributed systems and IT.
In our industry we can use Little's Law by replacing clerks with CPUs/servers/threads/coroutines.
Rather than measuring the time it takes to complete check-out, we use transaction or request-response time.
What's truly amazing in all these scenarios is that these are the only dependencies.
For example this law is not affected by the distribution of response times (like constant vs. normal vs. exponential).
It's also unaffected by the distribution of arrival rate of customers.
In a stable system it works even if we only know about averages.
All we need is the average number of requests per second, average response time and throughput.
Knowing two of them we can calculate the third one.

Let's take a concrete example.
Imagine `Node.js` server that handles CPU-intensive request.
`Node.js` is famously single-threaded, so if a request needs your CPU for 100 milliseconds, we can effectively server at most ten requests per second.
However if we deploy four `Node.js` server behind a load-balancer, our theoretical throughput grows to forty requests per second.
On the other hand let's take old-school Tomcat server with one hundred worker threads by conigured by default.
If one transaction is IO-bound and takes on average hundred milliseconds, this Tomcat instance can server **one thousand** request per second.
Notice I said _IO-bound_.
If transactions on this Tomcat instance are CPU-bound, we use number of available CPU cores, not threads in the equation.

Little's Law is amazing for many reasons.
First of all it allows you to estimates the theoretical maximum throughput of your system knowing very little about its internals.
You just need to know what are your bottlenecks (servers? CPUs? database connections?)
Or the other way around - how many resources you need to sustain given traffic, outlined in your SLAs.
It's even more amazing if you take into account how simple it is.
It works no matter what is the distribution of incoming requests, whether you have random GC pauses, etc.
You only work on averages.

That's it about Little's Law.
I decided to talk about because I belive it's very fundamental and every software developer should understand it intuitevely.
Hope you enjoyed it.

# More resources:

* [Little's_law](https://en.wikipedia.org/wiki/Little%27s_law)
* [John Little](https://en.wikipedia.org/wiki/John_Little_(academic))
* [Node.js and CPU intensive requests](https://stackoverflow.com/questions/3491811/node-js-and-cpu-intensive-requests)

# My talk where I briefly mention Little's law

From 23:03:

<iframe width="560" height="315" src="https://www.youtube.com/embed/5TJiTSWktLU?start=1383" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

{% include post-footer.md %}
