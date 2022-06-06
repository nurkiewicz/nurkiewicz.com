---
title: "#75: 12th Factor App: portable and resilient services start here. Part 1-7/12"
category: podcast
permalink: /75
tags: 12th-factor Heroku microservices
description: >
    Twelve-Factor App is a set of design guidelines defined by Heroku.
    These guidelines are best suited for cloud-native, portable and resilient services.
    In this episode, I'll explain the first seven principles.
    I have four minutes left, so let's go!
---

{% include player.html episode_id="6DY7TcuO082kCzmAa5uRKU" %}

{{ page.description }}

## I. One codebase tracked in revision control, many deploys

It means that there should only be one version of your codebase deployed to all environments.
Having a separate artefact (DLL, ZIP, executable) for stage and production is an anti-pattern.
It leads to irreproducible bugs and less confidence.
After all, what you test on staging should be the same as what you run on production.
Of course, external configuration differs.

## II. Explicitly declare and isolate dependencies

Your application should not rely on third-party dependencies in the operating system.
You should not expect certain packages, libraries or utilities to exist on the server.
Your application should be self-sufficient.
Some programming languages, like Java, have you covered.
They package all dependencies inside a single archive.
Other languages, like Python or Ruby, may implicitly depend on system-wide packages.

Of course, you still need Python, Ruby or PHP interpreters.
Containers encapsulating the runtime help a lot.

## III. Store config in the environment

This one is slightly outdated.
The configuration should indeed be externalized.
Credentials and API endpoints should not exist in the codebase.
On the other hand, environment variables are not the only way to inject environment-specific configuration these days.

## IV. Treat backing services as attached resources

This one is a bit cryptic.
But the principle is simple.
Services that you rely upon, like databases or APIs, should be easy to configure and swap.
For example, replacing in-house MySQL with a managed one.
Or a local e-mail service with an external one.
These days APIs are so pervasive that it's actually hard to break this rule.

## V. Strictly separate build and run stages

This one is a no-brainer.
The software lifecycle must go through building, *then* releasing and *then* running on subsequent environments.
There is no bypass and no turning back.
How could you break this rule?
Well, simply build your application locally and deploy it straight to production.
Or, login to your production server and modify PHP or Python files directly.
This is a big anti-pattern.

## VI. Execute the app as one or more stateless processes

This one is important!
An application should not treat the file system as permanent storage.
It's best to avoid the file system altogether.
These days apps are restarted and redeployed on ephemeral servers all the time.
File system is simply not persistent enough.
Treat it like a large, slow memory instead.
If you need persistent storage, use an external database.
Preferably a managed one.

Also, every time you touch these spinning plates, you risk remote code execution and path traversal vulnerabilities.
That being said, we sort of standardized on immutable containers.
So we get isolation out of the box.

## VII. Export services via port binding

HTTP became a de-facto standard for service communication.
So this principle is kind of obvious.
However, there are some simple ways to break this rule.
For example, a file system is shared between services.
Or the same database accessed by different applications.

OK.
We'll explore the second half of these principles in the next episode.
That's it, thanks for listening, bye!

# More materials

* [Official website](https://12factor.net/)
* [Twelve-Factor App methodology](https://en.wikipedia.org/wiki/Twelve-Factor_App_methodology) on Wikipedia
