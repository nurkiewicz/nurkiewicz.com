---
title: "Generating Java bytecode: Write yourself a compiler, Part V"
category: writing-compiler
tags: compiler interpreter go jvm java
---

Last time [we created a virtual machine for our toy language]({% post_url 2026-08-17-compiling-to-intermediate-representation-write-yourself-a-compiler %}).
I think you can agree that designing a language which barely recognizes expressions like `2 + 3w` and building a brand-new virtual machine for it seems a bit tedious.
So what about keeping our microscopic language for now, but running it on a real, production-ready, battle-proven virtual machine?
Like the [Java Virtual Machine](https://en.wikipedia.org/wiki/Java_virtual_machine)?
Our task for today is to emit JVM bytecode in the form of a valid `.class` file.
That file can then be fed directly to the JVM to run our program.

How's that even possible?
Isn't the Java Virtual Machine made for, you know, Java?
Not really. There are dozens of programming languages that target the JVM, including [Scala](https://www.scala-lang.org), [Kotlin](https://kotlinlang.org), [Clojure](https://clojure.org), and [Groovy](https://groovy-lang.org), just to [name a few](https://en.wikipedia.org/wiki/List_of_JVM_languages).
So, let's just say we are building yet another JVM language!

## Getting familiar with the JVM bytecode

Superficially, JVM bytecode is very similar to the IR we built.
Here's the relevant code of our compiler, generating JVM-compatible bytecode:

```go
code = appendPush(code, expr.left, pool)
code = appendPush(code, expr.right, pool)
opcode, ok := map[byte]byte{
  '+': opcodeIadd,
  '-': opcodeIsub,
  '*': opcodeImul,
  '/': opcodeIdiv,
}[expr.op]
```

Opcodes are defined e.g. [here](https://en.wikipedia.org/wiki/List_of_JVM_bytecode_instructions).
So, push the first operand, push the second operand, and execute the operator instruction.
The instruction pops the two operands and pushes the result back.
Just like our custom VM.
For example, the expression `2 + 3` results in the following bytecode:

```
iconst_2
iconst_3
iadd
```

However, the instruction used to push an integer onto the operand stack depends on its value:

| Value (N) | Opcode | Argument |
|---|---|---|
| -1 | `iconst_m1` | - |
| 0 to 5 | `iconst_N` | - |
| -128 to 127 | `bipush` | N |
| -32768 to 32767 | `sipush` | N |
| N | `ldc` or `ldc_w` | C |

The JVM uses several instruction families just to push an integer onto the operand stack (!)
For values between `-1` and `5`, there's a dedicated instruction for each number (without arguments).
Other values fitting in a signed byte or signed 16-bit integer are stored directly in the `bipush` or `sipush` instruction.
Once a constant no longer fits in 16 bits, we use `ldc` or `ldc_w`.
These instructions load a value from the so-called _constant pool_ at index `C`; `ldc_w` supports a wider constant-pool index than `ldc`.

## Constant pool

The designers of the Java Virtual Machine decided that constants and symbolic references used by instructions should be kept outside the method code.
That special place is called the _constant pool_.
Moreover, if the same constant is used in more than one place, we can store it once and reuse its constant-pool entry.
The constant pool also contains strings, class and method references, and a bunch of other fixed values.
This makes our lives a little bit more complicated.
While `2 + 3` uses one set of bytecode instructions:

```
iconst_2
iconst_3
iadd
```

The same expression, but with higher values (`65536 + 65537`), is represented by completely different instructions:

```
3: ldc           #22                 // int 65536
5: ldc           #23                 // int 65537
7: iadd
```

The instructions `ldc #22` and `ldc #23` basically mean "_load the values located at indices 22 and 23, respectively, in the constant pool._"
Because the constant pool appears before the methods in a `.class` file, we must collect its entries before serializing the complete class.

## Building a fully functional `.class` file

There used to be a ton of ceremony to write a simple `"Hello, world!"` program in Java.
There's also a ton of ceremony in creating a proper Java class.
It's almost as if JVM bytecode is supposed to be as verbose as the language itself.
Boilerplate tradition.

There aren't many good Go libraries for creating Java `.class` files, so I'm building everything from scratch.
Just look how much structure we have to output for a minimal class:

```go
var class bytes.Buffer
u4(&class, 0xCAFEBABE)                  // magic
u2(&class, 0)                           // minor_version
u2(&class, 52)                          // major_version: Java 8
u2(&class, uint16(len(pool.entries)+1)) // constant_pool_count
for _, entry := range pool.entries {
  class.Write(entry)
}
u2(&class, 0x0021)                                             // public, super
u2(&class, thisClass)                                          // this_class
u2(&class, superClass)                                         // super_class
u2(&class, 0)                                                  // interfaces_count
u2(&class, 0)                                                  // fields_count
u2(&class, 1)                                                  // methods_count
method(&class, mainName, mainDescriptor, codeName, 3, 1, code) // max_stack, max_locals
u2(&class, 1)                                                  // attributes_count
u2(&class, sourceFileName)                                     // attribute_name_index
u4(&class, 2)                                                  // attribute_length
u2(&class, sourceFile)                                         // sourcefile_index
return class.Bytes(), nil
```

You can recognize the infamous `CAFE BABE` header, followed by the Java version we target.
I'm old-school, so our compiler will target Java 8.
Thanks to Java's legendary backward compatibility, such a class can also run on newer JVMs.
Just for fun, here's a complete Java class running the `65536 + 65537` "program":

```
$ echo '65536 + 65537' | ./jvm-compiler > PL0.class
$ xxd -u -g1 -c 16 PL0.class
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

Most of the above is just `.class` file structure and constant-pool data.
The executable code of our `main` method takes just a few bytes:

```
00 00 00 0C B2 00 0D 12 16 12 17 60 B6 00 13 B1
```

Within that method, bytes `12 16 12 17 60` represent the arithmetic expression itself.
These bytes correspond to the following bytecode:


```
3: ldc           #22                 // int 65536
5: ldc           #23                 // int 65537
7: iadd
```

The `#22` and `#23` are just indices in the constant pool:

```
Constant pool:
  #22 = Integer            65536
  #23 = Integer            65537
```

The constant pool is, of course, also part of the `.class` file:

```
000000e0: 07 50 4C 30 2E 70 6C 30 03 00 01 00 00 03 00 01  .PL0.pl0........
000000f0: 00 01 00 21 00 02 00 04 00 00 00 00 00 01 00 09  ...!............
```

To be precise, the following bytes represent these two entries.
The `03` tag means `Integer`, followed by the big-endian representation of `0x00010000` or `0x00010001`.

```
03 00 01 00 00 
03 00 01 00 01 
```

## Running on the JVM

Let's compile our tiny program and see if Java actually recognizes it!

```bash
$ echo '65536 + 65537' | ./jvm-compiler > com/nurkiewicz/PL0.class
$ java com.nurkiewicz.PL0
131073
```

**It's alive!**
The first command feeds the `jvm-compiler` process (full source code here: [`main.go`](https://github.com/nurkiewicz/writing-compiler/blob/part-v/cmd/jvm-compiler/main.go)).
The second command executes the generated binary `.class` file on a real Java Virtual Machine.
We managed to write a compiler which takes a program written in our imaginary (and extremely simple) language and creates a proper Java class.

## Disassembling the generated program

Java ships with the `javap` tool, which takes a `.class` file and disassembles it back into a human-readable representation of its bytecode.
Here's the complete program we managed to generate (cleaned up for brevity):

```bash
$ javap -v -c PL0.class
public class com.nurkiewicz.PL0
  minor version: 0
  major version: 52
  flags: (0x0021) ACC_PUBLIC, ACC_SUPER
  this_class: #2                          // com/nurkiewicz/PL0
  super_class: #4                         // java/lang/Object
  interfaces: 0, fields: 0, methods: 1, attributes: 1
Constant pool:
   #1 = Utf8               com/nurkiewicz/PL0
   #2 = Class              #1             // com/nurkiewicz/PL0
   #3 = Utf8               java/lang/Object
   #4 = Class              #3             // java/lang/Object
   #5 = Utf8               Code
   #6 = Utf8               main
   #7 = Utf8               ([Ljava/lang/String;)V
   #8 = Utf8               java/lang/System
   #9 = Class              #8             // java/lang/System
  #10 = Utf8               out
  #11 = Utf8               Ljava/io/PrintStream;
  #12 = NameAndType        #10:#11        // out:Ljava/io/PrintStream;
  #13 = Fieldref           #9.#12         // java/lang/System.out:Ljava/io/PrintStream;
  #14 = Utf8               java/io/PrintStream
  #15 = Class              #14            // java/io/PrintStream
  #16 = Utf8               println
  #17 = Utf8               (I)V
  #18 = NameAndType        #16:#17        // println:(I)V
  #19 = Methodref          #15.#18        // java/io/PrintStream.println:(I)V
  #20 = Utf8               SourceFile
  #21 = Utf8               PL0.pl0
  #22 = Integer            65536
  #23 = Integer            65537
{
  public static void main(java.lang.String[]);
    Code:
      stack=3, locals=1, args_size=1
         0: getstatic     #13                 // Field java/lang/System.out:Ljava/io/PrintStream;
         3: ldc           #22                 // int 65536
         5: ldc           #23                 // int 65537
         7: iadd
         8: invokevirtual #19                 // Method java/io/PrintStream.println:(I)V
        11: return
}
SourceFile: "PL0.pl0"
```

You can see the entire constant pool, including references to our base class (`java/lang/Object`) and the `PrintStream.println` method used for printing to `stdout`.
Our tiny little program is there, at the very bottom.
Just for fun, we can include the source file name, which will appear in many debugging tools.

As usual, the source code for this part is available on GitHub under [`part-v`](https://github.com/nurkiewicz/writing-compiler/tree/part-v) branch.

{% include writing-compiler.md %}
