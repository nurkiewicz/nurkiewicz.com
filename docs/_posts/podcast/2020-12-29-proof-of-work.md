---
category: podcast
title: "#27: Proof-of-work in blockchain: achieve consensus without trusted third party"
permalink: /27
tags: proof-of-work blockchain bitcoin double-spending halving
description: >
    Let's try to cheat the blockchain.
    If my wallet has exactly one bitcoin, I can't spend it twice.
    Once it's written into an immutable blockchain, **everyone** knows my wallet is empty.
    However, what if I purposefully create and announce two blocks at the same time.
    With the same parent block.
    For example, in one of the blocks there's a 1 bitcoin from my wallet spent on drugs.
    In the other block I spent that same bitcoin on unlicensed firearms.
    You know, things you do with cryptocurrencies.
    There are two competing blocks, each having a different version of the history.
    There is no central database so the blockchain network has no way of figuring out which block is valid and which is not.
    Well, they both technically are.
---

{% include player.html episode_id="3b59wmtZaC5V9qrNnL8zfE" %}

{{ page.description }}



A drug dealer may believe in one fork, whereas a gun dealer believes in the other.
They both think they received the money and sell me the goods.
But the whole network is confused.
Which block should be treated as a `master` branch, and which one should be forgotten?
Remember, these blocks are conflicting with each other, so we can't somehow merge them.
The solution?
Both branches keep growing and the network eventually chooses... the longer one.
That's right.
If the branch containing a drug transaction gets another one appended faster, it is considered the only valid one.
That block is said to have _one confirmation_.
The competing block with firearms transaction is discarded by the majority.
Gun dealer is out of luck.
Maybe that's a good thing.

However, it's still possible that the firearms block will somehow get two more blocks appended.
So now it has two confirmations, one more than drug's branch.
You see where this is going.
This game could continue forever. 
Drug and firearms sellers simply keep adding thousands of blocks to convince the network it's their transaction that's valid.
This is where the proof-of-work comes into play.

Cheating the system is only possible if you can create blocks out of thin air without much hassle.
But what if creating a new block was actually expensive, in some way?
To such extent that creating two blocks at the same time would be prohibitively expensive?
Rather than introducing some fees, _proof-of-work_ algorithm was invented.
In order to announce a new block you have to spend a little bit of time and energy.
Prove you did some work with your computer.
That's why it's called _mining_.
Like gold mining.
Mining a block requires solving some complex math problem, typically by brute-forcing every possible solution.
Every participant of the blockchain does the same thing, so they are competing with each other.
Whoever is first, wins.
In order to cheat the system you'd need more than 50% of the computational power of the whole network.
Currently it means probably hundreds of thousands of CPUs.
It's simply not worth it.

Moreover, because brute-forcing a solution happens simultaneously on thousands of computers, it requires extreme amounts of electricity.
We're talking CPU-intensive tasks like computing cryptographic hashes, billions per second.
It is estimated that mining bitcoin consumes as much energy as many developed countries consume in total.

There's one more thing.
Bitcoin's blockchain adds new blocks approximately once every 10 minutes.
So if you want your transaction to come through, you must wait until someone mines a block verifying it.
However, due to forks that can occur with no malicious intent, typically the receiver waits for a while.
The most cautious wait for as much as 6 confirmations.
I mean, 6 more blocks, an hour.
Also, you must incentivize miners to include your unverified transaction in their block by paying a fee.
Blocks have limited space, verifying a transaction against gigabytes of history is expensive.
So you must pay for that service.
Long story short, the price for decentralized currency is huge:

* transaction fees are quite large
* latencies are measured in minutes to hours
* throughput is small due to limited block size
* terawatts of energy are used redundantly

I see blockchain as a wonderful concept but with very limited practical uses.

Thanks for listening, bye!


# More materials

* [Proof of work](https://en.wikipedia.org/wiki/Proof_of_work)
* [How Does Bitcoin Mining Work?](https://www.investopedia.com/tech/how-does-bitcoin-mining-work/)
* [But how does bitcoin actually work?](https://www.youtube.com/watch?v=bBC-nXj3Ng4) on YouTube
* [Curated list of scams, hacks and fails of cryptocurrencies](https://github.com/nurkiewicz/crypto-hall-of-shame)
* [How does a block chain prevent double-spending of Bitcoins?](https://www.investopedia.com/ask/answers/061915/how-does-block-chain-prevent-doublespending-bitcoins.asp)
* [How proof of work prevents double spend](https://bitcoin.stackexchange.com/questions/61385/how-proof-of-work-prevents-double-spend)
* [Blockchain size (MB)](https://www.blockchain.com/charts/blocks-size)


