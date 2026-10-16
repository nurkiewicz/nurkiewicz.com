---
title: "Native binary with LLVM: Write yourself a compiler, Part VII"
category: writing-compiler
tags: compiler interpreter go llvm
---

So far, our every compiler produced non-standalone artifacts.
Even `.class` files [created last time]({% post_url 2026-09-15-generating-java-bytecode-write-yourself-a-compiler %}) still require Java Virtual Machine to interpret them.
I think it's about time to actually produce self-sufficient binary which only needs an operating system and not much more than that to run.
In general, this means producing machine code which target CPU/OS can run directly, not via some intermediate layer.

Historically, that'd mean our compiler must produce valid assembly/machine code.
Moreover, the compiler must be capable of producing valid, efficient code for each architecture (x86, ARM, Risc V, WebAssembly...)
That's how many compilers (like Go compiler) work.
But these days we have a simpler option.

## LLVM frontend

[LLVM](https://www.llvm.org/) is a set of tools helping to implement any compiler for any architecture.
Compilers for languages like C, C++, Objective-C (via `clang`), Swift, Rust and many more, use it to produce binaries.
In general, compilers built on top of LLVM implement so-called _LLVM frontend_.
It's a bespoke code which translates language-specific source code into LLVM intermediate representation (IR).
The concept of IR (or bytecode) is [familiar to us]({% post_url 2026-08-17-compiling-to-intermediate-representation-write-yourself-a-compiler %}).
But in this case, the IR is not the final product, it's just intermediate artifact.
Then, IR is immediately compiled into platform-dependent machine code using _LLVM backend_

## LLVM backend

LLVM provides dozens of backends, each one targeting a different platform.
x86, ARM, RISC-V, PowerPC... WebAssembly, eBPF programs - you name it.
As long as you produced valid IR, LLVM will do its best to compile it to target machine.
Moreover, LLVM backend has a set of platform-agnostic and platform-dependent optimizations.
If your IR code is inefficient it'll be heavily optimized as part of the compilation process.

This separation of concerns (frontend and backend) has two great benefits:

* if you want to implement a new programming language, just write a new frontend and you immediately get a compiler for every obscure hardware platform on the planet
* if a new, even more obscure platform appears, new LLVM backend will open that platform for every single programming language out there having an LLVM frontend

This separation means we no longer duplicate machine code generation work for each language and platform.
That's a extremely hard work, better left to professionals with real hardware sympathy.

## Limitations

Just because LLVM backend exists, doesn't mean you can take any frontend producing IR and run it on any platform.
Also, LLVM doesn't provide higher-level concepts like garbage collection.
That's still on you.
Last but not least, bespoke compiler might be faster than a collection of chained LLVM tools.
That was historically the reason why Go doesn't use it.

## Our first LLVM IR

Before jumping into the implementation of our custom LLVM frontend, let's see it in action.
Here, we consume the simplest `2 + 40` "program" into valid LLVM IR via `echo '2 + 40' | bin/llvm-compiler`:

```llvm
@format = constant [4 x i8] c"%d\0A\00"

declare i32 @printf(i8* %format, ...)

define i32 @main() {
main-block:
	%0 = add i32 2, 40
	%1 = getelementptr [4 x i8], [4 x i8]* @format, i32 0, i32 0
	%2 = call i32 (i8*, ...) @printf(i8* %1, i32 %0)
	ret i32 0
}

```

The only thing to care about from the snippet above is:

```llvm
%0 = add i32 2, 40
```

It's the actual `2 + 40` part.
The rest is just IR boilerplate and `printf` boilerplate needed to put the result on screen.
At this point, we can take this IR and compile it to native binary:

```bash
export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
echo "40 + 2" | ./bin/llvm-compiler > expression.ll
opt -O3 -S expression.ll -o expression.opt.ll
llc -O3 -filetype=obj -mcpu=native expression.opt.ll -o expression.o
ld expression.o -o expression -lSystem -syslibroot "$(xcrun --show-sdk-path)" -arch arm64 -dead_strip
./expression
```

{% include writing-compiler.md %}
