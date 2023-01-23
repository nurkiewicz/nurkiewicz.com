---
title: "#51: Cloud computing: more than renting servers per minute"
category: podcast
redirect_from:
  - /51
tags: cloud-computing iaas paas faas amazon ec2
description: >
    Cloud computing is a broad term.
    In general, it refers to using hardware and software managed by someone else.
    Typically with very flexible pricing: we only pay for what we use and for the time we use it.
    We don't build data centers ourselves.
    We don't buy large servers and provision them.
    We simply rent a server on a per-minute basis.
    The cloud provider has a pool of servers and they are reused and recycled.
    Once we are done, we no longer pay and some other customer can use that same server.
    Just like we don't own a taxi.
    We barely pay for kilometers and minutes.
    When the server breaks for some reason, the provider takes care of repairs and replacements.
    We simply, almost transparently, get a new machine.
---

{% include player.html spotify_id="6lKzjo3FsHZbEloAdsmAvo" youtube_id="U3QhlQNvVJI" %}

{{ page.description }}

This cloud model is known as Infrastructure as a Service.
IaaS for short.
It was popularized by one of the first cloud vendors: Amazon's Elastic Compute Cloud.
However, these days IaaS is considered too low-level.
Developers lean toward more managed environments, known as Platform as a Service.
Or PaaS.
With PaaS we don't get access to bare machine with Linux.
Instead, we simply deploy complete applications written in Python or NodeJS.
The platform makes sure the runtime is available and up-to-date, networks ports are public, etc.
Sometimes, the cloud connects directly to your git repository.
It then deploys your app on every code push.
Contrast that to building your own data center, managing operating systems, deployment pipelines, and so on.

Cloud providers typically own tens of thousands of server around the world.
This means you can easily deploy your code close to your customers.
You can even do so dynamically.
For example, when there is a burst of traffic in specific region of the world.
Your app may need computing power in the morning, whereas another app uses the same resources in the afternoon.
This way you don't pay for unused resources, which are utilized by someone else.
Moreover, one big machine may be used by multiple customers at the same time!
Vitualization and containers allow for efficient allocation of resources, further pushing the price down.
Of course, it has some drawbacks.
If you accidentally share a physical machine with some really heavyweight workload, your performance will suffer.
It's not your fault you have a _so-called_ noisy neighbour.
The only thing you can do is kill your application.
Hopefully, cloud will reschedule it onto less active node.

Even higher-level services exist, often called Software as a Service.
Or SaaS.
Superficially, every application served over web browser can be considered SaaS.
So e-mail, video conferencing, text editors and spreadsheets.
But also providing managed databases or message brokers.
In general, we rent software on a per-user or per-minute basis, rather than buying a license.
But more importantly, we don't host the software.
And don't care about updates.
We just use it.
Cloud computing became such a buzzword that many old-school companies declare they moved to the cloud.
In fact, they barely replaced in-house mail server with GMail or Slack.

I keep talking about cloud providers and sharing hardware and software.
In reality, there's also private and hybrid cloud.
Private cloud is essentially our own data center, used exclusively by a single organization.
Hybrid cloud is a private cloud with some computing resources moved to the public cloud.
Such a division may be dictated by regulatory requirements, for example keeping sensitive data in-house.
Or an organization only rents extra computing power during traffic peeks.

That's it, thanks for listening, bye!

# More materials

* [Cloud computing](https://en.wikipedia.org/wiki/Cloud_computing)
* [free-for-dev](https://github.com/jixserver/free-for-dev) - free tiers in all clouds and other
* [#4: Serverless](/4)
