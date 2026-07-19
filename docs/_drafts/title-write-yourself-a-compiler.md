---
title: "Template: Write yourself a compiler, Part ?"
layout: post
category: writing-compiler
tags: compiler interpreter go
---

- Arithmetic addition interpreter: Write yourself a compiler, Part I
- Arithmetic interpreter: Write yourself a compiler, Part II
- The simplest virtual machine: Write yourself a compiler, Part III
- Your first JVM language: Write yourself a compiler, Part IV
- Create standalone binary with LLVM: Write yourself a compiler, Part V
- Generate assembly by hand: Write yourself a compiler, Part VI
- Support operator precedence: Write yourself a compiler, Part VII
- Support parentheses: Write yourself a compiler, Part VIII

## Table of contents

- `2 + 3` - interpreter in Go
- Add minus, multiplication and division. Show operator precedence is not obeyed (`2 + 2 * 2`)
- `2 + 3` - using arbitrary binary opcodes
- `2 + 3` - custom virtual machine using JVM opcodes
- `2 + 3` - wrap with JVM `.class` file
- Show that sequence of opcodes (`2 + 3 + 4 + 5...`) also works
- Compile to WASM/WAT file
- `2 + 3` compiled as LLVM
- `2 + 3` compiled to target assembly (show it's not portable and not optimized), e.g. every compiler will just replace 2 + 3 with `5`
- Modularization - proper lexer
- Add proper grammar with operator precedence for binary multiplication and addition
- Add support for parentheses, proper lexer
- Support for assignment (no re-assignment?)
- Is our language Turing-complete?
