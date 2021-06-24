---
title: "#20: Chaos engineering "
permalink: /20
tags: chubby chaos-monkey chaos-kong chaos-gorilla
description: >
    We tend to focus on testing happy paths and expected edge cases.
    But how do you make sure that your system can survive minor infrastructure and network failures, as well as application bugs?
    Especially in microservice or serverless environment, where there are tons of moving parts.
    I've seen too many times systems that fail miserably because some minor dependency was malfunctioning.
    For example you have a tiny service that displays a small social widget on your website.
    When that service is down, the rest of the website should work.
    But without proper care and testing you may end up with global HTTP 503 failure.
    Code reviews and unit tests are fine, but the ultimate test is... turning off that service on production.
    And making sure the rest actually works.
    This is called _chaos engineering_.
---

{% include player.html episode_id="3PyGpbnyKKFPREVcc6DDmR" %}

{{ page.description }}



Believe it or not, many organizations do practice deliberately injecting faults into production.
Now, turning off a service's instance on production is probably the easiest test you can conduct.
The client must catch an exception and handle the failure gracefully.
Sometimes by retrying, hoping to reach another healthy instance.
Sometimes by returning fallback value that's less relevant or up-to-date.
Ideally the end-user should not realize one of the services is down.
Of course that would mean that a failed service is not needed at all and can be shut down forever.
So in practice we expect visible, but insignificant degrade in service quality.

Chaos engineering principles define many other interesting fault scenarios.
Turning off one service is childish.
What about turning off a whole data center or region?
In this scenario your system should actually continue to work.
Maybe with greater latency.
That's assuming you are distributed geographically, right?

Speaking of latency, another failure mode is injecting artificial latency between services.
This is one of the hardest failures to handle properly.
Clients need to balance their timeout values between availability and too frequent timeout failures.
Also at this point you realize that there is this one forgotten HTTP client with no timeouts configured.
And suddenly your whole web application has response times measured in minutes.
That's why you exercise chaos engineering.

There are tons of other failures you can test for, including:

* network packet corruption
* disk loss, fill or corruption
* running out of memory or CPU

You can probably imagine more.
One crucial part of chaos engineering is having the courage to run experiments on productions.
Obviously you should start only when you are certain that nothing bad will happen to your business.
It will probably anyway, but it's better to firefight controlled chaos than deal with real failures.
After all, the purpose of chaos engineering is to discover and fix resiliency issues before they appear for real.

Many big companies are doing such experiments.
Most famously, Netflix with their so-called Simian Army: a suite of tools running different scenarios.
This suite includes adorably named tools like Chaos Monkey, Latency Monkey, Chaos Gorilla and Chaos Machine.
Another great example is Google.
Internal developers became too reliant on Google's internal locking service Chubby.
So when it went down one day, it brought down many Google services with it.
So Google now shuts down Chubby to meet SLA but not more so that developers learn how to deal with it.
Facebook's Storm Project simulates large data center failures.
Finally, Amazon realized that injecting 100 milliseconds of latency costs them 1% in sales.
100 milliseconds, time that seems imperceptible. 

That's it for today, thanks for listening, bye!





# More materials

* [Chaos engineering](https://en.wikipedia.org/wiki/Chaos_engineering#10-18_Monkey)
* [Service Level Objectives](https://landing.google.com/sre/sre-book/chapters/service-level-objectives/) from SRE book
* [Amazon Found Every 100ms of Latency Cost them 1% in Sales](https://www.gigaspaces.com/blog/amazon-found-every-100ms-of-latency-cost-them-1-in-sales/)
* [Netflix's Chaos Monkey](https://netflix.github.io/chaosmonkey/)
* [Litmus](https://docs.litmuschaos.io/docs/getstarted/) - chaos engineering for Kubernetes
* [Chaos Engineering Experiment Automation](https://chaostoolkit.org/)




