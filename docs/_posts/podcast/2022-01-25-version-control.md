---
title: "#67: Version control systems: auditing source code, tracking bugs and experimenting"
category: podcast
permalink: /67
tags: version-control vcs git mercurial
description: >
    Version control systems, like git, serve two purposes.
    First of all, they allow collaborating on the same code by multiple developers.
    Collaboration is needed for any non-trivial project.
    Secondly, they keep the history of changes.
    Modification history allows tracking bug fixes and regressions.
    That, and many other applications of version control, will become obvious in a second.
---

{% include player.html episode_id="4Wvj5YmBvuOr57vL2xdHa0" %}

{{ page.description }}

<!--
Imagine you just began a new software project.
You desperately need a teammate to work on some features.
You work independently, maybe remotely.
How do you share the code?
Technically, it's a bunch of files in a directory structure.
So Dropbox or another cloud hosting?
This works for a while but has many shortcomings.

When developing a project, you typically make changes to multiple files.
For example, adding a function in one file and calling that new function from another file.
If you accidentally publish just the second file, the project won't build.
Version control systems solve that problem.
Rather than blindly replicating your changes straight to other developers, they bring one extra step.
Committing changes.

Basically, whenever you think your set of changes is complete, you commit.
Before committing, all your local development changes are just drafts.
Commits, just like a database transaction, are atomic.
Your teammates either see all your changes or none.

Commits are important for another reason.
They have an author and description.
By studying an individual commit you can figure out what changes were needed, and why.
You can even roll back a commit if it broke the application.
Theoretically, it should wipe out a bug without affecting the rest of the application.

Talking about bugs...
Imagine you just discovered a bug on production.
Also, you realized that the bug didn't exist half a year ago.
Most likely, there was a code change that introduced this bug.
The simplest fix is to revert the malfunctioning commit.
Without version control that'd be impossible.
But it gets better!

Some version control systems support have a feature called `bisect`.
In essence, you provide a range of commits.
`bisect` functionality will split that range in half and ask you whether the bug existed in the middle.
If it was, it'll split the first range in half.
If not, the second range.
This way you can find the exact commit that broke your application in logarithmic time.
For example, if your range has 1000 commits, you simply need to examine 10 commits.

There's one more fantastic feature.
Every time you commit and publish your changes, they become visible to your teammates.
However, sometimes you don't want your changes to be immediately available.
For example, when you are working on some experimental feature.
In that case, it's worth having multiple versions of the codebase.
I mean, like parallel universes, each having a slightly different version of the code.
In one universe, code is stable and production-ready.
In multiple other parallel universes, known as _branches_, different features are developed.
Once you are ready, you can _merge_ your feature branch into the stable, production one.

There are many other use cases for version control.
I can't imagine any modern project without git or a similar tool.
Even if you work alone.
Oh, and you can also version-control your infrastructure and developer environment!

That's it, thanks for listening, bye!
-->

# More materials

* [Automated bug finding with git bisect and mvn test](https://nurkiewicz.com/2014/03/automated-bug-finding-with-git-bisect.html)
* [`git`](https://git-scm.com/)
* [`Mercurial`](https://www.mercurial-scm.org/)
* [Version control](https://en.wikipedia.org/wiki/Version_control) on Wikipedia
