---
title: "#11: MapReduce"
permalink: /11
tags: hadoop hdfs spark hive google
description: >
    MapReduce is a programming model for processing large amounts of data.
    It works best when you have a relatively simple program, but data is spread across thousands of servers.
    MapReduce was invented and popularized by Google.
    I'll talk about MapReduce in general and Hadoop in particular.

---

{% include player.html episode_id="4lmzW5Z11t9Mrf2UORvG1C" %}

{{ page.description }}

## How MapReduce works?

Imagine you have a lot of data, way more than fits on disk.
As a matter of fact, MapReduce works best with distributed file systems like HDFS.
MapReduce requires you to write two pieces of code: _map_ and _reduce_.
Duh!
First, your input data is split into records.
These can be database records or, more commonly, lines from a large file.
In the _map_ phase, input records are transformed.
For each input, you can produce as many key-value pairs as you want.
In the reduce phase, pairs with the same key are collected and combined.
The implementation of the _reduce_ phase is also up to you.

## Hello world example: word count

The "Hello, world" example of MapReduce is counting distinct words in a large file.
So large it spans across hundreds of disks.
In the _map_ phase, for each line, we produce one pair for each distinct word found on that line.
Key is the word and value is simply number _one_.
One occurrence of a given word.
Then the MapReduce framework shuffles the data around so that pairs for the same key are transferred to the same node.
At this point the reduce phase kicks in.
Its responsibility is to merge, summarize pairs for the same key.
In our case it's simple: sum up values for each key individually.

## Advantages

The _map_ and reduce phases are trivial to implement.
The most complex part is provided by the framework, like Hadoop.
It's shuffling.
Shuffling sorts and moves data around the cluster.
This allows grouping, summarizing and sorting input.
Shuffling can also be the most time consuming and network intensive operation.

That's one of the reasons of MapReduce's success.
Writing _map_ and _reduce_ code is fairly straightforward.
The heavy-lifting of moving data around is done for us.
Also MapReduce implementation monitors for failures.
If either step fails due to node failure, it is repeated somewhere else.
Especially the _map_ phase is trivial to parallelize, so MapReduce jobs scale really well.
If all you need is to perform a single, independent action on each record, MapReduce works like a charm.
For example, a bank sending personalized PDF statements to tens of millions of customers.
You could write a `for` loop for that.
Yet, MapReduce adds almost unlimited parallelism and seamlessly handles failures.

Last, but not least, frameworks like Hadoop try really hard to run jobs locally.
What does it mean?
Data is typically distributed on hundreds, if not thousands of disks.
Hadoop tries to run mappers on the same machine as input data.
Or at least on the 
same datacenter rack.
Also, one can implement an additional so-called `Combiner`.
This piece of code is similar to the _reducer_, but runs locally.
Thanks to this, shuffling transfers preaggregated data.
And we save a lot of bandwidth. 

## Disadvantages

So if MapReduce is so awesome, why is Google no longer actively using it?
Turns out this simplistic approach of two steps, _map_ and _reduce_ is... too simplistic.
Distributed `for` loop, counting words, simple aggregations - these are straightforward.
But trying to implement something more sophisticated becomes cumbersome.
Often we must pipeline multiple MapReduce jobs.
The output of the first one becomes the input of the second one.
And so on.
The programming model is simply too low-level.
For example, Apache Hive supports SQL-like queries over big data.
Underneath it produces Hadoop jobs on the fly for you.
These days more elegant and expressive frameworks are popular.
Most commonly: Spark.

# More materials

* [MapReduce](https://en.wikipedia.org/wiki/MapReduce) on Wikipedia
* [How Hadoop Works Internally – Inside Hadoop](https://data-flair.training/blogs/how-hadoop-works-internally/)
* [Hadoop Combiner – Best Explanation to MapReduce Combiner](https://data-flair.training/blogs/hadoop-combiner-tutorial/)
* [Apache Hive](https://cwiki.apache.org/confluence/display/Hive/Home)

## MapReduce at Google
* [MapReduce: Simplified Data Processing on Large Clusters](https://research.google/pubs/pub62/) - the original whitepaper
* [Why did Google stop using MapReduce and start encouraging Cloud Dataflow?](https://www.quora.com/Why-did-Google-stop-using-MapReduce-and-start-encouraging-Cloud-Dataflow)
* [Google Dumps MapReduce in Favor of New Hyper-Scale Analytics System](https://www.datacenterknowledge.com/archives/2014/06/25/google-dumps-mapreduce-favor-new-hyper-scale-analytics-system/)



