---
title: "#65: Zero Downtime deployment"
category: podcast
permalink: /65
tags: devops blue-green canary kubernetes
description: >
    Remember the days when deploying a new version of your application required downtime?
    If your application is particularly important, you might have had to schedule a maintenance window.
    Or perform the deployment in the middle of the night to avoid disruption.
    Today's tools and DevOps practices allow deploying tens or even hundreds of times per day.
    With no downtime, and no noticeable disruption.
    Sometimes every commit is deployed automatically to production within minutes.
    How's all this possible?
---

{% include player.html episode_id="6clYLaFhwkV2j2MCIV2T90" %}

{{ page.description }}

<!--
A typical old-school process looked as follows:

1. Stopping the production server
2. Overwriting old binaries with the new ones
3. Starting the production with the new server

Many of these steps are performed manually or by some hand-written scripts.
Many of these steps can fail.
And when they do, you need to roll back.
This extends the downtime even further.

But even if everything goes smoothly, there's always this pesky period when production is down.
We don't want our users to be unhappy, so deployments are less and less common.
But the fewer deploys you have, the bigger they are.
And the more changes you deploy, the bigger the chances of failure.
So you deploy even less frequently.
Further increasing the risk.

Turns out, if it's painful, do it often!
Small, frequent deploys are less risky.
Not to mention we bring business value faster and get feedback sooner.
But how to minimize downtime, while deploying over and over again?

# Blue-green deployments

The first technique is called _blue-green_ deployments.
Imagine that you have twice as many servers.
Half of them, called _blue_, serve normal production traffic.
The other half, known as _green_, stays dormant.
When you deploy a new version, you simply deploy it to the _green_ environment.
The load-balancer in front doesn't route any traffic to _green_ servers.

But once they successfully start and you performed some manual or automated health checks...
Well...
We simply flip a switch in the load-balancer.
Suddenly all traffic is routed to the _green_ servers.
The _blue_ servers become obsolete and can be shut down.
If we encounter any error - we simply throw out the _green_ environment before switching.

Obviously, on subsequent deployment _blue_ and _green_ environments simply switch roles.
Notice that temporarily our application is deployed to twice as many servers and instances.
But if you live in the cloud, you don't need twice as much hardware all the time.
Only during deployment.

# Canary deployment

The second technique for deploying without downtime is called _canary deployment_.
It's similar but more fine-grained.
When deploying a new version, you deploy it to just a fraction of the servers.
Load-balancer routes a few per cent of traffic to canary - an instance of the new version.
If you don't encounter any bugs or performance issues, you gradually increase the percentage.

Keep in mind that with both techniques there are always some instances ready to serve the traffic.
Moreover, in case of deployment failure, very few users (if any) will notice.
Of course, there's quite a bit of extra complexity.
Luckily, modern DevOps tools like Kubernetes greatly simplify this common procedure.

That's it, thanks for listening, bye!

-->

# More materials

* [Canary vs blue-green deployment to reduce enterprise downtime](https://circleci.com/blog/canary-vs-blue-green-downtime/)
* [Deployment Frequency – A Key Metric in DevOps](https://humanitec.com/blog/deployment-frequency-key-metric-in-devops)
* [DevOps leaders deliver software 200 times more frequently than their peers, study shows](https://www.zdnet.com/article/devops-leaders-deliver-software-200-times-more-frequently-than-their-peers-study-shows/)
* [#12: Continuous integration, delivery and deployment](https://nurkiewicz.com/12)
* [#46: Kubernetes: Orchestrating large-scale deployments](https://nurkiewicz.com/46)
    * [https://codefresh.io/kubernetes-tutorial/fully-automated-blue-green-deployments-kubernetes-codefresh/](https://codefresh.io/kubernetes-tutorial/blue-green-deploy/)
    * [Canary deployment strategy for Kubernetes deployments](https://docs.microsoft.com/en-us/azure/devops/pipelines/ecosystems/kubernetes/canary-demo)
