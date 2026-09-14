---
title: "Interoperability with Java: Write yourself a compiler, Part VI"
category: writing-compiler
tags: compiler interpreter go jvm java
---

A small addendum to our previous article [where we wrote functional compiler targetting JVM bytecode]({% post_url 2026-08-17-compiling-to-intermediate-representation-write-yourself-a-compiler %}), let's discuss interoperability with the JVM.
The biggest win from using a well-established virtual machine is gaining access to the entire ecosystem.
Let's say I'm a Java developer.
I can write a program in my favorite language like so:

```java
package com.example;

import com.nurkiewicz.PL0;

public final class PL0Interop {
	public static void main(String[] args) {
		PL0.main(null);
	}
}
```

Look closely!
This program casually imports the `com.nurkiewicz.PL0` class.
The class that we generated from our toy language!
The client code simply calls a method from our compiled class, and it just works!
See for yourself:

```bash
$ javac -cp . com/example/PL0Interop.java
$ java -cp . com.example.PL0Interop

131073
```

The `javac` command compiles the `PL0Interop.java` file into `PL0Interop.class`.
The compilation works even though no Java source exists for the referenced `PL0` class.
That class is already available as a `.class` file, and the `javac` compiler doesn't care that it came from some alien language.
The second line just runs the `PL0Interop` program.
It works just fine, printing the result.

Notice that such integration is much broader.
Any other JVM language, like Scala or Kotlin, could interoperate with our language.
Moreover, our toy language can take advantage of the Java standard library—for example, by using `System.out.println()` to print results.

But the benefits don't end here.
A Java compiler compiling the equivalent Java expression would not even emit both `ldc` instructions followed by `iadd`.
Instead, it would evaluate the constant expression at compile time and emit the hard-coded value `131073`.
After all, the result is known at compile time, so why bother the CPU with the addition?
Even though our compiler is not nearly as smart, a JVM implementation with a just-in-time compiler may still be.
If this method becomes hot, the JIT compiler can fold the constant addition and replace it with the result.

## Adding line numbers mapping

Last but not least, we could add bytecode index to line number mapping, as well as local variable name table.
These pieces of metadata would allow debuggers to step through our code interactively, mapping instructions to our toy language!
Just for fun, I added `LineNumberTable` to our generated `.class` file.
Makes very little sense, because our language currently supports just one-line programs, but still...

```bash
echo '2 + 40' | ./jvm-compiler > PL0.class; javap -v -c PL0.class
...
{
  public static void main(java.lang.String[]);
    descriptor: ([Ljava/lang/String;)V
    flags: (0x0009) ACC_PUBLIC, ACC_STATIC
    Code:
      stack=3, locals=1, args_size=1
         0: getstatic     #14                 // Field java/lang/System.out:Ljava/io/PrintStream;
         3: iconst_2
         4: bipush        40
         6: iadd
         7: invokevirtual #20                 // Method java/io/PrintStream.println:(I)V
        10: return
      LineNumberTable:
        line 1: 3
}
```

The `line 1: 3` basically means: bytecode at index 3 (`iconst_2`) maps to line 1 of the source file.
This table will allow debuggers to highlight proper line when executing bytecode.

As usual, the source code for this part is available on GitHub under [`part-vi`](https://github.com/nurkiewicz/writing-compiler/tree/part-vi) branch.

{% include writing-compiler.md %}
