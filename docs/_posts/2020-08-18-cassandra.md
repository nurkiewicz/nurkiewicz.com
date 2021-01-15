---
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

# More materials

* [Official website](https://cassandra.apache.org/)
* [Cassandra writes in depth](https://blog.softwaremill.com/cassandra-writes-in-depth-6ea8d7581eb)
* [Cassandra Architecture and Write Path Anatomy](https://medium.com/jorgeacetozi/cassandra-architecture-and-write-path-anatomy-51e339bcfe0c)
* [The most important thing to know in Cassandra data modeling: The primary key](https://www.datastax.com/blog/2016/02/most-important-thing-know-cassandra-data-modeling-primary-key)
* [The CAP Theorem](https://teddyma.gitbooks.io/learncassandra/content/about/the_cap_theorem.html)
* [Difference between UPDATE and INSERT in Cassandra?](https://stackoverflow.com/questions/16532227/difference-between-update-and-insert-in-cassandra)
* [7 mistakes when using Apache Cassandra](https://blog.softwaremill.com/7-mistakes-when-using-apache-cassandra-51d2cf6df519)

{% include post-footer.md %}
