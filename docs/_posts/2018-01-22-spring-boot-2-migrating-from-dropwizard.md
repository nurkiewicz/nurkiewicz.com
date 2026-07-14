---
layout: post
title: 'Spring Boot 2: Migrating from Dropwizard metrics to Micrometer'
date: '2018-01-22T19:30:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- spring boot
- spring
- Micrometer
modified_time: '2018-01-25T09:17:21.728+01:00'
thumbnail: /assets/img/spring-boot-2-migrating-from-dropwizard/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4472987463344789373
blogger_orig_url: https://www.nurkiewicz.com/2018/01/spring-boot-2-migrating-from-dropwizard.html
---

Spring Boot 2 is around the corner.
One of the minor changes is the replacement of [Dropwizard Metrics](http://metrics.dropwizard.io/) with [Micrometer](http://micrometer.io/).
The migration path is fairly straightforward and Micrometer actually provides cleaner API.
With Metrics, you have to inject `MetricRegistry` wherever you need some metrics (see: [Monitoring and measuring reactive application with Dropwizard Metrics](http://www.nurkiewicz.com/2018/01/monitoring-and-measuring-reactive.html)).
This has many drawbacks:

- we are mixing business and technical dependencies in our components
- therefore I am sometimes reluctant to add new metrics because it requires me to inject `MetricRegistry`
- also `MetricRegistry` must be stubbed in unit tests

Micrometer's tagline is:

*Think SLF4J, but for metrics*

It's actually quite accurate.
Whenever I need a `Logger` I don't inject `LoggerFactory`, instead I simply use static methods available everywhere.
The same goes for Micrometer, I simply use static factory methods on globally available `Metrics` class:

```java
private final Timer indexTimer = Metrics.timer("es.timer");
private final LongAdder concurrent = Metrics.gauge("es.concurrent", new LongAdder());
private final Counter successes = Metrics.counter("es.index", "result", "success");
private final Counter failures = Metrics.counter("es.index", "result", "failure");
```

That's it!
You can put metrics anywhere you like without polluting your constructor with `MetricRegistry`.
The API is very similar, e.g.:

```java
concurrent.increment()
```

One major difference is gauges vs. counters.
In Dropwizard Metrics counters can go up and down whereas in Micrometer counter must increase monotonically.
I [thought](https://github.com/micrometer-metrics/micrometer/pull/318) it's a bug...
Counter is used in simple scenarios like counting how many requests succeeded.
So how can we measure things like the number of concurrent requests or queue length?
With gauges, but it's slightly convoluted.

Did you notice how `Metrics.gauge()` takes a `new LongAdder()` as an argument?
And returns it?
This way we create a gauge that track (by periodically polling for value) any instance of `Number` class (e.g.
`AtomicLong` or `LongAdder`).
We can modify the returned `LongAdder` and its current value will be reflected by the gauge.
Neat!
Moreover, there are helper methods like `gaugeCollectionSize()` and `gaugeMapSize()` that take any `Collection` or `Map` respectively - and are quite self-explanatory.

## Built-in JVM metrics

Micrometer also has a bunch of built-in system and JVM metrics, for example:

- `LogbackMetrics` - number of log messages per each log level.
  You can watch e.g. error rate
- `ProcessorMetrics`- average system load
- `JvmMemoryMetrics` - memory usage, split by area
- `JvmThreadMetrics` - number of thread (live, daemon, peak...)
- `JvmGcMetrics` - GC promotion rate, etc.

Most of these are registered by default by Spring Boot.
The last two of them [will be available](https://github.com/spring-projects/spring-boot/pull/11425) as well.
By having all these metrics we can actually enhance our dashboard quite a bit:

[![](/assets/img/spring-boot-2-migrating-from-dropwizard/1.png)](/assets/img/spring-boot-2-migrating-from-dropwizard/1.png)

The dashboard definition for Grafana is available [on GitHub](https://github.com/nurkiewicz/elastic-flux/blob/micrometer/src/main/docs/grafana-elastic-flux-micrometer.json).
Notice how this application uses about 100 MiB of RAM while sustaining almost two thousand concurrent connections (!)
Also less than 45 live threads compared to thousands of concurrent connections is impressive.

It's worth mentioning that the setup of Micrometer in Spring Boot is really simple.
First, add the appropriate dependency:

```groovy
compile 'io.micrometer:micrometer-registry-graphite:1.0.0-rc.5'
```

and a bunch of configuration parameters.
Zero code:

```yaml

spring.metrics.export.graphite:
  host: graphite
  port: 2003
  protocol: Plaintext
  step: PT1S
```

In the last part of this short series, we will wrap everything together in a Spring Web Flux application.

This is part of a longer series:

- [Spring, Reactor and ElasticSearch: from callbacks to reactive streams](http://www.nurkiewicz.com/2018/01/spring-reactor-and-elasticsearch-from.html)
- [Spring, Reactor and ElasticSearch: bechmarking with fake test data](http://www.nurkiewicz.com/2018/01/spring-reactor-and-elasticsearch.html)
- [Monitoring and measuring reactive application with Dropwizard Metrics](http://www.nurkiewicz.com/2018/01/monitoring-and-measuring-reactive.html)
- Spring Boot 2: Migrating from Dropwizard metrics to Micrometer
- [Spring Boot 2: Fluxes, from Elasticsearch to controller](http://www.nurkiewicz.com/2018/01/spring-boot-2-fluxes-from-elasticsearch.html)
