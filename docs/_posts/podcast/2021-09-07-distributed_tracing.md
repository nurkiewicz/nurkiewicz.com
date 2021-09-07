---
title: "#48: Distributed tracing: find bottlenecks in complex systems"
category: podcast
permalink: /48
tags: zipkin jaeger microservices span trace opentracing opentelemetry kibana
description: >
    Life used to be simple.
    In a traditional monolithic application, when a failure occurred, you could easily find the problem.
    When an exception bubbles up, it appears throughout all stack frames.
    You can easily examine which methods or functions were invoked from each other.
    You can see application layers involved.
    Moreover, it's fairly easy to profile performance bottlenecks.
    Answering these questions becomes much harder when there are multiple systems involved.
---

{% include player.html episode_id="6ArAEK4X6mmjhyx79QIsgS" %}

{{ page.description }}

<!--
In a distributed system, a failure in one component may be caused by problems several services away.
For example, your Python backend returned HTTP 503 to the browser.
What happened?
If all you had was this Python application, looking through the logs should be enough.
It's all visible on the stack trace.
Moreover, you can see which functions led to the invocation of a broken code.
No wonder in Python it's often called `traceback`.
You can trace back what happened!

But what if this Python backend is just a gateway, orchestrating tens of other services?
You go to your logs.
You see that an error was caused by another error when calling, let's say, `user-service`.
OK...
So you go to the logs of a `user-service`, whatever it is.
Indeed, it was calling `token-service` and it timed-out waiting for a response.
Looking through the logs of a `token-service` shows, sadly... nothing.
I mean, there are thousands of logs per second and no errors.
Seriously.
You carefully correlate logs by time.
You ask yourself, why, on earth, `token-service` uses Australian time zone?
Nevermind.

Just by pure luck you realize that `token-service` makes a call to `token-verifier`, OAuth authentication endpoint and some SQL database.
The SQL query is apparently slow.
`token-service` itself returns successfully.
However, too late.
`user-service` no longer waits for its response, timing out.
That leads to an error in Python backend and broken frontend.
As you can see, this process is insanely tedious and relies on luck and intuition.

Now, imagine every request, starting from the Python all the way down to the database, had some unique identifier.
Let's call that a span ID.
All requests within one transaction also share a single trace ID.
These two IDs are forwarded inside every HTTP request/response.
In fact, it can work for other technologies, like message brokers.
So, what's the point?
First of all, assume you collect all application logs in one central place like Kibana.
Knowing a trace ID where an error occurred you can find all logs from all services that contributed to that error.
As if all services were invoked within one unique thread.

But it gets better.
Each trace consists of multiple spans.
Span can have a parent span, start and end timestamps.
Therefore, you can reconstruct the hierarchy of callers easily.
Even better, you can see which spans run concurrently, and which ones are exceptionally slow.
In our example it would've been obvious what is the root cause by simply visualising the trace and spans.
Because spans are collected from multiple machines, it's called *distributed tracing*.

Keep in mind that collecting and aggregating traces in a busy system is no easy task.
So, often only a fraction of traces are stored.
Moreover, specialized software and databases like Zipkin and Jaeger is used to quickly search through data.

That's it, thanks for listening, bye!
-->

# More materials

* [Distributed tracing: A complete guide](https://lightstep.com/distributed-tracing/)
* [#36: Microservices architecture: principles and how to break them](https://nurkiewicz.com/36)
* [GraphQL server in Java: Part III: Improving concurrency](https://nurkiewicz.com/2020/03/graphql-server-in-java-part-iii.html) - tracing in a real-world scenario
* [Pattern: Distributed tracing](https://microservices.io/patterns/observability/distributed-tracing.html)
* [OpenTracing](https://opentracing.io/) and [OpenCensus](https://opencensus.io) got merged to become [OpenTelemetry](https://opentelemetry.io/)
* [Zipkin](https://zipkin.io/) is a distributed tracing system
* [Jaeger](https://www.jaegertracing.io/): open source, end-to-end distributed tracing
* [Zipkin vs Jaeger: Getting Started With Tracing](https://logz.io/blog/zipkin-vs-jaeger/)
* [W3C `tracing-context`](https://www.w3.org/TR/trace-context/)
* [`traceback`](https://docs.python.org/3/library/traceback.html) in Python
