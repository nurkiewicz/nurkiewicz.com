---
title: "#37: Fallacies of distributed computing: overlooked challenges"
permalink: /37
tags: microservices kubernetes distributed-computing
description: >
    Fallacies of distributed computing are a set of myths we believe, when designing complex systems.
    And what is a distributed system?
    Well, if your application is split into hundreds of microservices, it's distributed.
    Or if you have a single application, scaled horizontally to hundreds of instances.
    Or...
    If you have a monolith connecting to a database on the other node.
    This is a distributed system as well!
    OK, we have 200 seconds left and 8 fallacies to cover.
    Let's go!
---

{% include player.html episode_id="77yxlj0QlkCbWixgbjLTe2" %}

{{ page.description }}

<!--
## Number 1: The network is reliable

Somehow we believe that making an HTTP request will always suceed.
OK, it can fail with 404 when the resource does not exist.
We somehow forget about dropped packets, broken connections, random router failures, malformed data frames.
So much can happen between two machines talking to each other.
In the same server rack or on two sides of the ocean.

## Number 2: Latency is zero

We can't beat the speed of light.
See episode 7 of this podcast.
Light needs about hundred millisconds to travel from one continent to another.
There is no way around that.
If your system needs to make ten sequential requests between Europe and America, expect at least one second spent in transit.

## Number 3: Bandwidth is infinite

It's atually possible to saturate network interface.
Really.
Modern protocols like JSON over HTTP add so much bloat to the real data that it's surprisingly easy to run out of bandwidth.
Even without Facebook's scale.
BTW Facebook is using BitTorrent to deploy their monolithic backend.
Otherwise, it would take ages to transfer a large binary from one server to thousands of others.

## Number 4: The network is secure

In the old days we all used HTTP without TLS.
These days even raffic inside our data centers should be encrypted.
You never know what malicious actors are deployed next to your machine in the cloud.

## Number 5: Topology doesn't change

Modern architectures on top of Kubernetes and alike make it impossible to rely on static IPs.
Dynamic discovery is everywhere.
Sometimes we hit a server next to us, sometimes on the other continent.
The deployment topology is constantly changing and we can't predict latencies and number of hops.

## Number 6: There is one administrator

Modern systems are so complex that while handling a request you are probably hitting tens of APIs.
Some are public, some are proprietary.
Some were implemented by your team, some by an ofshore company years ago.
Sometimes the hardest part is not finding the broken component.
It's figuring out who is responsible for it.
There are even special service catalogs for that, like [Backstage](https://backstage.io/) from Spotify.

## Number 7: Transport cost is zero

Internet is running in debug mode.
HTTP protocol used to be textual.
Machine-to-machine communication is done via JSON, a textual protocol.
I can't even imagine how much computing power we could save by using binary protocols.
Not to mention the superior support for validation.
Although that power would have been used for pointless mining of bitcoins.
But that's a different story.

## Number 8: The network is homogeneous

We somehow believe that all machines are the same.
We forget that their architecture and capabilities are different.
When was the last time you though about little- vs. big-endian?
We standing on the shoulders of decades-old protocols.
Battle-proven under a lot of conditions.
Ethernet, IP, TCP/IP.
Don't take them for granted and don't reinvent them.

There are actually more myths, but these are most common.
That's if, thanks for listening, bye!
-->

# More materials

* [Fallacies of distributed computing](https://en.wikipedia.org/wiki/Fallacies_of_distributed_computing)
* [Backstage](https://backstage.io/) from Spotify
* [The Internet is running in debug mode](http://java-is-the-new-c.blogspot.com/2014/10/why-protocols-are-messy-concept.html)


{% include post-footer.md %}