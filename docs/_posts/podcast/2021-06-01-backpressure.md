---
category: podcast
title: "#42: Flow control and backpressure: slowing down to remain stable"
permalink: /42
tags: backpressure reactor rxjava tcp-ip
description: >
    Imagine two independent systems communicating with each other.
    One producing data and the other consuming it.
    There must be some place where data is buffered.
    Just in case the producer generated some data but the consumer is currently busy.
    For example, incoming requests, messages, packets - must wait.
    Sooner or later, this buffer overflows and either starts dropping data or crashes altogether.
    Moreover, large buffers imply growing latency between production and consumption.
    The consumer is perceived less responsive because data waited for a long time in queue.
    Especially when nothing is prioritized, so first come, first served.
    Also known as FIFO, first in, first out.
---

{% include player.html spotify_id="6llTs2WyoVFkSsTsW2NQfD" youtube_id="S_5hiY5esf4" %}

{{ page.description }}

Backpressure is a mechanism of automatically slowing down the producer when the consumer can't keep up with the incoming data.
This term was popularized recently with many reactive libraries flourishing.
But it's much older.
TCP/IP protocol used throughout the Internet has flow control mechanism built-in.
To fully appreciate it let's first think how TCP works.
We have two ends, one sending data and the other receiving it.
The receiving end has a receive buffer where data waits to be processed.
If the receiver is busy, data sits in that buffer.
Whenever data is received, the receiver sends back acknowledgment.
That ACK packet not only confirms how many bytes we received successfully.
It also notifies how many bytes we have left in the receiving buffer.

This algorithm has two great advantages.
First of all, if the sender doesn't get an acknowledgement, it won't send more data.
To improve the throughput there's actually a sliding window.
The sender can push data without receiving ACK, hoping it'll arrive sooner or later.
If not, it'll stop.
Moreover, if the receiving window is full, the sender will also stop.
So TCP naturally adapts to the speed of the receiver when sending data.
This is called flow control.

It even goes the extra mile by introducing congestion control.
This mechanism prevents the network from saturating the available bandwidth.
TCP starts slowly and gradually increases the throughput until it experiences congestion.
Then it goes back a bit and finds the optimal speed.

As you can see, TCP deals with varying sender/receiver capabilities in a natural and transparent way.
Like everything in IT, old ideas are rephrased and sold like new ones, over and over again.
Backpressure in reactive libraries like RxJava and Reactor is inspired by TCP.
Imagine you have two components within the same application.
They communicate with each other by message passing.
Without backpressure the queue between them may grow indefinitely.
But because the consumer is aware of its limitations, it does not allow that.
Rather than blindly receiving and accepting data, it explicitly asks for a given number of events.
The producer _should_ honor that request.
Honouring means slowing down the production of events.
Of course, not all sources can be slowed down.

To make matters worse, often producers consume events on their own as well.
They simply receive, transform and forward events.
Imagine an event-driven architecture where dozens of components send and receive data constantly.
In such a scenario, the producer must forward the desired number of events to its producer.
Over time, the system tends to self-tune itself.
Data is not piling up, but all components are working at their full capacity.

This is sometimes called a push-pull model.
The producer pushes data to the consumer.
But the consumer pulls data, based on its current processing capacity.

That's it, thanks for listening, bye!

# More materials

* [TCP Flow Control](https://www.brianstorti.com/tcp-flow-control/)
* [TCP slow start](https://developer.mozilla.org/en-US/docs/Glossary/TCP_slow_start)
* [I'm not feeling the async pressure](https://lucumr.pocoo.org/2020/1/1/async-pressure/)
* [Push-Pull Functional Reactive Programming](http://conal.net/papers/push-pull-frp/push-pull-frp.pdf)
* [The Reactive Manifesto](https://www.reactivemanifesto.org/)
* [Reactive Streams](https://www.reactive-streams.org/)
* [#35: Reactive programming: from spreadsheets to modern web frameworks](https://256.nurkiewicz.com/35)


