---
title: "#46: Kubernetes: Orchestrating large-scale deployments"
permalink: /46
tags: docker k8s
description: >
    Kubernetes is a platform for managing various workloads inside containers.
    Before I jump into a definition, let's describe the problems it tries to solve.
    Imagine your application consists of several components.
    It can be microservices, multi-layer application, etc.
    Each type of component needs to be deployed on multiple servers.
    First of all, to support fault tolerance, but also to achieve horizontal scaling.
    Doing this by hand is quite problematic.
    Manually tracking which servers should host which components is tedious and error-prone.
    You need to take into account:
    
    * CPU and memory requirements of each component
    * discoverability (where each component is located)
    * provisioning (different components need different libraries and packages)
    * scaling out and migrating from broken servers
    * and so on, and so forth
---

{% include player.html episode_id="3Y2ROQqmPKatG2bMMFzEQE" %}

{{ page.description }}

<!--
This sound like too much work!
All you want is to deploy a backend, a message queue and a database with some redundancy.
The first stop to tackle this chaos is containerizing everything.
You may use Docker for that, but Kubernetes supports other container technologies these days.
Once you have containers everywhere, Kubernetes can take care of the rest.
Of course, after you write a ton of YAML configuration.
This configuration describes your system's desired state.

* How many instances of each container you need?
* What are their CPU and memory requirements?
* Do they need any storage?

Technically, the tiniest unit of deployment in Kubernetes is a pod.
A Pod is one or more containers running closely together on the same host.
One container per pod is fine.

OK, once you've defined the desired deployment, you let Kubernetes do the hard work.
It looks at your available hosts and tries to schedule pods among them.
It makes sure that pods are evenly distributed and have sufficient resources.
It also does some DNS magic so that pods can see each other.
Finally, Kubernetes constantly watches over each pod.
If something bad happens with any pod, it's restarted automatically.

Moreover, you can define metrics that drive auto-scaling.
For example, high CPU utilization of one pod may increase the number of instances.
Another pod, based on some business metric, might be scaled down.
Kubernetes also handles deployments gracefully.
Downtime during deployment is a thing of the past.
The platform first deploy a bunch of instances with the new version.
Only when they boot successfully and are healthy, it shuts down the old version.
Clients won't notice, assuming your code is backward compatible.
Canary deployments with a fraction of the traffic routed to a new or experimental version is also possible.

Scheduling and scaling stateless containers is simple.
If your application dies, it's redeployed transparently.
Most of the time you don't really care about out of memory errors or network issues.
If they are occasional, you just let Kubernetes do the restart for you.
Individual instances are expendable, rather than cured.

It's much more complex when your container needs state.
Databases or message brokers need persistent, safe storage.
In that case you can either use _so-called_ Stateful Sets.
Or take advantage of hosted databases-as-a-service.
By the way, every major cloud vendor has Kubernetes support.
So you don't have to maintain Kubernetes cluster yourself.
It's actually quite a lot of work.
Instead you upload your application's descriptor to the cloud.
The vendor does the deployment for you.

That's it, thanks for listening, bye!
-->

# More materials

* [Kubernetes Documentation](https://kubernetes.io/docs/home/)
* [Kubernetes](https://en.wikipedia.org/wiki/Kubernetes) on Wikipedia
* [Minikube](https://kubernetes.io/docs/tutorials/hello-minikube/) - running Kubernetes locally
* Hosted Kubernetes on:
    * [GCP](https://cloud.google.com/kubernetes-engine/)
    * [AWS](https://aws.amazon.com/kubernetes/)
    * [Azure](https://azure.microsoft.com/en-us/overview/kubernetes-on-azure/)
    * [Oracle Cloud](https://cloud.google.com/kubernetes-engine/)
