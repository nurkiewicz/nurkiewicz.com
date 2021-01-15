---
title: "#24: Service discovery"
permalink: /24
tags: zookeeper consul dns eureka
description: >
    In the old days an application consisted of a monolithic backend and a database.
    Once they were deployed their location never changed.
    So the only piece of configuration was the address of the database almost hardcoded into the monolith.
    These days an application is split into hundreds of microservices talking to each other.
    Probably too many services, probably talking too much.
    But that's a different story.
    Anyway, the environment became much more dynamic.
    Services come and go, orchestration frameworks are deploying them on different machines all the time.
    TCP/IP ports are random, instances are scaled up and down frequently.
    Sometimes automatically.
    New hosts are provisioned, old ones are shut down.
    Whole data centers are added.
    Under such circumstances we can no longer hard-code anything.
    When one service wants to talk to the other, it must somehow figure out where that service currently lives.
    It needs a mechanism to dynamically discover that service in an ever-changing environment.
---

{% include player.html episode_id="3caZaL67OHgcMP4RIaWV5C" %}

{{ page.description }}

<!--
## Shared database

The simplest approach is a shared SQL database.
Every time an application spins up it inserts its own name and address in some table.
When it shuts down, it removes itself.
Such a common registry has many drawbacks.
One stands out: it's a single point of failure.

## Zookeeper

Historically, Zookeeper was used instead.
It's a hierarchical, key-value database with strong consistency guarantees.
It has a few features that are quite useful.
Mainly so-called _ephemeral nodes_.
These special records disappear automatically when an instance, which created them, goes down.
So, when node spins up, it creates an ephemeral node containing its address.
When it goes down, this node disappears, making an address no longer visible.
That sounds great, however, Zookeeper wasn't designed for such a use cases.
It's simply... too consistent.
Zookeeper works great as a synchronization mechanism, for distributed locks and mutexes.
But when it goes down due to node failures, we loose whole service discovery mechanism.

And by the way, we don't need service registry to be so consistent!
You hear that right.
When registry is slightly out of date or eventually consistent, what's the worst thing that can happen?
Well, you may hit an endpoint of a no longer working instance.
There's nothing wrong with that, you simply retry.
You have retries anyway, right?
Moreover, you don't want to ask an external Zookeeper every time you make a network request to another service.
So you add caching and you are back to square one with an eventually consistent registry.
So where to go from here?

## Consul and DNS

More modern approaches are distributed and less error-prone.
For example, with Consul service registry agents are deployed next to applications on each server.
Data is broadcasted over the whole cluster and available locally.
To make it even more interesting the native API used for querying the registry is... DNS!
That's right, the good old DNS protocol.
Contrary to Zookeeper or any other centralized registry, the discovery mechanism is transparent to the application.
If you want to access a `product-service`, you simply call `http://product-service/something`.
DNS server provided by Consul, running on `localhost`, resolves `product-service` domain.
It looks like a real host, whereas in reality it's a dynamically managed binding.

Kubernetes with Kube DNS add-on has a similar functionality.
DNS with its built-in fault-tolerance, layers of caching and operating system support, once again saves day.

That's it, thanks for listening, bye!

-->

# More materials

* [Apache Zookeeper](https://zookeeper.apache.org/)
* [Eureka! Why You Shouldn’t Use ZooKeeper for Service Discovery](https://medium.com/knerd/eureka-why-you-shouldnt-use-zookeeper-for-service-discovery-4932c5c7e764)
* [Consul DNS](https://www.consul.io/docs/discovery/dns)
* [Kube DNS](https://github.com/kubernetes/kubernetes/blob/master/cluster/addons/dns/kube-dns/README.md)


{% include post-footer.md %}