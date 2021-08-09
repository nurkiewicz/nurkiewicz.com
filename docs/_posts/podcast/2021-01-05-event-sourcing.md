---
category: podcast
title: "#28: Event sourcing"
permalink: /28
tags: event-sourcing cassandra kafka read-model ddd event-store
description: >
    Event sourcing is an alternative technique of storing business data.
    Rather than updating a single database record, every change is captured in an immutable, append-only log.
    We never overwrite existing data.
    Instead, we create and store an event that represents what exactly has changed.
    From the business perspective.
    In order to recreate the current state of an entity we must go through all the events and reconstruct it from history.
    Event sourcing brings better auditing and debugging.
    Also, storing changes can be faster because it requires inserting a new record rather than updating an existing one.
---

{% include player.html episode_id="2Z8K3Zbe28Mqsw2gTMYJKo" %}

{{ page.description }}



Let's say you need to keep track of your customers.
When a new customer appears in your system, we store `CustomerCreated` event.
It contains customer's data provided during registration.
When that customer later makes a first purchase, `CustomerVerified` event is stored.
Changing the billing address, supplying credit card details, buying a premium plan...
All of these are kept in an event store.
We no longer have one central `Customers` table.
Instead, when we want to figure out whether the customer has a premium plan or not, we simply replay the events.
It is especially important for point-in-time queries.
For example, I know that the customer's billing address is in Warsaw.
But what was it 3 months ago?
Did he had a premium plan at that moment?
Moment was it cancelled?

If all we have is a `Customers` table, it's impossible to see the full history.
We only have access to the present snapshot.
We can achieve the same with simple auditing.
However, by rigorously recreating state from past events only, we can be sure that no knowledge is lost.
Another benefit is insane debugging capabilities.
Simply dump events related to the problematic customer onto your developer machine and replay them.
You can now debug how and when it transitioned from one state to another.

One of the biggest advantages of an event sourcing is the performance of writes.
Updating data is traditionally complex.
You have three choices:

* optimistic locking
* pessimistic locking
* or no locking and hoping for the best

Event sourcing requires an `INSERT`, rather than `UPDATE` in database terms.
Creating a new record or appending a new event to some sort of audit log is very cheap.
That is, compared to in-place modification.
However, the read path is much more complex.
Initially, you can replay all events in-memory every time you want to look at your customer.
This doesn't scale very well and makes reporting very hard.
Instead, we typically persist snapshots once in a while.
When you want to look at the current state of one customer, you simply take the last snapshot.
Known as a _read model_.
It may be slightly outdated, so you have to replay events that happened after that snapshot was taken.
This means your business logic may not see the most recent version of some entity.
Especially when the read model is updated asynchronously and periodically, rather than immediately.

Event sourcing may sound a little bit like a blockchain.
Well, you can sell it this way to Venture Capitals from San Francisco.
However, because events are stored in a central, secure database, there is no need for a blockchain.
The system trusts the event log so decentralized, zero-trust algorithms aren't worth it.
Speaking of a good database for events.
Some people use Kafka, some use Cassandra.
Some stick to relational database or choose commercial, specialized tools.
More links in the shownotes.

That's it, thanks for listening, bye!



# More materials

* [Event Sourcing Using Apache Kafka](https://www.confluent.io/blog/event-sourcing-using-apache-kafka/)
* [Using Cassandra as an event store](https://stackoverflow.com/questions/19321682/using-cassandra-as-an-event-store)
* [Event Store by Greg Young](https://www.eventstore.com/)
* [Event Sourcing pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)
* [A Decade of DDD, CQRS, Event Sourcing](https://www.youtube.com/watch?v=LDW0QWie21s) by Greg Young


