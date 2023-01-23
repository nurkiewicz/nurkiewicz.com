---
title: "#59: How compilers work: from source to execution"
category: podcast
redirect_from:
  - /59
tags: compiler syntax grace-hopper interpreter cobol
description: >
    A compiler is an application that turns text into an executable program.
    It's quite extraordinary how much work these complex pieces of software are doing.
    Pretty much every compiler works by executing several phases.
    Each phase takes the input of the previous ones to finally produce the runnable code.
    Let's take a journey through the compiler internals.
---

{% include player.html spotify_id="5v2EYpKDN6kFqBzpUjtwKw" youtube_id="T1lvRIHoMqc" %}

{{ page.description }}

The compiler's work is traditionally divided into three stages: frontend, middle, and backend.
The frontend interacts directly with the source code.
It reads your C++, Rust or... Go file.
At this point, your source code is just a sequence of characters.
Or even bytes, to be precise.

The first phase is tokenization by a so-called _lexer_.
A lexer takes a stream of characters and groups them according to the language rules.
It uses regular expressions for that.
For example, there's a regex for all keywords, number literals, operators, etc.
Whitespaces are typically ignored by this phase unless they are significant.
So, if your source code is:

```
answer = 21 * 2;
```

for a typical language this will produce a stream of the following tokens:

* an identifier named `answer`
* assignment operator
* number literal `21`
* multiplication operator
* number literal `2`

At this point, many syntax errors are caught.

The next phase of the frontend compiler is _parser_.
The parser takes a flat stream of tokens and organizes them in an _abstract syntax tree_.
Within that tree, functions and operators are parent nodes.
Arguments are children.
In our assignment example, the assignment is the parent node.
One child is the identifier: `answer`.
The second child is a subtree.
That subtree has multiplication as a parent node.
And numbers `21` and `2` are children.

![Abstract syntax tree](img/podcast-59-ast.svg)

This weird tree structure supports operator precedence, parentheses and overall is quite convenient.
At this point, many errors are caught.
For example, the first child of the assignment operator must be an identifier (a variable).
You can't assign to a constant.

The next phase is semantic analysis.
Here, the compiler checks types and other programming language constraints.

The middle end of the compiler takes the raw syntax tree and optimizes it.
The optimizations include dead code elimination, precomputing constants, etc.
All optimizations are agnostic to the target machine/processor.
The result of this stage is the so-called _Intermediate Representation_.
IR for short.
For example, bytecode in Java may be considered IR.

The backend compiler takes IR and produces the machine code.
First, it applies optimizations specific to selected CPU architecture.
Say, if you are targetting a 64-bit CPU, different optimizations are possible.
Similarly, some techniques faster on x86 are slower on ARM, and vice-versa.

Last but not least, the backend compiler generates machine code.
It still requires a lot of work, like organizing data in CPU registers.
Finally, a standalone executable is produced.

The important milestone for a new language is called bootstrapping.
It's the moment when you can write a compiler for a language in that language.
At first, it's impossible, because there's no compiler to compile... your compiler...
Duh!

Keep in mind that many languages these days aren't compiled ahead of time.
For example C# or JavaScript.
C# is compiled to IR.
JavaScript is distributed as source code.
The compilation typically happens inside a browser.
And it's just an optimization technique, known as Just-in-time compilation.

That's it, thanks for listening, bye!

# More materials

* [Bison is a general-purpose parser generator](https://www.gnu.org/software/bison/)
* [ANTLR](https://www.antlr.org/)
* [Grace Hopper](https://en.wikipedia.org/wiki/Grace_Hopper)
* [How do computers read code?](https://www.youtube.com/watch?v=QXjU9qTsYCc)
* [#18: JIT: bytecode, interpreters and compilers]({% post_url podcast/2020-10-13-jit %})


