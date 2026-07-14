---
layout: post
title: Breaking build is not a crime
date: '2013-02-02T22:38:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- git
- bamboo
- continuous integration
modified_time: '2013-02-02T22:38:27.339+01:00'
thumbnail: /assets/img/breaking-build-is-not-crime/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1818002603818858899
blogger_orig_url: https://www.nurkiewicz.com/2013/02/breaking-build-is-not-crime.html
---

For years I've been taught that breaking continuous integration build is something that should be avoided under all circumstances.
Let me first quote few classics.
*Uncle Bob* in [*The Clean Coder*](http://www.amazon.com/gp/product/0137081073/ref=as_li_ss_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=0137081073&linkCode=as2&tag=javaandneighb-20) says:

> The team must simply keep the build working at all times.
> If the build fails, it should be a “stop the presses” event and the team should meet to quickly resolve the issue.

and later in that section:

> I have every developer run the continuous-build script before they commit.

Final quote:

> They *(CI tests)* should never fail.
> If they fail, then the whole team should stop what they are doing and focus on getting the broken tests to pass again.
> A broken build \[...\]
> should be viewed as an emergency\[...\]

In another wonderful book [*Continuous Delivery*](http://www.amazon.com/gp/product/0321601912/ref=as_li_ss_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=0321601912&linkCode=as2&tag=javaandneighb-20) by *Jez Humble* and *David Farley* the authors go way further.
They present 7-point plan that we should follow on every commit (!):

> `3.`
> Run the build script and tests on your development machine to make sure that everything still works correctly on your computer
>
> \[...\]
>
> `5.`
> Wait for your CI tool to run the build with your changes.
>
> \[...\]
>
> `7.`
> If the build passes, rejoice and move on to your next task.
>
> \[...\]
>
> If the commit succeeds, the developers are then, and only then, free to move on to their next task.

They suggest the following best practices:

> #### Never Go Home on a Broken Build
>
> \[...\]
> When the build breaks on check-in, try to fix it for ten minutes.

To summarize what literature says about continuous integration:

- always run all the tests before committing to make sure everything is green
- look closely at your CI builds to make sure they pass, don't proceed with further tasks
- if you break the build, you must treat this as an emergency and fix it ASAP
- you have very little time to fix, otherwise revert your changes

It's not uncommon to have some hardware alarms triggering when build goes red.
I heard of teams where build-breaking developer had to wear some silly hat or donate a dollar for charity (nothing wrong with that alone).
Breaking build is considered a sin, assassination on team's productivity, carelessness and laziness.
CI server becomes this dreadful, scary machine that developers are afraid of.
Bamboo even gives each developer points based on the total number of broken vs. fixed builds.

I fully understand this point of view and behaviour, but this doesn't mean I agree.
I feel this workflow is just plain *wrong*.
I am aware that the whole team is working on the same HEAD/trunk in version control so breaking it is possibly a show-stopper for all of them.
But I'm against treating CI/source control as some scarce resource that is so mission-critical.

Continuous integration server and VCS should be your personal team-mate, doing work for me.
No one is really paying me for staring for, say, 5 minutes at my IDE before each commit to make sure all tests still pass.
If that's the case, I'm suppose to watch CI build blindly for next 5 minutes.
If I broke the build, they expect me to drop everything and just jump in, trying to fix build within 10 minutes, as *Continuous Delivery* suggests.
All this in emergency, stressful manner.
Why?

Back in the days of Java 1.4 we were taught that concurrent programming using `wait()` and `notify()` is hard.
But instead of giving up concurrency we came up with better and easier to use abstractions and libraries.
At the same time we were reluctant to rename classes as this also renamed `.java` files, operation not well supported in CVS.
But instead of keeping old names forever we migrated to superior SVN.
Now because of technical limitations of continuous integration servers and VCS we should treat CI server as a very expensive über-assertion that should never fail.
Technology deficiencies seem to affect our productivity and workflow.

**I want to break the build whenever I want!**
When I'm done and my new tests pass, I just want to commit/push my new stuff and let CI server perform full testing.
I hope everything flies but if not, I don't want to feel guilty.
I don't want to stay late or apologize my team-mates.
I will fix these unexpected problems when I can.
It's not production, it's just my experimental new feature failure that no one cares.

This naturally leads to an idea of [feature branches](http://martinfowler.com/bliki/FeatureBranch.html).
The concept is simple: you develop your feature on a separate branch, CI server might even build all *your* changes and when you feel you are ready, you simply merge your changes back to mainline.
The problem with feature branches is that it's no longer *continuous integration*.
After days of development your feature might be green and ready alone, but merging it back might be extremely problematic.
Also other team members might benefit from your changes, even if they are not complete (but already *green*).
All these observations led me to the following requirements:

- I want to push my changes as often as I need
- CI server should build my changes in isolation so that if they break, no one sees them or cares
- if my changes are good, I want them to be automatically and immediately visible to others
- I also want to see changes made by others as soon as possible

Fortunately modern CI servers (I'm using [Bamboo](http://www.atlassian.com/software/bamboo/overview) as a reference) and version control systems (git here, Mercurial should work exactly the same) are capable of supporting the workflow I've dreamed of.
The main requirement is that I want to push my changes as fast as possible without running all the tests and breaking `master`.
The first step is to create a separate branch and commit to that branch.
**We should never commit to `master`**.
When I think I'm ready with my new feature I simply push that branch and move on.
No running tests locally, no nervous monitoring of CI server.
Just push and approach new challenges.
This may lead to great savings in time if your test suite takes few minutes to run.

First things first, here is how you set up Bamboo.
Under *Plan Configuration* and *Branches* select the following highlighted options:

[![](/assets/img/breaking-build-is-not-crime/1.png)](/assets/img/breaking-build-is-not-crime/1.png)

*Automatically manage branches* will discover and build all new branches automatically.
*Branch Merging Enabled* allows Bamboo to automatically merge new branches with `master` one way or another.
In the *Gatekeeper* configuration we tick *Push on* option.
Here is how it works: I make several commits to my `feature` branch.
You can push them immediately or after some time:

**[![](/assets/img/breaking-build-is-not-crime/2.png)](/assets/img/breaking-build-is-not-crime/2.png)**

```text
* 894217c (HEAD, feature, origin/feature) More tests
    * 3883a5c Starting to work on a feature
    * 1bd4e34 (origin/master, master) Multiplication test
    * f5c886c Testing addition
    * 3e6ab7c Initial revision
```

Notice that my `feature` branch is placed on top of `master`.
`master` branch is still green and my, possibly breaking, changes are isolated.
Here comes the magic.
I configured Bamboo to discover new branches and build them automatically:

[![](/assets/img/breaking-build-is-not-crime/3.png)](/assets/img/breaking-build-is-not-crime/3.png)

What's so special about that?
Bamboo tells me that my changes are fine so I am free to integrate them into the mainline (`master` branch).
Am I?
No, Bamboo did it already!
It built my changes, found them to be *green* and automatically merged them into \`master so that others can see them.
Merging was simple, it's just fast-forward:

**[![](/assets/img/breaking-build-is-not-crime/4.png)](/assets/img/breaking-build-is-not-crime/4.png)**

```text
* 894217c (HEAD, origin/master, origin/feature, master, feature) More tests
    * 3883a5c Starting to work on a feature
    * 1bd4e34 Multiplication test
    * f5c886c Testing addition
    * 3e6ab7c Initial revision
```

[![](/assets/img/breaking-build-is-not-crime/5.png)](/assets/img/breaking-build-is-not-crime/5.png)

OK, was it really that interesting?
After all we would get the same result by simply pushing directly to `master`...
Well, but what happens if we are pushing *breaking* changes to unmodified mainline?
This is the terrifying moment in most of the teams.
I just pushed breaking changes and everyone is yelling at me.
*Fix.
Fast.
Y U NO RUN TEST?*
But not in this approach:

**[![](/assets/img/breaking-build-is-not-crime/6.png)](/assets/img/breaking-build-is-not-crime/6.png)**

```text
* cc4ea63 (HEAD, origin/feature, feature) Experimental changes
    * f0a1a95 Side effects
    * 894217c (origin/master, master) More tests
    * 3883a5c Starting to work on a feature
    * 1bd4e34 Multiplication test
    * f5c886c Testing addition
    * 3e6ab7c Initial revision
```

The last commit is breaking one of the tests:

[![](/assets/img/breaking-build-is-not-crime/7.png)](/assets/img/breaking-build-is-not-crime/7.png)

Here is where all this pain starts to pay off: `feature` branch might be broken, but `master` is untouched.
No merging occurred.
Only my very own, private branch is broken.
Other developers are unaffected.
If this build was *green*, my experimental changes would have been automatically merged to `master` and pushed.
But I made a mistake and they remain hidden.
No one cares, my team mates still see stable `master`.
I can go for lunch or fix it tomorrow.
No stress, no peer-pressure.
When I get it right, Bamboo will automatically apply my fix.

This was all very easy as Bamboo could use fast-forwarding instead of ordinary merge.
But what if we try pushing *good* changes to modified remote `origin/master`?
Suppose we are working on our feature but in the meantime other developer pushed some changes to `bugfix` branch which happened to be correct so Bamboo decided to merge them immediately:

**[![](/assets/img/breaking-build-is-not-crime/8.png)](/assets/img/breaking-build-is-not-crime/8.png)**

```text
* d600da5 (HEAD, feature) Cosmetics
    | * 25612d7 (origin/master, origin/bugfix, master, bugfix) Documentation
    | * 733b6a9 Urgent bug fix
    |/  
    * 4f258a6 (origin/feature) Fixing test failure
    * cc4ea63 Experimental changes
    * f0a1a95 Side effects
    * 894217c More tests
    * 3883a5c Starting to work on a feature
    * 1bd4e34 Multiplication test
    * f5c886c Testing addition
    * 3e6ab7c Initial revision
```

As you can see our `feature` branch was not yet pushed to main repository while `bugfix` branch is already integrated.
How will Bamboo deal with `feature` branch being pushed?
The behaviour is a bit more complex, but still manageable: Bamboo first checks out `master` (including `bugfix` branch already merged) and tries to merge changes from `feature` branch.
If merge was successful (no conflicts), ordinary build is performed.
If build is successful, merge results are pushed to `master`:

**[![](/assets/img/breaking-build-is-not-crime/9.png)](/assets/img/breaking-build-is-not-crime/9.png)**

```text
*   e58a2db (origin/master) [bamboo] Automated branch merge
    |\  
    | * d600da5 (HEAD, origin/feature, feature) Cosmetics
    * | 25612d7 (origin/bugfix, master, bugfix) Documentation
    * | 733b6a9 Urgent bug fix
    |/  
    * 4f258a6 Fixing test failure
    * cc4ea63 Experimental changes
    * f0a1a95 Side effects
    * 894217c More tests
    * 3883a5c Starting to work on a feature
    * 1bd4e34 Multiplication test
    * f5c886c Testing addition
    * 3e6ab7c Initial revision
```

Notice the "*\[bamboo\] Automated branch merge*" commit made implicitly by Bamboo.
As you can see this commit merges all my `feature` branch changes into `master` branch.
This approach works but has several drawbacks:

- after a while your `master` branch history might consist of barely Bamboo generated commits.
  I'd rather see ordinary commits there
- automatic merging in Bamboo might fail
- my `feature` branch still doesn't have `bugfix` branch changes already merged into mainline

For the reasons above it's better to merge my `feature` branch first locally with `master` and push that.
In this scenario you are almost guaranteed that remote merge on Bamboo will never fail (only fast forward), it's predictable and you work on the latest `master` state.
And BTW wondering what would happen if automatic merging on Bamboo fails?

[![](/assets/img/breaking-build-is-not-crime/10.png)](/assets/img/breaking-build-is-not-crime/10.png)

## Summary

This approach for working with version control brings best of both worlds: feature branches and continuous integration.
Because each developer is working on a separate branch (or even repository!), broken commit won't ever make it to `master` branch/mainline.
On the other hand automatic merging will make sure our feature branch is always up-to-date and we won't run into issues when trying to merge days worth of work.
Moreover good commits are immediately visible to others while bad ones remain hidden.
