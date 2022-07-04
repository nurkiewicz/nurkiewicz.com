---
title: "#76: 12th Factor App: portable and resilient services start here. Part 8-12/12"
category: podcast
permalink: /76
tags: 12th-factor Heroku microservices terraform kubernetes logging Terraform Docker testcontainers Logstash Splunk DataDog
description: >
    In part 2 of the Twelve-Factor App, we'll explore the second half of the principles.
    Be sure to listen to the previous episode as well.
    We still have only four minutes, so let's go!
---

{% include player.html spotify_id="5i2IYlEgtz7RcWTVKvVNSH" youtube_id="ldzltWr_HM4" %}

{{ page.description }}

## VIII. Scale out via the process model

This principle encourages scaling out by spawning multiple instances of the same application.
While scaling up through thread or in-process workers is still an option, scaling out is more useful.
And guess what?
This is exactly what orchestrators like Kubernetes do.
If your application is running out of resources, it's simply scaled out to more instances.
It may also be cheaper to run multiple small servers vs. one huge.
But don't take that for granted.

## IX. Maximize robustness with fast startup and graceful shutdown

An application should start and shut down fast.
Some frameworks make it easy, others require several minutes before the app is ready.
Why is this important?
It's all about agility.
Fast restart or redeploy means you can revert a broken version quickly.
Also, configuration changes can be applied faster.
Some developers try to dynamically reload configuration without restarting.
From my experience it's error-prone.

## X. Keep development, staging, and production as similar as possible

This principle actually touches many disparate things.

First of all, all environments should be similar.
With infrastructure as code, this is a no-brainer.
You just run Terraform with a different configuration parameter and boom!
Your staging or second preproduction environment is live.
Or with Kubernetes, you can build a single-node cluster on your machine.

Secondly, we should aim for continuous integration and deployment.
CI/CD allows delivering software faster, from a developer machine to production.

Thirdly, applications running locally should avoid in-memory stubs and fakes of dependencies.
Like SQLite database locally instead of MySQL running on prod.
This used to be problematic.
Now we have Docker and testcontainers.

## XI. Treat logs as event streams

This sounds abstract until you realize it's about separating responsibilities.
Your app should print logs to the console and forget about them.
Some supervisors, like Logstash, Splunk or DataDog should take care of them.
This means reading, parsing, pushing to some external server and aggregating.

Log files on file system have two drawbacks:

* file system is transient, so you should not rely on it at all
* searching is limited to a single instance of a single app.

With aggregated logging, you can trace transactions even across services.

## XII. Run admin/management tasks as one-off processes

The application should not run maintenance, one-off batch jobs on its own.
Instead, they should be externalized.
This makes a lot of sense.
Too many times I saw a single instance of an application being overutilized simply because it was running some batch jobs in the background.

On the other hand, this principle also covers database migrations.
In some scenarios, I actually find it useful to run a migration together with an application.
This way I'm sure I won't forget about added columns or constraints.
However, migrations unnecessarily slow down and lock the deployment.

These were twelve principles defined back in 2011.
Some of them are less relevant these days.
Others became a de-facto standard.
Anyway, it's worth knowing them.
Feel free to break some of these rules intentionally, rather than accidentally.

That's it, thanks for listening, bye!

# More materials

* [Official website](https://12factor.net/)
* [Twelve-Factor App methodology](https://en.wikipedia.org/wiki/Twelve-Factor_App_methodology) on Wikipedia
* Tools:
    * [testcontainers](https://www.testcontainers.org/)
    * [Kubernetes](https://nurkiewicz.com/46)
    * [Terraform](https://nurkiewicz.com/47)
* Log aggreagation:
    * [Logstash](https://nurkiewicz.com/63)
    * [Splunk](https://docs.splunk.com/Documentation/Splunk/latest/AdvancedDev/ModInputsLog)
    * [DataDog](https://www.datadoghq.com/knowledge-center/log-aggregation/)
