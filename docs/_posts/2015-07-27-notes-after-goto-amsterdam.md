---
layout: post
title: Notes after GOTO Amsterdam
date: '2015-07-27T21:30:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- 4FinanceIT
- bitcoin
- conferences
- microservices
- review
modified_time: '2015-07-29T23:38:00.142+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4119130399355589398
blogger_orig_url: https://www.nurkiewicz.com/2015/07/notes-after-goto-amsterdam.html
image: /assets/img/notes-after-goto-amsterdam/hero.jpg
---

Few weeks ago I attended [GOTO Amsterdam conference](http://gotocon.com/amsterdam-2015/).
[Beautiful venue](https://nl.wikipedia.org/wiki/Beurs_van_Berlage), great food but most importantly, couple of interesting talks that caught my attention.
Out of two days and five to six tracks I want to comment couple of sessions.

# ["Challenges in Implementing MicroServices"](http://gotocon.com/amsterdam-2015/presentation/Challenges%20in%20Implementing%20MicroServices) by [Fred George](http://twitter.com/fgeorge52)

Yet another microservices talk, you might say.
But this one was slightly more in-depth and practical.
\[Slides are available\], let me comment slide 10, copied here:

> ## Summary principles of MicroServices
>
> - Very, very **small**
> - Team size of **one** to develop/maintain
> - Loosely coupled (including flow)
> - Multiple **versions** acceptable (encouraged?)
> - Self-monitoring of each service
> - Publish interesting "stuff" (w/o explicit requirements)
> - "Application" seems to be a poor conceptualization

I don't quite buy the "*micro-" or even "nano-" services trend.
The service shouldn't be as small as possible, it should encapsulate business component, typically [*bounded context*](http://martinfowler.com/bliki/BoundedContext.html).
If it's just one bounded context, it's a microservice.
Everything smaller is just not practical from performance perspective (too chatty protocol, too big latency).
I also don't think a team of* one *developer is enough.
Good team has [5 people +/- 2](http://noop.nl/2009/04/the-optimal-team-size-is-five.html), including QA, PO, etc. But in order to make any pair-programming, code review, improve [bus factor](https://en.wikipedia.org/wiki/Bus_factor) - you need more than one developer.
I agree with the rest of this slide and the whole talk was really cool.
I especially agree with publishing interesting* stuff\*.
Even without microservices we knew that centralized shared databases are bad.
Event store keeping long history of business events (e.g.
Kafka) can often solve the problem of sharing data between services.
Interestingly it allows us to start new projects that need lots (all?)
historical data from other projects without costly data migration and batch jobs.
Simply grab historical events, as deep as you want.
Word of caution: make sure your distributed event store doesn't become another centralized "database".
Otherwise you'll wake up one day with a system publishing events in a slightly different format than yesterday, breaking too fragile consumer.

I wholeheartedly agree with Fred that asynchronous communication should be preferred.
Just like with publishing events, communicating via message passing allows better decoupling and resiliency.
There is a place for blocking communication: when handling online requests or when data is needed now or never.
But focusing on message passing will pay off.

# ["How the Bitcoin Protocol Actually Works"](http://gotocon.com/amsterdam-2015/presentation/How%20the%20Bitcoin%20Protocol%20Actually%20Works) by [Jan Møller](https://twitter.com/jan_moller)

Amazingly, in 50 minutes Jan Møller managed to explain how BitCoin protocol/currency works.
I came to that session with absolutely no prior knowledge whatsoever but left with quite good understanding how brilliantly the protocol is designed.
Best talk in my humble opinion.
Check out [the slides](http://gotocon.com/dl/goto-amsterdam-2015/slides/JanMller_HowTheBitcoinProtocolActuallyWorks.pdf), I'm not even trying to summarize what I learned, but just to give you a quick overview what to look for.
The core idea behind bitcoin protocol is [blockchain](https://en.wikipedia.org/wiki/Block_chain_(database)) - an immutable, global, append only list of transactions.
Nodes in bitcoin network can append to that list, confirming transactions.

During this session I learned: how transactions get accepted and why it might takes several minutes, why mining used to be profitable and how miners can now profit from transaction fees, how was the algorithm design to control mining speed despite unknown number of participating nodes, and even what are the most popular attacks and they are circumvented.
Fascinating talk, Jan really knows what he is talking about.

I would also like to mention ["The Evolution of Hadoop at Spotify - Through Failures and Pain"](http://gotocon.com/amsterdam-2015/presentation/The%20Evolution%20of%20Hadoop%20at%20Spotify%20-%20Through%20Failures%20and%20Pain) by [Josh Baer](https://twitter.com/L_phant) and [Rafal Wojdyla](https://twitter.com/ravwojdyla) was quite entertaining.
These guys built an impressive Hadoop cluster and shared their knowledge and experience, for example how to monitor jobs developed by wide range of developers across the company.
However I am a bit concerned about the "future" of Map-Reduce concept.
Google [published the idea](http://research.google.com/archive/mapreduce.html) in 2004 and [abandoned this concept](http://www.datacenterknowledge.com/archives/2014/06/25/google-dumps-mapreduce-favor-new-hyper-scale-analytics-system/) in 2014 - are we betting the right horse with Hadoop?
Another talk I want link is ["Developing Event-driven Microservices with Event Sourcing & CQRS"](http://gotocon.com/amsterdam-2015/presentation/Developing%20Event-driven%20Microservices%20with%20Event%20Sourcing%20&%20CQRS) by [Chris Richardson](https://twitter.com/crichardson) - I couldn't attend that one, but [slides](http://gotocon.com/dl/goto-amsterdam-2015/slides/ChrisRichardson_DevelopingEventDrivenMicroservicesWithEventSourcingCQRS.pdf) look very promising.

Overall I enjoyed GOTO Amsterdam conference, big thanks to [4Finance IT](https://twitter.com/4financeit) for sponsoring the trip.
