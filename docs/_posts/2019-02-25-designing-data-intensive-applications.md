---
layout: post
title: 'Designing Data-Intensive Applications: my favourite book of last year'
date: '2019-02-25T23:31:00.001+01:00'
author: Tomasz Nurkiewicz
tags:
- review
- books
modified_time: '2019-02-25T23:34:44.150+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3046381142609042890
blogger_orig_url: https://www.nurkiewicz.com/2019/02/designing-data-intensive-applications.html
image:
  path: /assets/img/designing-data-intensive-applications/hero.jpg
  alt: "Warsaw Old Town"
---

Martin Kleppmann, the author of [*Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems*](https://amzn.to/2teQsWS) wrote a wonderful, comprehensive book.
I consider this to be my most valuable reading of 2018, even though the book is almost 2 years old now.
Martin proves that great bestsellers in the programming industry aren’t about shiny new frameworks and buzzwords.
*Data-Intensive Applications* is a solid piece about the fundamentals of computer systems, especially from the data manipulation perspective.

This book introduces and explains all topics related to data storage, retrieval and transmission.
That doesn’t sound very exciting, does it?
However, expect very thorough (600+ pages!)
and enjoyable journey through databases, protocols, algorithms and distributed systems.

In the **first chapter**: “*Reliable, Scalable, and Maintainable Applications*” the author describes the environment in which our systems live nowadays.
What are the possible failure modes (software, hardware, human), what are the limits of scalability and how to tackle the complexity of ever-evolving system?
**Second chapter** “*Data Models and Query Languages*” goes through the history of various query languages.
Apart from SQL we learn about how diverse NoSQL query languages are, including graph queries, map-reduce paradigm and logic languages.
**The third chapter**, titled “*Storage and Retrieval*”, describes algorithms and data structures relevant for storing and querying data.
We are talking B-trees, hash-indexes and so on.
This chapter really blew my mind with a very detailed explanation of replicated key-value database that is optimized for writes and fault tolerant.
The author explains very clearly every design decision he makes: keeping the most recent data in memory accompanied with an append-only log for persistence and fault tolerance, background compaction, consistent hashing to avoid collisions.
Also synchronous vs. asynchronous replication, bloom filters, and much more.
After many pages of this seemingly academic discussion, he basically says: OK, so this how Cassandra works.
You’ll find dozens of such eye-opening themes throughout the book.

In **chapter four**: “*Encoding and Evolution*” author explains the challenges of schema evolution.
Often forgotten or ignored problem, especially when everything is a map of maps of something (e.g. JSON document).
I admire how different text and binary formats are explained in-depth.
To the point where Martin compares each binary format byte-by-byte.
Avro, Thrift, Protobuf - you will have a very good understanding of these formats and what makes some of them more robust than the others.
**Chapter five** was a joy to read: “*Replication*”.
Leader vs. follower, multi-leader, leaderless replication are all explained with their advantages and drawbacks.
Such a great introduction should help you to choose the right (No)SQL datastore in the future.
“*Partitioning*” (**chapter six**) was even better.
Once your dataset is replicated, how do you split data to a subset of nodes to avoid data loss?
Partitioning by key, hashing, routing, rebalancing - these are all covered.

**Chapter seven**, “*Transactions*” says it all.
It’s amazing how Martin finds parallels in rather distant technologies.
For example relation databases with their transaction log and distributed message brokers.
I always wondered how transactions are *really* implemented in modern databases.
This book gives very thorough explanation.
**Chapter eight**, “*The Trouble with Distributed Systems*” deals with many fault modes in distributed systems.
Unsynchronized clocks are explained very thoroughly, as well as various network unreliability scenarios, Byzantine faults and other failure modes.
Must read for every developer working on a distributed system.
**Chapter nine**, “*Consistency and Consensus*” continues discussion on challenges in distributed systems.
How independent nodes can agree on something?
How can they choose a leader without any shared state?
How to tackle ordering guarantees and linearizability?
Martin does not follow recent hypes and doesn’t lean toward any particular technology.
For example, a chapter related to distributed transactions doesn’t simply repeat common wisdom that “they are bad and slow”.
Instead, he explains in detail how a distributed transaction manager works, what is the protocol and failure scenarios.
I didn’t know that XA manager is such a crucial point of this design style and when it fails, the rest of the system basically stalls.
Moreover, it *must* recover because it’s stateful and distributed transaction log can’t simply disappear.
So yes, distributed transactions are slow and brittle.
But the author at least explains why, rather than repeating common Internet wisdom.

**Chapters ten and eleven** are describing batch and stream processing respectively.
Despite recent hype for stream processing, batch processing is also considered a viable option.
Book concludes with the last, **twelfth** chapter: “*The Future of Data Systems*”.
Surprisingly, the very end of the book tackles ethic problems like privacy and tracking.
After such a deep and technical content looking through this perspective was truly mind-boggling.
I loved it.

My favourite quote from the book comes from… the glossary!

*CAP theorem: A widely misunderstood theoretical result that is not useful in practice.*
**[Designing Data-Intensive Applications](https://amzn.to/2teQsWS) - highly recommended.
