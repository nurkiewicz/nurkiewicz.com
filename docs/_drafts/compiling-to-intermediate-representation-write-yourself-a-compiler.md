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
Until recently, you couldn't just run Java.
You always had to compile it first.

That being said, both `.pyc` and `.class` files aren't real computer instructions.
They look fairly abstract with instructions like `STORE_SUBSCR` and `ldc2_w` respectively.
But no computer on earth can run these instructions.
Instead, we build virtual machine _interpreting_ them

## Virtual machine


