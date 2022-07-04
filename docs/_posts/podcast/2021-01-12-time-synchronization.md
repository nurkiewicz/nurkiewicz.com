---
category: podcast
title: "#29: Time synchronization: how Network Time Protocol does it's magic"
permalink: /29
tags: ntp stratum spanner CockroachDB truetime
description: >
    Clocks are important to computers.
    Computers need to order events in a way understandable to humans.
    Every computer has a bunch of internal counters, like CPU ticks.
    But they only work within one machine.
    We need a way to have a reliable, global clock, that is synchronized between many computers.
    Why, exactly?
    Well, imagine you are selling tickets to The Rolling Stones concert.
    They sometimes sell within a few seconds.
    First come, first served.
    But who was first, if selling happens asynchronously in multiple data centers?
    Fans shouldn't be penalized for being routed to a server with higher latency.
    So, instead, we use timestamps.
    Late messages may still be treated as earlier ones if a transaction timestamp says so.
    Obviously we can't rely on the client's clock.
    It's too easy to change your laptop's time and see Mick Jagger from the front row.
    But how do we make sure servers aren't lying the same way?
    Even unintentionally?
    This is where NTP, network time protocol, comes into play.
---

{% include player.html spotify_id="6vvNijnCYZMVJM8ZzD1DhB" youtube_id="2epTAKPGcOs" %}

{{ page.description }}



For practical reasons we really want two servers, even very geographically distant, to have the same time.
I'm not talking about time zones.
I'm talking about tiny differences, measured in milliseconds.
They are called _time drift_ and are quite normal.
Computers don't have atomic, accurate clocks.
They will lose or gain a few microseconds here and there.
The only way to have clocks in sync is to have some third party.
That third party is the ultimate source of truth regarding the time.
These third parties are called time servers, organized in a hierarchy.
At the top there are _so-called_ Stratum 0 devices.
Typically atomic clocks or GPS.
Below there are Stratum 1 servers, known as primary time servers.
They have a direct connection to Stratum 0 and are very high-precision.
The hierarchy goes on, with each level deeper typically being less accurate.

The protocol itself is, on the surface, fairly straightforward.
You ask the time server, _what time is it?_
The server responds with some timestamp.
But it's fairly obvious that the network latency must be taken into account.
To make matters worse, network packets can be routed in different ways, leading to unpredictable latencies.
So, NTP protocol makes multiple roundtrips to the time server.
The algorithm calculates the average round-trip delay.
This works to a certain extent, sufficient in most cases.
But not always.
For example, when incoming and outgoing latencies are not the same.
The link is asymmetric.

But even in perfect conditions some applications can't tolerate clock drift between servers.
Take Google Cloud Spanner as an example.
It's a highly available and distributed SQL database.
In order to guarantee consistency between nodes, they must have clocks synchronized perfectly.
In practice, it's impossible.
So, Google uses their proprietary _TrueTime_ technology.
It guarantees that the clock difference is below 7 milliseconds within the cluster.
How does it help?
Well, any node can technically be at most 7 milliseconds ahead of the others.
So to guarantee that causality is not violated, each transaction... wait for it... waits.
Waits for 7 milliseconds.
This clever trick allows Spanner to achieve external consistency.
In short, it behaves as if all transactions run sequentially on a single node.
In reality, Spanner runs across multiple data centers.

An open-source equivalent to [Spanner](https://cloud.google.com/spanner/) is [CockroachDB](https://www.cockroachlabs.com/product/).
It obviously can't rely on hardware-accelerated, TrueTime technology.
Waiting is also impractical, as normal NTP synchronization can cause drifts of 200-300 milliseconds.
Sleeping for 300 milliseconds on each transaction is out of the question.
CockroachDB on the other hand makes an optimistic bet that clocks are in sync.
If it discovers a clock drift, some reads are retried.
Fun fact: if clocks between nodes drift too much, CockroachDB simply terminates itself.

You can find lots of extra materials in the show notes.
That's it, thanks for listening, bye!



# More materials

* [Network Time Protocol](https://en.wikipedia.org/wiki/Network_Time_Protocol)
* [List of highest-grossing concert tours](https://en.wikipedia.org/wiki/List_of_highest-grossing_concert_tours)
* [Cloud Spanner: TrueTime and external consistency](https://cloud.google.com/spanner/docs/true-time-external-consistency)
* [Living Without Atomic Clocks](https://www.cockroachlabs.com/blog/living-without-atomic-clocks/)
* [CockroachDB](https://www.cockroachlabs.com/product/)
* [Spanner](https://cloud.google.com/spanner/)
