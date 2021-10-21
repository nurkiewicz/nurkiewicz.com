---
category: podcast
title: "#7: Speed of light"
permalink: /7
tags: moore cpu cdn ping
description: Speed of light is not as abstract to us, software engineers, as you might think. If you are deploying to the cloud or if you want to squeeze every bit of performance in your app, speed of light holds you back

---

{% include player.html episode_id="4xmF0EoYZLebgUSMmpz9Tt" %}

{{ page.description }}

Light travels at an unbelievable speed of three hundred thousand kilometres per second.
That's more than 7 times around the globe in one second.
Is this relevant in our industry?

What do you think is faster: loading data from local hard drive or from a Redis in-memory cache, deployed somewhere in the same data center?
Turns out network round-trip is faster by an order of magnitude, compared to hard drive.
Basically the speed of light beats mechanical device by far.
But let's scale out a little bit.
Ever heard of `ping` command?

`ping` measures how much time a tiny network packet travelled from your computer to the server and back again.
This time is affected by the number of network hops, server's latency, but also... speed of light.
The distance from Perth (Australia) to New York is almost nineteen thousand kilometres.
So `ping` from your customer in Australia to your server in New York needs to travel more than **thirty seven thousand** kilometres.
This is about one hundred and twenty five milliseconds if `ping` was a photon and a server was a mirror.
In practice speed of light is the least of your concerns, when you think about server's latency, number of network hops, dropped and retransmitted packets, etc.
But the speed of lights says already tells us, that no matter what you do, you can't expect your website to respond faster that one eighth of a second.
That's why CDNs (content delivery networks) are so popular, serving data and running code as close geographically as possible.
Also that's why the most scalable database are replicated across multiple continents.
Otherwise, even if your backend is deployed in close proximity to the customer, it has to wait ages (well, milliseconds) for the database.
Even if you believe that network is extremely fast, when building a worldwide business, you must think about geography.
Because of the speed of light limitations.

OK, that's the speed of light on the macro scale.
But it happens to be relevant in the micro scale as well.
The fastest CPUs these days have a clock speed of about 5 GHz.
Greatly oversimplifying, this means a single instruction takes about 0.2 nanoseconds.
That's rather... fast.
How far can light travel in that time?
I'll spare you the tedious math - only 6 centimetres.
If CPU is larger than 9 square centimetres there is not enough time for light to travel from top-left to bottom-right corner of the device.
Assuming paths are perpendicular.
Let that sink into you: today's CPUs are so fast that there is not enough time for electrical signal to propagate from input to output.
OK, I'm greatly simplifying.
First of all, CPU architectures takes that into account.
They can't bend the laws of physics, but due to instruction pipelining a single cycle invokes only small part of instruction.
So even the simplest instruction, like adding two numbers, takes multiple cycles.
However, when CPU is about to finish addition, it already started several subsequent instructions.
This techniques was used in Intel's 386 CPU back in 1985.

And no, speed of light is not causing Moore's Law to collapse.
First of all because Moore's does not talk about CPU speed doubling every 18 months.
This indeed no longer olds true.
But it talks about number of integrated transistors that keeps growing.
And Moore's Law still holds.

However, because transistors do include certain delay in signal propagation and because of the speed of light, CPU clock frequencies can't go higher infinitely.
That's it, thanks for listening about physics for a while.
Hope you'll understand why choosing the right location for your data center is important.
Any why CPUs are not getting faster.

# Distance the light travels during one CPU cycle at 5 GHz

<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

<p>
    \begin{align}
    c = 3 \cdot 10^8 \mathrm{m \over s} \\
    f = 5 \mathrm{GHz} = 5 \cdot 10^9 \mathrm{Hz}\\
    t = {1 \over f} \\
    s = c \cdot t = {c \over f} \\
    s = { {3 \cdot 10^8 \mathrm{m \over s}} \over 5 \cdot 10^9 \mathrm{1 \over s}} = \\ 
    = {3 \over {5 \cdot 10}}  \mathrm{m} = {30 \over 5} \mathrm{cm} = \\ 
    6 \mathrm{cm}
    \end{align}
</p>

<blockquote class="twitter-tweet"><p lang="en" dir="ltr">The speed of light on a cosmic scale.<br><br>Credit: <a href="https://twitter.com/physicsJ?ref_src=twsrc%5Etfw">@physicsJ</a> <a href="https://t.co/ekTd5Sdamu">pic.twitter.com/ekTd5Sdamu</a></p>&mdash; Wonder of Science (@wonderofscience) <a href="https://twitter.com/wonderofscience/status/1450804100388384771?ref_src=twsrc%5Etfw">October 20, 2021</a></blockquote>
<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

# More materials

* [Latency Numbers Every Programmer Should Know](https://gist.github.com/jboner/2841832)
* [Instruction pipelining](https://en.wikipedia.org/wiki/Instruction_pipelining)
* [A CPU history](https://www.techjunkie.com/a-cpu-history/)
* [Moore's law](https://en.wikipedia.org/wiki/Moore%27s_law)
* [The distance from Perth, Australia to New York](https://www.travelmath.com/distance/from/Perth,+Australia/to/New+York,+NY)


