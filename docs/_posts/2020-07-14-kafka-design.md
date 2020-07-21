---
title: "#8: Kafka's design"
permalink: /8
tags: kafka sendfile tail partitioning
description: >
    Kafka is not a message broker.
    However, it can be used as such very effectively.
    Instead, I'd like to think about as a very peculiar database.
    A database where inserts are insanely fast and sequential reads are preferred and very fast as well.
    Also there is very little support for deleting and updating data. In this episode I am focusing on the architecture and internals of Kafka.
    The best way to understand Kafka is by examining how it works.

---

{% include player.html %}

{{ page.description }}

# More materials

* [`sendfile` in Java](https://docs.oracle.com/javase/9/docs/api/java/io/InputStream.html#transferTo-java.io.OutputStream-)
* [How LinkedIn customizes Apache Kafka for 7 trillion messages per day
](https://engineering.linkedin.com/blog/2019/apache-kafka-trillion-messages)

{% include newsletter-input.md %}
