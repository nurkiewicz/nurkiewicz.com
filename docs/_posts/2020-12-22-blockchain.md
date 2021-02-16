---
title: "#26: Blockchain"
permalink: /26
tags: blockchain bitcoin merkle-tree hash-function
description: >
    Blockchain is a technology used for storing data without a central database.
    Data is organized in an ever-growing list of blocks with each block referencing the previous one.
    Like a linked list.
    Once a block is added to this list, it can't be modified.
    The integrity is guaranteed by including a cryptographic hash of the previous block.
    If the previous block changes, all subsequent blocks need to change as well.
    You can't simply modify history.
    This is similar to the operations on your bank account.
    However, the idea behind the blockchain is to maintain integrity without a central authority, like a bank.
    Data is distributed among peers.
    No node is distinguished and some number of nodes can even be hostile.
    Blockchain tolerates up to 50% of nodes purposefully trying to cheat the system.
    Everything happens using peer-to-peer network with no central backbone whatsoever.
    At what cost all of this can be achieved?
---

{% include player.html episode_id="5IbUexoU3P9QCiRhKMRNfv" %}

{{ page.description }}



Starting from the basics.
Blockchain is most commonly used to keep track of cryptocurrency transactions.
The most popular one is bitcoin, so I'll use it in the examples.
Bitcoins are like an ordinary electronic currency.
You can transfer bitcoins from one account to another, known as wallets.
Blockchain must provide one important guarantee: the same bitcoin cannot be spent twice.
The double-spending problem doesn't exist with paper cash.
Once you exchange ten dollar bill for a burger, you can no longer use that bill.
When paying by credit card the card terminal contacts your bank.
Payment is refused in case of insufficient funds.
But how can you ensure that the same bitcoin wasn't spent twice on two different goods or services?
By definition there is no single server storing your wallet's balance!

Well, actually, this information is stored on every participant's computer.
A complete history of each and every transaction from the beginning of the blockchain.
As of December 2020, the bitcoin's blockchain contains 600 million transactions in 600 thousand blocks.
The whole blockchain has about 300 GiB of data.
When a new unconfirmed transaction appears, every participant of the blockchain can verify it.
We must make sure that the source wallet contains sufficient funds.
This can be done by replaying all transactions from the past.
Because every transaction is public, we can easily verify consistency.
Surprisingly, that's not the reason why blockchain consumes so much computing power and energy.
More on that later.

OK, so we have a pool of unconfirmed transactions that every node in the blockchain may verify.
This pool is verified and packaged together in a block.
That block is attached to the end of the blockchain and broadcasted to everyone.
Periodically, for example every 10 minutes.
The transaction becomes an immutable part of history.
Spending the same bitcoin once again is impossible because it was already spent in one of the previous blocks.
Is that enough to prevent a fraud?
Unfortunately, it's just the beginning.

What if two independent nodes verify a bunch of transactions, package them in a block and broadcast them?
Suddenly we have two blocks with the same parent.
Blockchain just forked.
These two blocks can be different.
In order to understand how blockchain handles forks and prevents double-spending, we must understand the _proof-of-work_ algorithm.
That also explains why blockchain uses more energy than the country of Austria.
But that will be covered in the next episode.

Thanks for listening, bye!





# More materials

* [Proof of work](https://en.wikipedia.org/wiki/Proof_of_work)
* [But how does bitcoin actually work?](https://www.youtube.com/watch?v=bBC-nXj3Ng4) on YouTube
* [Curated list of scams, hacks and fails of cryptocurrencies](https://github.com/nurkiewicz/crypto-hall-of-shame)
* [How does a block chain prevent double-spending of Bitcoins?](https://www.investopedia.com/ask/answers/061915/how-does-block-chain-prevent-doublespending-bitcoins.asp)
* [How proof of work prevents double spend](https://bitcoin.stackexchange.com/questions/61385/how-proof-of-work-prevents-double-spend)
* [Blockchain size (MB)](https://www.blockchain.com/charts/blocks-size)

{% include post-footer.md %}