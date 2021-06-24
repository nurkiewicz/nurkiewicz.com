---
title: '#2: Service Mesh'
permalink: /2
tags: microservices istio envoy linkerd
description: Service mesh is used in environments where there are many services talking to each other. The aim of the service matches is to extract cross-cutting concerns like infrastructure and networking code to an independent layer. Service mesh is commonly implemented using an HTTP proxy.

---

{% include player.html episode_id="6zuXau7Dt0RmbhmbprUf4g" %}

# Transcript

Service mesh is used in environments where there are many services talking to each other.
The aim of the service matches is to extract cross-cutting concerns like infrastructure and networking code to an independent layer.
Service mesh is commonly implemented using an HTTP proxy.
Imagine you have just two services talking to each other, one named Alpha on a server A and another name Delta on a server D.
Without a service mesh when service Alpha wants to make a request to service Delta it simply makes an HTTP requests directly from server A to server D.
With service master situations is much more complex.
On each server there is a special proxy called the side car which is part of the service mesh.
When service Alpha wants to talk to service Delta, rather than making a request directly to server D, it makes a request to server A, to its own server so to localhost, to a sidecar proxy.
Sidecar proxy then makes a request to server D, but not to the service Delta.
Instead it makes a request to another side car that's deployed on server D.
And a sidecar proxy on server D makes a local request to service Delta over localhost.
Overall rather than having a single HTTP request from server A to server D, we have three requests.
Two requests are through localhosts so between service Alpha and sidecar proxy and then between sidecar proxy and service Delta and also one remote call between one side car and the other.
OK so what's the point of having this extra layer that definitely adds a lot of latency to your request?
Well, first of all, these two requests are over localhost so the performance hit is not as big as you would imagine.
On the other hand service mesh brings you a whole lot of features.
If you've ever tried microservice architecture you soon realized that there is a lot of infrastructure code that has to go to your application like service discovery, metrics, security.
Every single application within the ecosystem needs to have this custom logic built-in.
It gets even worse when you're truly polyglot so you have services written in .NET, Java, Python and whatever.
All the services need to have this custom logic.
And this custom logic has to be compatible with each other.
This is where service mesh really shines.
For example, you don't have to implement SSL or TLS in each and every service.
If you want to have secure communication it's enough that side cars can talk to each other over TLS and you can talk to your side car using even HTTP 1 protocol.

Service mesh can not only add security.
It can even upgrade to the HTTP 2 or 3 to get better performance.
Also because all traffic goes through service mash you have lots of metrics out of the box like which services are talking to each other, what are the response times, what are the error codes and so on and so forth.
Typically you would have to add this logic to each and every service, no matter in which language it is implemented.
Moreover, most of the time, you will come up with a library.
So you'll have a special library that you include in every service that adds these capabilities.
However, when you discover a bug or there is a feature that you would like to add you have to upgrade each and every service with a new version of this library.
When this logic is encapsulated in that side car in a service mesh you don't have to touch the application logic and at all, it becomes cleaner and smaller.
Also you don't have to implement this infrastructure logic for each and every language.
It has to be implemented just once in a service mesh and no matter the language or platform your service uses everything goes through the same side car proxy

That's it about service meshes.
Find more resources regarding service mesh in the show notes.
Bye!

## Notable implementations of service mesh:

* [Istio](https://istio.io)
* [Linkerd](https://linkerd.io)

## More details:

* [What's a service mesh? And why do I need one?](https://buoyant.io/2017/04/25/whats-a-service-mesh-and-why-do-i-need-one/)
* [What's a service mesh?](https://www.redhat.com/en/topics/microservices/what-is-a-service-mesh)
* [InfoQ](https://www.infoq.com/servicemesh/)
* [Service Mesh Landscape](https://layer5.io/landscape)
* [Service Mesh Comparison](https://servicemesh.es/)

## Also listen to

* [#1: Circuit Breaker](1) - often included transparently in a service mesh

