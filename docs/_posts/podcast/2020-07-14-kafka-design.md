---
category: podcast
title: "#8: Kafka's design"
permalink: /8
tags: kafka sendfile tail partitioning
description: >
    Kafka is not a message broker.
    However, it can be used as such very effectively.
    Instead, I'd like to think about as a very peculiar database.
    A database where inserts are insanely fast and sequential reads are preferred and very fast as well.
    Also, there is very little support for deleting and updating data. In this episode I am focusing on the architecture and internals of Kafka.
    The best way to understand Kafka is by examining how it works.

---

{% include player.html spotify_id="2gXn06ADmh68Pae1rRAHru" youtube_id="lTyta7LoHeY" %}

{{ page.description }}

In this episode I am focusing on the architecture and internals of Kafka.
The best way to understand Kafka is by examining how it works.
Writing data to Kafka (publishing messages) is done by appending messages to a flat file.
Such operation is extremely fast because both storage and operating systems are optimized for appending.
Message is identified by its position in the file, known as *offset*.
Reading data from Kafka (consuming messages) is done by opening that file and simply reading it sequentially.
When the consumer reaches the end of file, it simply waits for more messages.
On the other hand if consumer is slower than producer, it keeps reading and ever-growing file.
When consumer crashes, all we need is its offset - a position in the file he last read.
Therefor consumers are very cheap in Kafka.
Typical message broker needs to remember if each and every message was consumed.
In Kafka we consume sequentially.
Producers are also very cheap, they simply transfer data from socket to file.

As a matter of fact there is an important optimization happening in the write path.
On the lowest level bytes from incoming messages are read from socket and saved to file.
Implemented naively, one must copy data from socket (kernel) to process memory and then back to kernel (to file).
Turns out operating system has a special routine called `sendfile` that allows routing from one abstract file (socket) to another without switching to user space.

OK, all this sounds like appending logs to a log file and reading them using UNIX `tail` command.
Indeed, that's how it would work if Kafka was working on a single server.
However, Kafka broker is distributed, replicated and fault-tolerant.
This means that data is split across multiple nodes, but also the same data is copied to a few nodes for safety.
How does this architecture scale?
A single logical topic is split into multiple partitions.
Each partition is a single append only file.
The number of partitions is fixed, whereas the number of nodes is dynamic.
When sending a message, we can optionally choose a message key.
Key uniquely identifies a partition.
Then Kafka client must figure out which node currently owns given partition.
This changes dynamically when nodes die, cluster is scaled out, etc.
Kafka brokers manage that.
Also, they manage replication, so that the same partition is copied over to multiple replicas.
When a node dies or a new one appears, Kafka transfers partitions seamlessly.

Splitting data into partitions has a few advantages.
First of all messages sent to the same partition (with same key) have guaranteed order.
Secondly, one can either consume messages from all partitions, or just from a selected subset.
Offset (positions in the file) are also defined for each partition.

Such a simple architecture is enough to store and consume hundreds of thousands of messages.
The last time I checked, Kafka was processing **trillion** messages per day.

That's it, thanks for listening, bye!

# More materials

* [`sendfile` in Java](https://docs.oracle.com/javase/9/docs/api/java/io/InputStream.html#transferTo-java.io.OutputStream-)
* [How LinkedIn customizes Apache Kafka for 7 trillion messages per day
](https://engineering.linkedin.com/blog/2019/apache-kafka-trillion-messages)


