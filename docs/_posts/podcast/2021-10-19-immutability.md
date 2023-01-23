---
title: "#54: Immutability: from data structures to data centers"
category: podcast
redirect_from:
  - /54
tags: immutability postgresql wal kafka mvcc docker caching
description: >
    Immutability means that when something was once created, it can't be changed.
    This concept is tremendously important across our whole industry.
    Probably you've heard about immutable data structures.
    Let's take an immutable list as an example.
    If you create such a list with a few items, you can't add more items to that list.
    It's written in stone.
    Any action attempting to modify that list returns a modified copy.
    The original instance is left intact.
    Modifying a single item, adding or removing, sorting - each of these operations return a copy.
---

{% include player.html spotify_id="6xiMQEggYikV7WwG0nWULU" youtube_id="7w9BVQLlVO4" %}

{{ page.description }}

You may think this is terribly inefficient.
Naively implemented immutable data structures are very inefficient.
Imagine copying 1 million items in a list just to add a new one.
However, immutable data structures use one clever technique, called structural sharing.
In principle, the modified copy of a data structure reuses large parts of the original object.
Therefore, more often than not, copying is very superficial.
Underneath, a lot of data is shared.
Sharing is safe because data is, you know, immutable!

Such data structures have some amazing features.
If your data never changes, it's absolutely safe to share it between threads.
You don't need any synchronization or mutexes.
It also means you can easily take a consistent snapshot of your program's state.
Imagine you are implementing a computer game.
Saving the game to disk is a challenge.
Without freezing the entire game you'll read inconsistent data.
But when game's state is immutable, it's trivial.
In general, immutability helps tremendously when consistency is needed.

BTW that's why many relational databases take advantage of immutability.
For example, PostgreSQL uses Multiversion Concurrency Control, MVCC for short.
The basic principle of this idea is to keep multiple, unmodifiable versions of the same record.
Another use case is Write-Ahead Logging (WAL).
A log of database changes that can only grow, but never mutates.
Synchronizing this log with multiple machines makes replication much easier.
A similar approach was taken by Kafka.

Immutability makes its way up the stack.
Version control systems like git take advantage of immutability quite extensively.
Effectively, each commit represent an immutable snapshot of the whole directory.
Of course, each snapshot shares a lot of data with its predecessors.
The same applies to Docker containers.
Each container is a set of immutable file system layers.
Creating a new container means taking an existing file system and applying another immutable layer.

This approach is taken to the extreme with _so-called_ immutable infrastructure.
In that case we never touch modify production servers manually.
Instead the desired state of production (servers, packages, users and privileges) is defined once.
Any change to production environment happens via new definition.
To avoid configuration drift it's sometimes safer to destroy a machine and provision it again.

The last place where immutability comes to my mind is caching.
Cache invalidation is extremely hard.
But when you can prove that whatever is cached never changes, there's no need for invalidation.
For example, consider `Cache-Control: immutable` header in HTTP response.
This is the most effective caching technique.
Once stored in your browser or caching proxy, it may live there forever, safely.

That's it, thanks for listening, bye!

# More materials

* [_immutable_](https://www.merriam-webster.com/dictionary/immutable) in Merriam-Webster Dictionary
* [John Carmack Keynote - Quakecon 2013](https://www.youtube.com/watch?v=Uooh0Y9fC_M&t=4660s) about implementing Wolfenstein 3D in Haskell with immutable data structures
* [Write-Ahead Logging (WAL)](https://www.postgresql.org/docs/13/wal-intro.html) in PostgreSQL
* [Episode 447: Michael Perry on Immutable Architecture](https://www.se-radio.net/2021/02/episode-447-michael-perry-on-immutable-architecture/)
* [Using Immutable Caching To Speed Up The Web](https://hacks.mozilla.org/2017/01/using-immutable-caching-to-speed-up-the-web/)
* [#40: Docker: more than a process, less than a VM]({% post_url podcast/2021-05-18-docker %})
* [#47: Terraform: managing infrastructure as code]({% post_url podcast/2021-07-06-terraform %})

