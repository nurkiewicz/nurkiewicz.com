---
title: '#5: asm.js and WebAssembly'
permalink: /5
tags: javascript asm.js webassembly c c++ rust gc
description: asm.js and WebAssembly are two technologies used to run native code in the browser with great performance. They can be used to run game engines and complex computation on the client.
---

{% include player.html episode_id="43vAe1EWEf0pPWVdf32IHg" %}

{{ page.description }}

JavaScript is a dynamically typed languages and languages like that are typically harder to get fast.
Take for example a simple expression like `A + B`.
In statically typed languages if you know in advance that `A` and `B` are, let's say, integers, you simply issue a single CPU instruction for adding 2 numbers.
In dynamically typed languages when you say `A + B`, `A` can be anything: a number but also an array, object, a function.
And for example according to the spec if you add 2 empty arrays what you get in return is an empty string.
At least in JavaScript

asm.js was an effort to run native statically typed languages in the browser.
asm.js is not meant to be written by hand.
Typically you take an existing source code written in C, C++ or Rust (or other low level languages like that) and do you translate it into asm.js.
asm.js is actually a subset of JavaScript meaning that asm.js program is a valid JavaScript program.
However, when compiling to asm.js you add seemingly unimportant statements.
For example our original program was `A + B`.
This is how it would look like in C or C++.
In asm.js it becomes `A|0 + B|0`.
You might think adding `|0` doesn't change the actual number.
It's a no-operation.
However, when the JavaScript engine sees an expression like that: `A|0` it knows that it has to be a number.
So in other words we are casting arbitrary expression into a number and just-in-time compiler sees `number + number` and it can deduce much more.
Just by looking at the source code it knows exactly how to add 2 numbers.
This is a great performance optimization.

Another performance optimization that asm.js adds is the lack of garbage collection.
It's not a coincidence that I mentioned C, C++ and Rust but not Go or Java - because these are the languages that have garbage collector.
Programs translated into asm.js are not supposed to produce any garbage, meaning they should allocate and delegate memory on their own.

So once again asm.js is not another languages.
It's not a library, it's just a way of writing JavaScript programs in a way that's much easier to reason about for JavaScript engine and ahead of time compiler.
This translation happens using a tool called `emscriptem` that takes an existing source code and translates it into a subset of JavaScript.

asm.js is kind of a hack, therefore there was an effort to create something a little bit more standard which later became WebAssembly.
WebAssembly is the fourth language running inside the browser, next to HTML, JavaScript and CSS.
WebAssembly is a binary language that has the same purpose as asm.js but it's implemented in a much different way
You no longer send a stripped down version of JavaScript.
Instead you send a binary code that's run in the JavaScript sandbox.

Is this whole transformation worth it?
Well, in some benchmarks asm.js and WebAssembly are only two times slower than the native binary code like C or C++.
Which also means they are much, much faster than the corresponding JavaScript code.
It's pretty amazing that you can now compile a full Unreal Engine or Unity engine into asm.js or WebAssembly and run games like Quake 3 inside your browser.


# More resources:

* [asm.js](https://en.wikipedia.org/wiki/Asm.js)
* [WebAssembly](https://en.wikipedia.org/wiki/WebAssembly)
* [Compiling C/C++/Rust/... to asm.js via LLVM backend](https://emscripten.org/)
* [Quake in the browser (asm.js)](http://www.quakejs.com/)
* [Unity Engine in the browser (WebAssembly)](https://blogs.unity3d.com/2018/08/15/webassembly-is-here/)


