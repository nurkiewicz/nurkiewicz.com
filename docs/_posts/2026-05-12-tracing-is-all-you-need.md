---
title: "Tracing is all you need. Especially if costs don't matter"
tags: observability OpenTelemetry tracing Grafana Alloy
layout: post
description: >
    Traces can theoretically replace metrics and logs. But the cost of unsampled traces is enormous, and sampling destroys the very property that makes traces a single source of truth.
---

There's a seductive idea floating around observability circles: traces are the one true signal.
Metrics? Just aggregate your spans.
Logs? Span events with extra steps.
Instrument once, derive everything.
It's elegant.
It's architecturally beautiful.
It's also a trap.

## The beautiful theory

A span already carries timestamp, duration, status, attributes.
Count spans — request rate.
Histogram of durations — latency percentiles.
Filter by `error=true` — error rate.
That's your RED metrics, derived for free.

OTel Collector's spanmetrics connector does exactly this.
Servicegraph connector gives you a dependency map.
Span events become log lines in Loki.
One pipeline, three signals.

No more drift between what metrics say and what traces show.
Single source of truth.
The dream.

## The catch-22

A single HTTP request produces 10-50 spans.
Each span carries attributes, events, links.
At 10K requests/second, that's half a million spans per second.
Your observability backend now costs more than the system it observes.

The obvious fix: sampling.
Keep 1% of traces.
Problem solved?

No.
Because you just destroyed the entire premise.
Metrics derived from 1% of spans aren't metrics — they're estimates with terrifying confidence intervals.
You can't alert on a counter that undercounts by 99%.

Head-based sampling decides at the start — coin flip, you might drop the one trace explaining the 3 AM incident.
Tail-based sampling buffers entire traces in memory before deciding.
Better, but now you need infrastructure to hold millions of in-flight spans.

The premise is internally contradictory: unsampled traces give you accurate derived metrics but bankrupt you.
Sampled traces are affordable but useless as a metrics source.

## What actually works (the boring middle ground)

Metrics stay metrics.
Cheap, pre-aggregated, 100% of traffic.
Alert on these.

Traces are sampled.
1-5% head-based, or tail-based keeping errors and slow requests.
Debug with these.

Logs for what doesn't fit a request: startup, cron jobs, background workers.

Alloy/OTel Collector as the router: receives OTLP from your apps, sends metrics to Mimir, traces to Tempo, logs to Loki.
Three backends, one collector, no magic derivation.

Spanmetrics connector is still useful — but as a *supplement*, not a replacement.
It gives you per-endpoint latency breakdowns you might not have instrumented explicitly.
Don't rely on it for alerting.

## Conclusion

"Tracing is all you need" is the observability equivalent of "we'll rewrite it in Rust."
Technically sound, economically delusional.
The boring answer — separate signals for separate purposes — exists for a reason.
Your CFO will thank you.
