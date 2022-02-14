---
title: "#68: ACID transactions: don't corrupt your data"
category: podcast
permalink: /68
tags: acid base isolation-level sql nosql deadlock two-phase-commit
description: >
    Transactions in SQL databases are rock-solid.
    By reading and modifying data within a transaction we limit the risk of data corruption.
    Actually, there's an acronym describing transactions: ACID.
    Which stands for: _atomicity_, _consistency_, _isolation_ and _durability_.
    A good database engine follows these properties religiously.
    NoSQL engines, on the other hand, trade ACID properties for availability or speed.
    Of course, this is a gross simplification.
    Anyways, NoSQL crowd coined another acronym: BASE.
    Which stands for: _basically available_, _soft state_ and _eventually consistent_.
    We'll leave BASE for another episode.
---

{% include player.html episode_id="4dtpAcKhsiPJUv9vjdTbif" %}

{{ page.description }}

When it comes to ACID, _A_ means _atomicity_.
Simply put, if you make multiple changes to your database, either all or none of them are persisted.
Contrast that to a typical NoSQL database.
Imagine your application modifies two records or documents.
If either your application or DB engine dies in between two writes, only one of them is saved.
Your database is now inconsistent.

Talking about consistency, this is what _C_ in _ACID_ stands for.
This is not really a property of a transaction.
It's more of a feature provided by SQL database.
If your transactions are well-defined, DB engines guarantee to keep the database in a consistent state.
Even if your app dies between two writes, the transaction will abort as if nothing happened.

_I_ means _isolation_.
This is a hard one to provide.
In an ideal world, the database engine should behave as if all transactions run sequentially.
In other words, there are no interactions between transactions.
Of course, this would limit scalability.
So SQL engines have a few tricks.

First, if two transactions are not interacting with the same data, it's fine to run them concurrently.
Only if they do, one transaction must wait for the other to complete.
This means that if one transaction reads the whole table, no other transaction can even touch that table.
This, again, is quite limiting.
So we can actually loosen up these guarantees.
They are called isolation levels.

The strongest isolation level, called _serialized_, is the ideal one described above.
The weakest isolation level, called _read uncommitted_, essentially turns off isolation.
And there are a few levels in between.
It is your responsibility, as a developer, to choose the right level.
Or at least figure out, what is the default isolation level in your application.

Finally, _D_ in ACID stands for _durability_.
That's a no-brainer.
If the database said it committed your transaction, it's guaranteed to store it on disk, safely.

Implementing all these properties is actually quite challenging.
There are a few techniques like write-ahead logging, locks and multi-version concurrency control.
Moreover, the abstraction may leak in the form of deadlocks.
They may occur if two transactions are accessing the same database rows in an unfortunate order.
What will happen is two transactions will wait indefinitely for the other one to complete.

The complexity doesn't end here.
Some databases support distributed transactions via two-phase commit.
Theoretically, you can have ACID properties over multiple databases.
In practice, two-phase commits are rather slow and may fail in an inconsistent state, anyway.

That's it, thanks for listening, bye!

# More materials

* [ACID](https://en.wikipedia.org/wiki/ACID) on Wikipedia
* [ACID versus BASE for database transactions](https://www.johndcook.com/blog/2009/07/06/brewer-cap-theorem-base/)
* [Eventual consistency](https://en.wikipedia.org/wiki/Eventual_consistency) on Wikipedia
* [Two-phase commit protocol](https://en.wikipedia.org/wiki/Two-phase_commit_protocol) on Wikipedia
