---
title: "OpenTelemetry glossary: 30 terms you should know"
tags: observability OpenTelemetry monitoring Grafana Prometheus
layout: post
image: telemetry-glossary/opentelemetry-glossary.png
description: >
    A glossary of OpenTelemetry and observability terms, from traces and spans to Grafana and Datadog.
    Opinionated definitions for developers who don't have time for dry documentation.
---

If you've ever stared at a Grafana dashboard pretending to understand what's going on - this post is for you.
Observability is one of those areas where everyone nods along in meetings but secretly Googles half the terms afterwards.
I've been that person.
More than once.
The following is a glossary of the most important observability and OpenTelemetry concepts.

Observability
: The ability to understand what's happening inside your system by examining its external outputs.
Unlike traditional monitoring, where you define upfront what to watch, observability lets you ask arbitrary questions about your system's behavior *after the fact*.

Trace
: The complete journey of a single request as it travels through your distributed system.
It starts when a user clicks a button and ends when the response comes back, capturing every service, database call, and queue hop along the way.
Without traces, debugging a slow request in a microservices architecture is like finding a needle in a haystack.
I covered this topic in detail in my podcast about [distributed tracing](https://nurkiewicz.com/48).

Span
: A single unit of work within a trace.
Like one leg of a relay race.
Each span records a specific operation: an HTTP call, a database query, or a message being published.
Spans are nested - a parent span for handling an HTTP request may contain child spans for authentication, business logic, and persistence.
What you see on the header picture is a single trace with hundreds of spans.
Each horizontal bar is a span.

Context propagation
: The mechanism that links related operations across service boundaries.
When service A calls service B, context propagation injects trace identifiers into the request (usually as HTTP headers like W3C `traceparent`).
Service B extracts them and continues the same trace.
Without this, you'd have isolated spans with no way to stitch them into a complete picture.
It's the glue that makes distributed tracing *distributed*.

Metric
: A numeric measurement collected over time: request count, error rate, CPU usage, queue depth.
Metrics are cheap to store and query, making them perfect for dashboards and alerting.
They tell you *that* something is wrong, but rarely *why*.
That's where traces and logs come in.

Log
: A discrete event recorded by your application at a specific point in time.
The oldest and most familiar form of observability data.
Every developer has written a `log.info()` at some point.
The challenge isn't producing logs - it's making them searchable and correlated with traces and metrics.
Logging at scale is serious business.

Structured logging
: Logging where each entry is a set of key-value pairs rather than a free-form string.
Instead of `"User 42 logged in from 192.168.1.1"`, you emit `{event: "login", userId: 42, ip: "192.168.1.1"}`.
This makes logs machine-parseable, filterable, and actually useful at scale.
`grep` doesn't cut it when you process terabytes of logs daily.

Backend
: The system that receives, stores, and lets you query your telemetry data.
Jaeger, Prometheus, Datadog, Grafana Tempo - these are all backends.
Your application produces traces, metrics, and logs.
The backend is where they end up and where you actually go to make sense of them.

OpenTelemetry (OTel)
: A vendor-neutral, open-source observability framework for generating, collecting, and exporting telemetry data.
It provides APIs, SDKs, and tools for all three pillars: traces, metrics, and logs.
Instrument your code once, send data to any backend you choose.
If you learn only one thing from this glossary, let it be OTel.

OTLP (OpenTelemetry Protocol)
: The native wire protocol for transmitting telemetry data in OpenTelemetry.
OTLP defines how traces, metrics, and logs are encoded and transported - typically over gRPC or HTTP.
Most backends accept OTLP directly nowadays, which means you can often skip format-specific exporters entirely.
One protocol to rule them all.

OpenTelemetry instrumentation
: The process of adding observability to your application using OTel's APIs and SDKs.
Auto-instrumentation can inject tracing into popular frameworks (Spring Boot, Express, Django) with zero code changes.
Feels like magic, and mostly works.
Manual instrumentation gives you finer control - adding custom spans, attributes, or metrics where the automatic approach falls short.

OpenTelemetry Collector
: A vendor-agnostic proxy that receives, processes, and exports telemetry data.
Instead of configuring each application to send data directly to your backend, you route everything through the Collector.
It decouples your instrumentation from your backend choice and lets you transform, filter, or enrich data in transit.
Switching from Jaeger to Tempo?
Change the Collector config.
Your applications don't need to know.

Receiver
: The Collector component that ingests telemetry data from your applications.
Receivers support various protocols and formats: OTLP, Jaeger, Zipkin, Prometheus, and many more.
You can run multiple receivers simultaneously, which is invaluable when migrating from one instrumentation library to another.
Migration without downtime.

Processor
: The middle layer of the Collector pipeline that transforms data between receiving and exporting.
Processors can batch data for efficiency, filter out noisy spans, sample only a percentage of traces, or enrich telemetry with additional attributes.
Order matters.
Processors execute sequentially, and a poorly placed filter can drop data before it gets enriched.

Exporter
: The Collector component that sends processed telemetry to your backend of choice.
Exporters exist for virtually every observability platform: Jaeger, Prometheus, Datadog, Splunk, you name it.
You can even configure multiple exporters simultaneously - send traces to Jaeger for debugging and to long-term storage for compliance.
Why choose?

Connector
: A relatively new Collector component that acts as both an exporter and a receiver, bridging two pipelines.
A connector can analyze incoming spans and generate metrics from them - counting errors or measuring latency without separate instrumentation.
Deriving one signal from another.

APM (Application Performance Monitoring)
: A broad category of tools that monitor and manage the performance and availability of your applications.
APM solutions typically combine traces, metrics, and logs into a unified experience with dashboards, alerting, and root cause analysis.
Every vendor defines APM slightly differently, but the goal is always the same: know when your app is slow or broken, and understand *why*.

Prometheus
: The de facto standard for metrics collection in the cloud-native world.
Prometheus uses a pull model - it *scrapes* metrics from your applications at regular intervals, rather than waiting for them to be pushed.
Its query language, PromQL, is powerful but has a learning curve that makes regex look approachable.

Grafana
: A visualization and dashboarding platform that can display data from virtually any source.
Grafana doesn't store data itself - it connects to Prometheus, Loki, Tempo, and dozens of other backends.
If Prometheus is the engine, Grafana is the dashboard on your car.
Pretty, informative, and the part everyone actually looks at.

![Grafana dashboard based on Node Exporter Full pre-made template](/assets/img/telemetry-glossary/grafana-dashboard.png)
*Dashboard based on [Node Exporter Full](https://grafana.com/grafana/dashboards/1860-node-exporter-full/) pre-made template*

Loki
: A log aggregation system, inspired by Prometheus.
Unlike Elasticsearch, Loki indexes only metadata (labels) rather than the full text of log lines.
Much cheaper to operate.
The trade-off?
Full-text search is slower.
But in practice, filtering by labels and then scanning is fast enough for most use cases.

Tempo
: A distributed tracing backend, designed for massive scale at minimal cost.
Tempo stores traces in object storage (like S3) without requiring any indexing infrastructure.
The catch: you need a trace ID to look up a trace.
But integrations with Loki and Grafana make discovery seamless, so it's less of a problem than it sounds.

Jaeger
: An open-source distributed tracing platform, originally built by Uber.
Jaeger helps you visualize request flows and latency bottlenecks in complex distributed systems.

Zipkin
: One of the earliest open-source distributed tracing systems, inspired by [Google's Dapper paper](https://research.google/pubs/dapper-a-large-scale-distributed-systems-tracing-infrastructure/).
Zipkin pioneered many concepts that are now standard, including the B3 propagation format - a set of HTTP headers (`X-B3-TraceId`, `X-B3-SpanId`, etc.) that carry trace context between services.
Still actively maintained and has a loyal following, though newer tools have captured more mindshare.

Mimir
: A highly scalable, long-term storage backend for Prometheus metrics.
Prometheus is great for short-term storage, but Mimir can handle months or years of metrics data across multiple tenants.

Thanos
: Another approach to scaling Prometheus, focused on long-term storage and global querying across multiple Prometheus instances.
Thanos sits *alongside* your existing Prometheus servers and uploads their data to object storage, providing a unified query layer.
If Mimir *replaces* Prometheus, Thanos *extends* it.

Alloy
: Open-source telemetry collector, previously known as Grafana Agent.
Collects metrics, logs, traces, and profiles, then ships them to your backends.

Pyroscope
: A continuous profiling platform.
While traces tell you *where* time is spent across services, Pyroscope tells you *where* time is spent *within a single process* - down to the function and line of code.
Some call profiling the "fourth pillar" of observability.
I'd say the jury is still out, but Pyroscope makes it accessible in production without significant overhead.

![Pyroscope dashboard in Grafana](/assets/img/telemetry-glossary/pyroscope-dashboard.png)
*Source: [Grafana Pyroscope documentation](https://grafana.com/docs/grafana/latest/datasources/pyroscope/)*

Commercial APM platforms ([Datadog](https://www.datadoghq.com/), [Splunk](https://www.splunk.com/), [New Relic](https://newrelic.com/))
: Full-stack observability solutions that bundle metrics, traces, logs, dashboards, and alerting into a single managed product.
They all solve the same problem: you don't want to run your own observability infrastructure.
The trade-off is cost and vendor lock-in.
OpenTelemetry helps with the lock-in part - instrument once, switch backends later.

ELK Stack (Elasticsearch, Logstash, Kibana)
: The classic open-source trio for log management.
Elasticsearch stores and indexes, Logstash ingests and transforms, Kibana visualizes.
For years, ELK was *the* answer to "where do I search my logs?"
Powerful, but running Elasticsearch at scale is practically a full-time job.
The Grafana stack (Loki + Grafana) is a lighter alternative - Loki skips full-text indexing, which trades search flexibility for much lower operational cost.
ELK predates OpenTelemetry and focuses primarily on logs, while OTel covers all three signals and is backend-agnostic.
That said, you can absolutely feed OTel data into Elasticsearch.

Kibana
: The visualization layer of the Elastic Stack (formerly ELK: Elasticsearch, Logstash, Kibana).
Provides dashboards and exploration tools for data stored in Elasticsearch, particularly logs.
While Grafana has become the default for metrics, Kibana remains the go-to for teams heavily invested in Elasticsearch.

---

## Further reading

* [Demystifying OpenTelemetry](https://opentelemetry.io/blog/2026/demystifying-opentelemetry/)
