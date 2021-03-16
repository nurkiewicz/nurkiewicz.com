---
title: "#36: Microservices architecture: principles and how to break them"
permalink: /36
tags: microservices monolith big-ball-of-mud rest graphql conways-law
description: >
    Microservices are contrasted to a monolith.
    Single, large application that implement the whole system.
    Typically hard to understand, develop, test and deploy.
    Monoliths tend to become a big ball of mud with each component referencing every other.
    The idea behind microservices is to split your complex system into multiple independent applications.
    Small and agile.
    They communicate with each other via APIs but are otherwise highly decoupled.
    The independence and decoupling has many aspects: deployment, languages and frameworks, storage, organization.
    Most importantly, each microservice should be self-sufficient to a reasonable degree.
    Let's discuss what it means and how often these aspects are violated.
---

{% include player.html episode_id="7siqtZgiHgPRzH5E7lkcQ3" %}

{{ page.description }}

<!--
# Deployment independence

It should be possible to deploy each service independently.
This means the implementation cycle of each service does not depend on the deployment of other services.
Services can be very quickly deployed and rolled back.
The biggest mistake is when two services need to be deployed simultaneously.
For example, due to a breaking API change.
Either we need to make sure the API is backward compatible - or merge these two services.

# Language and framework independence

Another advantage of microservice architecture is language and framework independence.
Service typically talk to each other via blocking APIs like REST.
Or, asynchronously via some message broker.
This means the implementation behind the API should be irrelevant.
C# or Haskell?
As long as it can talk HTTP, we are good to go.
In reality, organizations typically standardize on some rather fixed stack.
Thanks to this developers and knowledge is easily transferable.
Also, teams can make changes to other teams' services with little effort.
Last but not least, companies often build wrappers or helpers around existing frameworks.
They typically add features specific to organization and their infrastructure.
A different stack would require reimplementing that wrapper over and over.

# Storage independence

Similarily, this architecture allows different storage engines behind each service.
Some applications require strong transactional guarantees while others need fast, eventually consistent stores.
In practice, the cost of supporting dozens of entirely different DB engines is very high.

On the other hand, sometimes two distinct services use the same database.
This is probably the biggest anti-pattern.
Often it happens after extracting a service from a monolith.
Services should only talk through APIs, synchronous or asynchronous.
Common database is a hidden, tight coupling and unobvious dependency.

# Organizational independency

Another angle of independence is being able to develop services separately.
A service can be maintained and deployed without interrupting the work of other teams.
This is a striking occurrence of Conway's law.
It gets even better if services are so independent that they can tolerate partial failures.
If a service is useles without another service, they'd better be merged as they provide no isolation.

Microservices promises better scalability and improved modularization.
In practice, they require certain practice in the long run.
Fallacies of distributed computing have never been so important.
Troubleshooting issues requires extensive monitoring, logging and tracing infrastructure.
No wonder why some companies are actually merging their microservices back into a monolith.
Well-structured and modularized monolith.

# 2002 API mandate by Jeff Bezos

See [The Bezos API Mandate: Amazon’s Manifesto For Externalization](https://nordicapis.com/the-bezos-api-mandate-amazons-manifesto-for-externalization/):

* All teams will henceforth expose their data and functionality through service interfaces.
* Teams must communicate with each other through these interfaces.
* There will be no other form of inter-process communication allowed: no direct linking, no direct reads of another team’s data store, no shared-memory model, no back-doors whatsoever. The only communication allowed is via service interface calls over the network.
* It doesn’t matter what technology you use.
* All service interfaces, without exception, must be designed from the ground up to be externalize-able. That is to say, the team must plan and design to be able to expose the interface to developers in the outside world. No exceptions.
* The mandate closed with: Anyone who doesn’t do this will be fired. Thank you; have a nice day!
-->

# More materials

* [Microservices](https://www.martinfowler.com/articles/microservices.html) by Martin Fowler
* [microservices.io](https://microservices.io)
* [Building Microservices](https://samnewman.io/books/building_microservices/) by Sam Newman



{% include post-footer.md %}