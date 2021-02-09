---
title: "#32: Cryptographic hash function"
permalink: /32
tags: hash-function cryptographic-hash-function md5 sha256 java c# rainbow-table birthday-attack
description: >
    Sometimes you need to split arbitrary objects into a fixed number of groups.
    For example, storing a record into one out of many database nodes.
    Or saving a cookie in a hash table.
    Or distributing jobs among multiple workers.
    In all of these cases you later want to know, bucket or worker was chosen.
    Also, data should be split evenly.
    You don't want one node or worker to be overloaded.
    The above properties are implemented by a _so-called_ hash function.
    It's an algorithm that takes arbitrary input and produces fixed-length output.
    A number.
    For the same input, often called a _message_, it always produces the same output, known as a hash.
    Ideally, different messages should produce a different hash.
    Even better, two _slightly_ different messages should produce _wildly_ different hash.
    In practice, hash collisions must happen.
    After all, we are mapping arbitrarily large messages into a fixed-length hash.
    Often 32- or 64-bit.
---

{% include player.html episode_id="7uKytCrSRoGD7PhLXI5bx7" %}

{{ page.description }}

<!--
Good hash functions are quintessential to implement efficient hash tables.
It's a data structure which allows searching by key in constant time.
You simply calculate the hash of the key and then go to the bucket for that key.
In a well-designed hash function and hash table, collisions are infrequent.
So, two different keys rarely land in the same bucket.
But can we do better?
Can we have a hash function without collisions at all?
Theoretically, it's impossible.
If the input space is larger than the output space, by definition two inputs must produce the same output.
Sooner, or later.
In practice, we have several such functions!

Meet cryptographic hash functions.
This special class of functions are designed in such a way that finding a collision is almost impossible.
Mainly because the output space is quite large.
A hash code in Java and C# is just 4 bytes.
Cryptographic hashes are typically 16, 32 or even 64 bytes long.
A 20-digit number!
Finding two messages with the same hash is possible.
But it requires brute-forcing billions upon billions of messages.
Impractical.
Moreover, any reasonable cryptographic hash function is irreversible.
Some legacy hash functions, like MD5, are reversible, thus broken.
Fairly fast algorithms to find any message for a given hash exist.
Why does it mean that MD5 is broken?
Let's think about practical usages.

In the old days of the Internet users' passwords were stored in plaintext in the database, next to user name.
That sounds obvious, how would you make sure that the password is correct, without storing it?
The user enters username, password and you make an equality check.
Sure, but if your user database leaks, all passwords are known to an attacker.
Not only the criminal can login to your account.
Most likely you used the password elsewhere, so all your services are exposed.
But what if, instead of storing the password, we **only** store a cryptographic hash of the password?
When a user logs in, her password is hashed using the same algorithm.
If hashes match, they must have been produces from the same password.
Otherwise, the password is incorrect.
Remember, for practical reasons, two different passwords will never produce the same hash.
Also, it's impossible to figure out what was the password, knowing only the hash.

Another use case is verifying the integrity of a large file.
Suppose someone sends you one gigabyte of data.
How do you make sure the file was not corrupted, or modified by a malicious man-in-the-middle?
Well, if the sender of the file also provides a cryptographic hash of that file, you can verify that file against the hash.
Hash is short enough to be provided through a different, more secure channel.
Over the phone or in a tweet.
We can even go further and hash a message together with our public key.
Without going into details, this not only proves that message wasn't tampered with.
The digital signature also proves we are the authors of that message.

You'll find more materials in the show notes.
Especially about birthday attack and rainbow tables.
Thanks for listening, bye!
-->

# More materials

* [Hash function](https://en.wikipedia.org/wiki/Hash_function)
* [Cryptographic hash function](https://en.wikipedia.org/wiki/Cryptographic_hash_function)
* [Message authentication code](https://en.wikipedia.org/wiki/Message_authentication_code)
* [Birthday attack](https://en.wikipedia.org/wiki/Birthday_attack)
* [Collision attack](https://en.wikipedia.org/wiki/Collision_attack)
* [Rainbow table](https://en.wikipedia.org/wiki/Rainbow_table)


{% include post-footer.md %}