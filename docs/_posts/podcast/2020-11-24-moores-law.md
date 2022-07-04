---
category: podcast
title: "#22: Moore's law"
permalink: /22
tags: moore intel 286 386 486 pentium wolfenstein doom quake transistor
description: >
    It's a common misconception that Moore's law is dead.
    That's because many believe it's about the speed of a CPU.
    But in reality Gordon Moore meant the number of transistors, not the clock frequency.
    And also, it's now even a law.
    Just an observation that holds true after half a century.
    OK, so what does this "law" state?
    Gordon Moore, before co-founding Intel, noticed that the number of transistors in a CPU doubles every two years.
    This means exponential growth.
    Which is a lot.
    So why are these transistors important?
---

{% include player.html spotify_id="57LAFOw2alamnCswuejX17" youtube_id="ZsM9mbOKnSA" %}

{{ page.description }}



A clock speed is simple.
It tells how many operations a processor can run in a second.
The role of transistors is more complex.
Let's drill down into CPU architecture a bit.
A single transistor is a tiny electronic device that can amplify or switch power.
That doesn't tell a lot until you realize that a combination of two transistors can act as a binary gate.
For example, an AND gate produces output current only when both inputs have current.
With a bunch of AND and OR gates you can build a 1-bit adder.
You know, `0 + 0 = 0`, `0 + 1 = 1 + 0 = 1`, `1 + 1 = 0`, carrying `1` to the next digit.
Chaining together 64 1-bit adders gives 64-bit adder.
Now we have an electronic device that can add two really large numbers encoded in binary.
Cool!
Doing subtraction is trivial.
In a similar fashion we can build a circuit that compares two numbers, digit-by-digit.
One step further we can add multiplication, division, etc.
Add a bunch of gates and we can control which operation should be executed against input: adding, multiplying or comparing?
We just built an ALU - Arithmetic logic unit.
Now add a capability to run many operations sequentially, encoded in memory.
This allows us to add thousands of numbers or sort by comparing them.
We essentially built a microprocessor on top of binary gates, which consist of transistors!
How many of them?

One of the first mass-produced CPUs was 4004 by Intel in 1971.
Half a century ago.
It contained 2250 transistors.
Moving forward one decade, the much more important milestone was 286.
With more than 130 thousand transistors, it could run Wolfenstein 3D.
10 more years we see 486 with 1 million transistors and playable Doom.
Roughly by the end of the century, to enjoy the original Quake, Pentium III was required.
With 10 million transistors.

Long story short your iPhone or MacBook now run on more than 10 **billion** transistors.
Why on earth do modern CPUs need so many transistors?
The Arithmetic Logic Unit itself is probably around a few thousand transistors.
What else? 
Well, the clock speed can't grow forever.
As a matter of fact CPUs don't get faster due to the physical limits.
The speed of light to be precise.
But if we can't get faster, maybe we should have more of the same?
Rather than scaling up, CPUs are scaling out, adding new cores.
Most consumer processors these days have many cores, which essentially means multiple processors in one tight box.
That's why taking advantage of parallel algorithms is so important.
In the old days, parallelism was emulated by context switching between threads and processes.
These days multiple threads can run truly at the same time.
This is thanks to multiple cores made possible.
Also, various levels of caches consume a lot of CPU's real estate and transistors.

Does it all mean that Moore's law will continue forever?
That's impossible. 
A single transistors is really, really small.
And they get even smaller to fit integrated chip.
So small that quantum tunneling effects begin to appear.
But they have to get smaller, otherwise our CPUs would become larger and consume kilowatts of energy.
Yet, for the time being, we can enjoy an unbelievable progress in computing capacity.

That's it, thanks for listening, bye!




# More materials

* [Moore's law](https://en.wikipedia.org/wiki/Moore%27s_law)
* [4004 chip schematics](https://4004.com/mcs4-masks-schematics-sim.html)
* [Transistor count table](https://en.wikipedia.org/wiki/Transistor_count)
* [Apple M1 has 16 billion transistors](https://www.forbes.com/sites/patrickmoorhead/2020/11/11/the-good-bad-and-the-ugly-of-apples-mac-launch-with-m1-processors/)
* [Designing an AND Gate using Transistors](https://circuitdigest.com/electronic-circuits/designing-and-gate-using-transistors)
* [TSMC: Moore’s Law is "not dead, it’s not slowing down, it’s not even sick."](https://www.pcgamesn.com/tsmc-moores-law-not-dead-not-slowing-down-not-even-sick)
* 🔉 [#7: Speed of light](https://256.nurkiewicz.com/7)
* [From Nand to Tetris](https://www.nand2tetris.org/) - Building a Modern Computer From First Principles


