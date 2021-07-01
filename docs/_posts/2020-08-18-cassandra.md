---
category: podcast
title: "#13: Cassandra"
permalink: /13
tags: cassandra bloom-filter scylladb memtable sstable vnode consistent-hashing cap-theorem
description: >
    Cassandra is an open-source NoSQL database.
    It's heavily optimized for writes, but also has intriguing read capabilities.
    Cassandra has near-linear scalability.
    In terms of CAP theorem it favours availability over consistency .
    Interestingly, despite NoSQL label, Cassandra tables have strict schema.
    Also, Cassandra Query Language is similar to SQL.

---

{% include player.html episode_id="24hMSXpkmQcVkfM1g0J4Ez" %}

{{ page.description }}

# Write path

Writing data to Cassandra is very clever.
It involves two operations: 

* writing record to an append-only commit log on disk 
* and updating memtable.

In principle, Cassandra works in-memory, storing most recent inserts and updates in memtables.
If the node crashes, data can be retrieved from a commit log.
As you already know from the episode about Kafka, append-only files are very cheap.

When memory is full, contents of memtable is flushed to disk to so-called SStable.
Once written, SStables are immutable.

If you update the same record multiple times, two things can happen:

* either you overwrite previous version in memtable, which is cheap
* or the previous version was already flushed to SStable, so you now have two copies.

Obviously having one outdated copy of a record is unfortunate.
Thus, Cassandra will transparently merge SStables during compaction.
Also, deleting records is quite costly.
You can't remove them from immutable SStable.
Instead, you create a special tombstone record.

# Read path

In order to understand how reading from Cassandra works, you must be familiar with a few concepts.
First of all, data is spread between partitions and partitions are assigned to virtual nodes.
The number of virtual nodes (vnodes for short) is fixed and much larger than the number of physical nodes.
Cassandra dynamically allocates vnodes to physical nodes.
This allows transferring very little data when cluster shrinks or scales out.

You have full control over partitioning.
Each row has a primary key, consisting of a partition key and optional clustering columns.
The partition key defines in which partition to look for data.
Knowing partition we quickly find vnode, knowing vnode we find physical node.
Clustering columns are used for sorting.

Despite having tables and columns, Cassandra is actually a sophisticated key-value store.
You can only query data by primary key or by the beginning of it.
By beginning I mean partition key only or partition key and some clustering columns.
This supports fast, sorted ranges queries.
It works because data within SStable is sorted when written down.
Querying by other columns is discouraged.

Knowing partition is not enough.
If given record is available in memtable, it's great.
Otherwise, we must find all SStables that _may_ contain it.
However, only the most recent version is important.
Specifically, if the last version is a tombstone, it means the record was deleted.
Another interesting fact: inserts and upudates are almost indistinguishable in Cassandra.

A clever optimization here is the usage of a Bloom filter.
It's a probabilistc data structure that can sometimes... lie.
It if says something is absent in a set, that's 100% sure.
If it says something is present in a set, that may not be true.
But it's enough to reduce the number of SStables being read.

# Technology

Cassandra is implemented in Java.
This means it may be occasionally be slow to respond when JVM performs garbage collection.
The database tries to workaround that by implementing so-called speculative execution.
Because data is almost always replicated across multiple nodes, client first asks the closest node.
However, if that node does not respond fast enough, it speculates that other node may reply faster.
At this moment we wait for the fastest one.

More radical approach was to reimplement Cassandra in a non-managed language, like C++.
That's how ScyllaDB was born.
Same concepts and API, different technology.
And much faster.


# More materials

* [Official website](https://cassandra.apache.org/)
* [Cassandra writes in depth](https://blog.softwaremill.com/cassandra-writes-in-depth-6ea8d7581eb)
* [Cassandra Architecture and Write Path Anatomy](https://medium.com/jorgeacetozi/cassandra-architecture-and-write-path-anatomy-51e339bcfe0c)
* [The most important thing to know in Cassandra data modeling: The primary key](https://www.datastax.com/blog/2016/02/most-important-thing-know-cassandra-data-modeling-primary-key)
* [The CAP Theorem](https://teddyma.gitbooks.io/learncassandra/content/about/the_cap_theorem.html)
* [Difference between UPDATE and INSERT in Cassandra?](https://stackoverflow.com/questions/16532227/difference-between-update-and-insert-in-cassandra)
* [7 mistakes when using Apache Cassandra](https://blog.softwaremill.com/7-mistakes-when-using-apache-cassandra-51d2cf6df519)


