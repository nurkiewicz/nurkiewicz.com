---
title: "#52: How computers work: from electrons to Electron"
category: podcast
permalink: /52
tags: cpu alu transistor
description: >
    Today I'd like to explain how computers work.
    From the ground up, grossly simplifying.
    It all starts with an electric field.
    It's a place where charged particles, like electrons, are attracted or repelled.
    The electricity flows through a piece of wire because of the difference in electric field potential on wire's ends.
    This difference is known as voltage.
---

{% include player.html episode_id="7EVHMs2fpRLF0wjyU1eHJk" %}

{{ page.description }}

<!--
## Vacuum tubes

Then comes diode.
It's like a one-direction valve, passing current only one way.
You can build a diode using vacuum tubes.
A tube is a fairly big glass device that needs a lot of energy and often breaks.
But!
One can also build switches and amplifiers using vacuum tubes.
It's just one step from constructing large, clumsy computers like ENIAC.
With its 18 thousand vacuum tubes and 30 tons of weight, it wasn't very portable.
The invention of transitors changed everything.

## Transistors

Transistors are much smaller than vacuum tubes.
You'd need a very sophisticated microscope to see a them.
Turns out, you can connect two transistors two create a very simple device, with two inputs and one output.
The output has high electric potential if and only if both inputs have high potential.
Change _high potential_ to binary `one` and you end up with logic AND gate.

## Logic gates

With a few AND gates you can build a 1-bit adder.
A tiny device that takes two bits and adds them.
Bits are numbers, 0 or 1.
If you connect 32 such adders sequentially, you can now add two, 32-bit numbers.
This is big!
We have an electronic circuit that adds binary-encoded numbers ranging up to 4 billion.
But it gets better.
Inverting bits of the second number makes it negative.
So our device can also subtract!

## ALU

By adding one extra input bit we control if we want to add or subtract inputs.
Or maybe we want to compare which number is bigger?
Or apply logical AND of corresponding bits?
We now have a device that takes two large numbers and an encoded operation.
Depending on which operation we choose, the output is different.
This device is typically called ALU: Arithmetic Logic Unit.

## CPU

ALU itself is too simple.
What if we want to add a thousand numbers, not just two?
We can build an extra wiring that takes the output of addition and feeds it back as input of the next step.
That's how we can program ALU to perform multiple, very simple steps.
We just built a CPU: reading a sequence of instructions from memory, feeding them into ALU and providing outputs.
Outputs are stored into memory or fed back into ALU.
Oh, and memory is also a bunch of transistors that can keep state.

## High-level languages

Programming computers using machine code is tedious.
That's why high-level languages, like C++ or Go, were invented.
The compiler translates `for` loops, `if` statements and so on - into machine code.
All this happens within an operating system.
Yet another program that abstract away the hardware.

So the next time you open, for example, Slack, remember this:
It's a JavaScript application deployed on top of Electron.
Electron is itself written in C++.
Which was compiled to machine code that is loaded from memory into CPU.
CPU decodes, caches and invokes instructions.
Data and instructions are encoded as binary, which in turns, is converted into electric signals.
The electrons flow through transistors, which produce output current.
All of this to see funny cat pictures.

That's it, thanks for listening, bye!

-->

# More materials

* [Build a Modern Computer from First Principles: From Nand to Tetris (Project-Centered Course)](https://www.coursera.org/learn/build-a-computer)
* [Electric field](https://en.wikipedia.org/wiki/Electric_field)
* [Electric potential](https://en.wikipedia.org/wiki/Electric_potential)
* [Electric current](https://en.wikipedia.org/wiki/Electric_current)
* [Vacuum tube](https://en.wikipedia.org/wiki/Vacuum_tube)
* [Relay](https://en.wikipedia.org/wiki/Relay)
* [Transistor](https://en.wikipedia.org/wiki/Transistor)
* [Logic gate](https://en.wikipedia.org/wiki/Logic_gate)
* [Use Transistors to Build a NAND Gate](http://mathcenter.oxford.emory.edu/site/cs170/nandFromTransistors/)
* [Adder (electronics) (full adder)](https://en.wikipedia.org/wiki/Adder_(electronics) (full adder))
* [Arithmetic logic unit](https://en.wikipedia.org/wiki/Arithmetic_logic_unit)
* [74181](https://en.wikipedia.org/wiki/74181)
* [Central processing unit](https://en.wikipedia.org/wiki/Central_processing_unit)
* [Elctron.js](https://www.electronjs.org/)
* [Exploring How Computers Work](https://www.youtube.com/watch?v=QZwneRb-zqA)
* [How Do Computers Remember?](https://www.youtube.com/watch?v=I0-izyq6q5s)
