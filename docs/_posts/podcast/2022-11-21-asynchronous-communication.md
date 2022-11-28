---
title: "#91: Asynchronous communication: loose coupling in distributed systems"
category: podcast
permalink: /91
tags: asynchronous message-broker
description: >
    There are two main ways to communicate between components in your distributed system: synchronous and asynchronous.
    Synchronous communication is like making a phone call.
    The system on the other side must be present and you actively wait for a response to your every question.
    Examples of this style include [REST](https://nurkiewicz.com/44), [SOAP](https://nurkiewicz.com/74) and [GraphQL](https://nurkiewicz.com/3).
---

{% include player.html spotify_id="0Ljr9sGNDCVJsEpzaa687r" youtube_id="TODO" %}

{{ page.description }}

On the other hand, asynchronous communication is more like sending a text message.
Fire and forget.
You don't actively wait for a reply.
You may continue your normal work, rather than passively waiting.
You can also send multiple messages to one or many subscribers.
But asynchronous communication requires a message broker in between publisher and subscriber.
You don't connect directly from producer to consumer.
Instead, you pass your message to the broker.
Then it's the broker's responsibility to deliver that message.
Sooner or later.
Keep in mind that the producer and the consumer don't have to be alive at the same time, ever.

At first sight, the asynchronous communication style has many drawbacks.
When sending a message, you have no idea when it will arrive at the destination.
Frankly speaking, you may not even know if there _is_ any destination.
Also, in general, it's one-way communication.
If you want to ask a question and get an answer straight away, you're out of luck.

But asynchronous communication with a message broker in between has a lot of advantages as well.
First of all, it decouples the producer from the consumer.
What does it mean?
Well, when the producer sends a message, all it needs is a message broken to be available.
Once the message is sent, the producer may go offline or do other work.
At this point, the message broker, a special reliable cluster, does its best to route the message.
In the simplest case, there is just one consumer on the other side.
However, if the consumer is down or busy, the message will wait indefinitely.
This way, the producer is unaware of transient issues with the subscriber.

Moreover, if the subscriber is really busy handling, a backlog of messages is created inside a broker.
The producer may continue sending messages.
It's the broker's responsibility to deliver them, sooner or later.
This enables many mechanisms that improve reliability and scalability.
For example, by observing queue length we can automatically scale out consumers.
And vice versa, we may scale it down, once the backlog is empty.

Message-oriented architectures also support other interesting patterns.
Rather than point-to-point communication, we may want to broadcast messages to multiple consumers.
There are two possible scenarios.
In the first one, the consumer is deployed on multiple instances.
A producer sends a message that is automatically delivered to all instances.
This is useful to synchronize the internal cache or something.

In the second scenario, there are multiple different applications listening to the same event.
In principle, the producer may not even know which applications (if any) are interested.
And the list of subscribers is dynamic.
In this pattern, new consumers implementing new use cases can be added with very little effort.
For example, if one application sends an `InvoicePaid` message, multiple components may be interested in that.
One for billing, one for mailing, etc.

There is a ton of other patterns for message-oriented architectures.

That's it, thanks for listening, bye!

# More materials

* [https://www.enterpriseintegrationpatterns.com/](Enterprise Integration Patterns): Patterns and Best Practices for Asynchronous Messaging
* [Kafka's design](https://nurkiewicz.com/8)
* Synchronous communication protocols:
    * [REST](https://nurkiewicz.com/44)
    * [SOAP](https://nurkiewicz.com/74)
    * [GraphQL](https://nurkiewicz.com/3)
