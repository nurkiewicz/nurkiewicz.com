---
title: "A railroad diagram for the simplest interpreter"
layout: post
category: writing-compiler
tags: compiler interpreter grammar mermaid
mermaid: true
---

In [Part I of the compiler series]({% link _posts/2026-07-17-simplest-interpreter-write-yourself-a-compiler-part-i.md %}),
we started with a language that understands just one expression: two numbers separated by a plus sign.
Here is the same grammar as a railroad diagram:

```mermaid
railroad-ebnf-beta
title "The simplest expression grammar"

expression = whitespace number whitespace "+" whitespace number whitespace ;
number = sign? unsigned_number ;
unsigned_number = digits | digits "." digits | "." digits ;
digits = digit+ ;
sign = "+" | "-" ;
digit = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
whitespace = whitespace_character* ;
whitespace_character = "space" | "tab" | "newline" ;
```

Start on the left and follow a path to the right.
Every valid path describes an expression accepted by the interpreter, such as `40 + 2`, `-2 + .5`, or `1.25 + -3`.
