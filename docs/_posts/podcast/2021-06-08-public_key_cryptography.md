---
category: podcast
title: "#43: Public-key cryptography: math invention that revolutionized the Internet"
permalink: /43
tags: encryption rsa enigma pki alan-turing
description: >
    Disclaimer: this podcast is not about cryptocurrencies.
    I despise them.
    Instead, we'll talk about asymmetric encryption.
    One of the most wonderful math discoveries of the 20th century.
    Before 1970s all cryptographic algorithms were symmetric.
    This means that the same key must be used to encrypt and decrypt data.
    That sounds rather obvious.
    If you encrypt a file with a password, you must use the same password to decrypt it.
    But there's one problem.
    Imagine Bob wants to e-mail an encrypted file to Alice.
    Sadly, Eve can read all communication between Alice and Bob.
    File was encrypted, so no worries?
    Well, it's not only encrypted, but also worthless.
    Alice doesn't have a password.
    And how is Bob suppose to provide that password if Eve can spy all communication channels?
---

{% include player.html spotify_id="5K3tGBIHCIG3TdPDg3cZTs" youtube_id="snYyLmOKJq8" %}

{{ page.description }}

This is not an abstract problem.
German army during Second World War used an encryption device known as Enigma.
The password was changed daily.
Of course, both the sending and the receiving machine need to use the same password.
So once a month passwords for the upcoming month were printed in a code book.
This sheet of paper was later delivered out-of-band, physically, via courier.
Surprisingly, stealing code book was not how the machine got cracked.
Polish mathematicians discovered a weakness in the machine's algorithm, that was later fully exploited by Alan Turing's team.
But back to the topic.

As you can see, distributing the key is a major challenge.
What if we could have an algorithm where one key is used for encryption and another for decryption?
It's like I have a door key that can only close the door and another one that can only open it.
As a matter of fact, such an asymmetric algorithm was an area of research for centuries.
Then, RSA algorithm was invented in the 1970s.
Underneath, it uses a particular math problem of factoring large numbers.
Since then, many other algorithms were invented, but let's focus on the basic principles.

When Bob wants to securely send something to Alice, she must first create a pair of keys.
One is private and never leaves her computer.
The other is public and it should be freely available to everyone.
Bob takes Alice's public key and encrypts a message to her.
Keep in mind that Eve now knows both Alice's public key and an encrypted message.
However!
A message encrypted with the public key can only be decrypted with the private key.
And the private key never left Alice's computer.

This ingenious idea allows two parties to communicate securely without any prior key exchange.
Another immensely important feature of public-key cryptography is a digital signature.
Let's say you take a document and encrypt it via your private key.
By definition, the document can only be decrypted using the other key.
The public one, freely available.
This way everyone can decrypt that document.
But more importantly, if we can decrypt a document with someone's public key, it proves it was encrypted using that person's private key.
In other words, the holder of the private key is the only person that could sign that document.
It's almost an unforgeable signature.

Public-key cryptography has two challenges.
First one is the distribution of public keys.
This is somewhat solved by public-key infrastructure.
A hierarchy of well-known certification authorities.
Another challenge is slowness of asymmetric encryption.
So typically it's only used in the beginning to exchange strong, single-use symmetric key.

But that's a different topic.
Thanks for listening, bye!

# More materials

* [If the German's changed the Enigma settings every day at midnight, how did the recipients of the encrypted messages know about the settings?](https://www.quora.com/If-the-Germans-changed-the-Enigma-settings-every-day-at-midnight-how-did-the-recipients-of-the-encrypted-messages-know-about-the-settings?share=1)
* [How did the Germans make sure their Enigma machines were all configured the same?](https://www.reddit.com/r/AskHistorians/comments/45unnm/how_did_the_germans_make_sure_their_enigma/)
* [Public key infrastructure](https://en.wikipedia.org/wiki/Public_key_infrastructure)
* [Enigma code book](http://users.telenet.be/d.rijmenants/pics/hires-wehrmachtkey-stab.jpg)
* [Cryptography: Crash Course Computer Science #33](https://www.youtube.com/watch?v=jhXCTbFnK8o) on YouTube


