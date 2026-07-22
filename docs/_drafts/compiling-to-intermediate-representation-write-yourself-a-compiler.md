---
title: "Compiling to intermediate representation: Write yourself a compiler, Part III"
layout: post
category: writing-compiler
tags: compiler interpreter go ir python JavaScript
---

It's time to dive a bit deeper and abandon the naive realm of interpreters.
Our tiny little project can finally call itself a _compiler_.
In this part we'll emit so-called _intermediate representation_ instead of just evaluating and running the source code as-is.
OK, what does this all mean?

## Intermediate representation

Languages like JavaScript or Python are traditionally classified as _interpreted_.
You "run" the source code, there's no compilation step.
Well, that's not entirely true.
Python is technically compiled to _bitcode_ - a low-level, binary encoding of source code.
You can find bitcode in `.pyc` files somewhere around your project.
On the other hand languages like Java or C# are always compiled, but also to some intermediate representation.
E.g. [bytecode](https://en.wikipedia.org/wiki/List_of_JVM_bytecode_instructions) stored in `.class` files for Java.
Until recently, you couldn't just run Java program.
You always had to compile it first.

JavaScript, on the other hand, still interprets the source code.
But under the hood code is JIT-compiled.
JIT stands for [Just-in-time compilation](https://en.wikipedia.org/wiki/Just-in-time_compilation), but that's a completely different story we might cover later.

That being said, both `.pyc` and `.class` files aren't real computer instructions.
They look fairly abstract with instructions like `STORE_SUBSCR` and `ldc2_w` respectively.
But no computer on earth can run these instructions.
Instead, we build virtual machines _interpreting_ them.

## Virtual machine

Virtual machine (VM) is just yet another program which can technically be called an _interpreter_.
But rather than using complex regular expressions and parsing, it interpret intermediate representation (IR).
IR code is typically a bit more verbose, but much easier to interpret.
For example, it's a linear sequence of commands with no nesting, parentheses, complex flow structures.
It looks closer to assembly, but again, it's not recognizable by any real CPU.

Instead, VM reads IR instruction-by-instruction and invokes it.
Let me give you a short example in Java.
The expression `2 + 3` in Java source code would be translated to:

```
iconst_2
iconst_3
iadd
```

The bytecode basically says: push constant `2` onto virtual operand stack, followed by `3`.
Then the instruction `iadd` pops two most recent values from the stack and replaces them with value `5`.
This sounds silly, but it's still way faster than reading through source code.

