---
title: "Generating Java bytecode: Write yourself a compiler, Part ?"
category: writing-compiler
tags: compiler interpreter go
---

Last time [we craeted a virtual machine for our toy language]({% post_url 2026-08-17-compiling-to-intermediate-representation-write-yourself-a-compiler %}).
I think you can agree that writing a language which barely recognizes `2 + 3` expressions and building a branch new virtual machine for it seems a bit tedious.
So what about keeping our microscopic language, but running it on a real, production-ready, battle-proven virtual machine?
Like Java Virtual Machine?
Our task for today is emit JVM bytecode in the form of a valid `.class` file.
That file can then be fed directly to JVM and run our program.

How's that even possible?
Isn't Java Virtual Machine made for, you know, Java?
Not really, there are dozens of programming languages, like [Scala](https://www.scala-lang.org), [Kotlin](https://kotlinlang.org), [Clojure](https://clojure.org), [Groovy](https://groovy-lang.org), just to [name a few](https://en.wikipedia.org/wiki/List_of_JVM_languages).
So, let's just say we are building yet another JVM language!

## Getting familiar with the JVM bytecode

Superficially, JVM bytecode is very similar to the IR we build 

```
bash-3.2$ xxd -u -g1 -c 16 PL0.class
00000000: CA FE BA BE 00 00 00 34 00 18 01 00 12 63 6F 6D  .......4.....com
00000010: 2F 6E 75 72 6B 69 65 77 69 63 7A 2F 50 4C 30 07  /nurkiewicz/PL0.
00000020: 00 01 01 00 10 6A 61 76 61 2F 6C 61 6E 67 2F 4F  .....java/lang/O
00000030: 62 6A 65 63 74 07 00 03 01 00 04 43 6F 64 65 01  bject......Code.
00000040: 00 04 6D 61 69 6E 01 00 16 28 5B 4C 6A 61 76 61  ..main...([Ljava
00000050: 2F 6C 61 6E 67 2F 53 74 72 69 6E 67 3B 29 56 01  /lang/String;)V.
00000060: 00 10 6A 61 76 61 2F 6C 61 6E 67 2F 53 79 73 74  ..java/lang/Syst
00000070: 65 6D 07 00 08 01 00 03 6F 75 74 01 00 15 4C 6A  em......out...Lj
00000080: 61 76 61 2F 69 6F 2F 50 72 69 6E 74 53 74 72 65  ava/io/PrintStre
00000090: 61 6D 3B 0C 00 0A 00 0B 09 00 09 00 0C 01 00 13  am;.............
000000a0: 6A 61 76 61 2F 69 6F 2F 50 72 69 6E 74 53 74 72  java/io/PrintStr
000000b0: 65 61 6D 07 00 0E 01 00 07 70 72 69 6E 74 6C 6E  eam......println
000000c0: 01 00 04 28 49 29 56 0C 00 10 00 11 0A 00 0F 00  ...(I)V.........
000000d0: 12 01 00 0A 53 6F 75 72 63 65 46 69 6C 65 01 00  ....SourceFile..
000000e0: 07 50 4C 30 2E 70 6C 30 03 00 01 00 00 03 00 01  .PL0.pl0........
000000f0: 00 01 00 21 00 02 00 04 00 00 00 00 00 01 00 09  ...!............
00000100: 00 06 00 07 00 01 00 05 00 00 00 18 00 03 00 01  ................
00000110: 00 00 00 0C B2 00 0D 12 16 12 17 60 B6 00 13 B1  ...........`....
00000120: 00 00 00 00 00 01 00 14 00 00 00 02 00 15        ..............
```

Most of the above is just Java bytecode boilerplate.
Our very own `65536 + 65537` program takes just a few bytes:

```
00000110: 00 00 00 0C B2 00 0D 12 16 12 17 60 B6 00 13 B1  ...........`....
```

Bytes `12 16 12 17 60` basically represent our entire program, the rest is just `.class` file ceremony.
These bytes correspond to the following bytecode:


```
3: ldc           #22                 // int 65536
5: ldc           #23                 // int 65537
7: imul
```

The `#22` and `#23` are just indices in the constant pool:

```
Constant pool:
  #22 = Integer            65536
  #23 = Integer            65537
```

The constant pool of course is also part of the bytecode:

```
000000e0: 07 50 4C 30 2E 70 6C 30 03 00 01 00 00 03 00 01  .PL0.pl0........
000000f0: 00 01 00 21 00 02 00 04 00 00 00 00 00 01 00 09  ...!............
```

To be precise, the following bytes represent these two entries.
`03` constant means `integer` followed by Big-endian `0x010000` and `0x010001.`

```
03 00 01 00 00 
03 00 01 00 01 
```

{% include writing-compiler.md %}
