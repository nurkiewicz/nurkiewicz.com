---
title: "#12: Continuous integration, delivery and deployment"
permalink: /12
tags: CI CD canary-deployment ab-testing
description: >
    Typically, more than one developer is working on the same codebase.
    How do they share their work?
    The simplest approach is a common Dropbox folder.
    This has several drawbacks, mainly we risk breaking other's work with our half-done features.
    So we come up with version control systems.
    There we only commit code when all changes are done.

---

{% include player.html episode_id="0yhni9TICTBT8zBbnTwjJA" %}

{{ page.description }}


# The problem

Some developers take it to the extreme.
They work on their branch for weeks or even months, without showing the results of their work.
This is quite common.
A developer hides in the closet for weeks, making tons of changes that only he/she sees.
After a month or two changes are merged, wreaking havoc.
Large refactorings, reorganized code structure, changed database schema.
You name it.
Suddenly a huge feature appears out of the blue in the `master`.
This is problematic for two reasons:

* other developers may find it hard to incorporate changes into their features
* deploying such large features is often troublesome

Simply put: conflicts and broken production.

# Merge more often

The solution seems simple: merge more often.
Continuous integration basically means merging your changes several times a day back to `master`.
So how's it different to simply working on `master` all the time?
Well, continuous integration comes with some discipline.
First of all, our version control needs to be capable of atomic commits and easy branching/merging.
Secondly, every commit needs to be built and tested automatically.
Otherwise it's too easy to merge code that doesn't compile or with failing tests.
Other quality gates are a bonus.

This way whenever you branch of off `master`, you are guaranteed to have very recent codebase.
Without continuous integration you might be working on a version that's very outdated.
Also, long-living branches that you are not aware of, may contain valuable changes.
Refactorings, performance optimizations, documentation updates.
Things that were needed for a particular feature, but everyone can benefit from them.

# Continuous delivery

All right, so it seems you can integrate your changes to `master` multiple times a day.
You even have mechanisms to prevent broken code and regressions.
When's the right time to deploy to production?
Always!
Any time you or your manager wants.
Moreover, it should be so simple that even your manager can deploy to production!
Every new feature or bugfix, if it's on `master`, _may_ be deployed at any time.
This encourages frequent deployments.
However, the deployment process must be fully automated and bullet-proof.
Building, applying configuration, avoiding downtime.
The last one is especially interesting, but easy to implement.
When deploying a new version, just keep the old one running, until the new version warms up.
Stacks like Kubernetes do this by default.
Typically, such an automated pipeline is orchestrated using tools like Jenkins or Bamboo.
There is still space for some manual verification.
But in general anyone can simply deploy with a single click.

# Continuous deployment

Continuous deployment takes this idea to the extreme once again.
If everything on `master` branch can be deployed at any time, why not deploy it immediately?
You hear it right, every commit to `master` is deployed to production straight away.
Obviously, there are unit, integration and end-to-end tests.
There are automated sanity checks.
There are A/B tests, canary deployments, etc.
But in principle, if something managed to get into `master`, it's automatically deployed to production.
Maybe several times a day.
Many organisations fear deployments on Friday or during peak season.
Smarter companies understand that bugfixes or new features are especially wanted during Black Friday.
Why wait if we have something great that passed all the tests?

# More materials

* [Velocity 09: John Allspaw and Paul Hammond: 10+ Deploys Per Day: Dev and Ops Cooperation at Flickr](https://www.youtube.com/watch?v=LdOe18KhtT4)
* [Continuous integration](https://en.wikipedia.org/wiki/Continuous_integration) on Wikipedia
* [Continuous delivery](https://en.wikipedia.org/wiki/Continuous_delivery) on Wikipedia
* [Continuous deployment](https://en.wikipedia.org/wiki/Continuous_deployment) on Wikipedia
* [Togglz](https://www.togglz.org/): Feature Flags for the Java platform
* [18 - Continuous Delivery & efficient workflows](https://anchor.fm/effective-developer/episodes/18---Continuous-Delivery--efficient-workflows-ehosqu) on _The Effective Developer_ podcast

{% include post-footer.md %}
