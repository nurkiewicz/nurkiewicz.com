---
title: "Compiling to intermediate representation: Write yourself a compiler, Part III"
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

Of course, such bytecode is encoded in binary, not as text.
The bytecode basically says: push constant `2` onto virtual operand stack, followed by `3`.
Then the instruction `iadd` pops two most recent values from the stack and replaces them with value `5`.

This sounds silly, but it's still way faster than reading through source code.
We'll talk more about virtual machines in the next part.
We'll also try to understand what's the point of generating IR and building a VM rather than, you know, just emitting proper assembly.
Now, it's time to emit some IR!

## Generating IR from source code

The core principle of intermediate representation is to reduce the source code into format more easily digestable by machine.
In our case we barely need a handful of instructions, sometimes called opcodes:

| Opcode | Hex | Meaning |
|--------|-----|---------|
| `PUSH` | 01  | Push 32-but number following this opcode onto the stack |
| `ADD`  | 2B  | Add |
| `SUB`  | 2D  | Subtract |
| `MUL`  | 2A  | Multiply |
| `DIV`  | 2F  | Divide |

We have one `PUSH` instruction which pushes (duh!) one number onto virtual operand stack.
Theoretically, that stack is infinite.
The remaining four opcodes decide what to do with two top-most numbers on the stack.
Bonus question: why did I choose such random hex codes, like `2B`, `2D`, etc.?
Never mind, in order to encode `2 + 3` expression in our IR, we need the following opcodes:

```
PUSH 2
PUSH 3
ADD
```

Where's the result?
All arithmetic opcodes pop two top-most numbers from the stack and push the result back.
So, after running this program our stack will contain just one entry: number `5`.
You might not see the beauty of this notation (called [_Reverse Polish Notation_](https://en.wikipedia.org/wiki/Reverse_Polish_notation)), but it'll become clear once we actually implement the virtual machine.

## Compiler implementation

Now it's time to turn human-readable source code (e.g. `2 + 3`) into bytecode.
Or, to be more precise, to the following sequence of bytes:

| Bytes | Explanation |
|--|--|
| `01 00 00 00 02` | `PUSH 2` |
| `01 00 00 00 03` | `PUSH 2` | 
| `2B`             | `ADD`    |

Two conventions: I'm using Big Endian for integers (for no apparent reason) and I'll add a small header with magic value [`PL/0`](https://en.wikipedia.org/wiki/PL/0) and version 0.1 of the format.
Magic value at the beginning of the file is always a good idea to quickly identify what kind of binary we deal with.
Version is useful to support compatibility and quickly discover no longer (or not yet!) supported features of the language.

OK, finally, this is how the core parts of the implementation look like.
Let's start with the basic data structure describing our entire program:

```go
type expression struct {
	left  int32
	op    byte
	right int32
}
```

Then, let's write a routine for turning string expression into `expression` instance:

```go
func parse(line string) (expression, error) {
	matches := exprRegex.FindStringSubmatch(line)
	if matches == nil {
		//syntax error
	}

	left, err := parseInt32(matches[1])
	if err != nil {
		return expression{}, err
	}
	right, err := parseInt32(matches[3])
	if err != nil {
		return expression{}, err
	}

	return expression{left: left, op: matches[2][0], right: right}, nil
}
```

As you can see we no longer mix parsing with execution.
We have proper data structure and separation of concerns!
The last part is just printing binary-encoded opcodes defined in `expression` type:

```go
var header = []byte{'P', 'L', '/', '0', 0x00, 0x01}

func writeProgram(w io.Writer, expr expression) error {
	program := make([]byte, 0, len(header)+11)
	program = append(program, header...)
	program = appendPush(program, expr.left)
	program = appendPush(program, expr.right)
	program = append(program, expr.op)

	if _, err := w.Write(program); err != nil {
		return fmt.Errorf("error: write program: %w", err)
	}
	return nil
}

func appendPush(program []byte, value int32) []byte {
	program = append(program, pushOpcode)
	return binary.BigEndian.AppendUint32(program, uint32(value))
}
```

We are too lazy to handle program arguments and files, so our compiler can only read source code from `stdin` and output IR to `stdout`:

```bash
$ echo '2 + 3' | ./compiler | xxd -u -g1 -c 16

00000000: 50 4C 2F 30   00 01   01 00 00 00 02   01 00 00 00 03  PL/0 .. ..... .....
00000010: 2B                                                     +
```

Hopefully, you can recognize two `PUSH` opcodes (`01 00 00 00 02` and `01 00 00 00 03`) as well as the terminating `2B` (`+` in ASCII).
In the next part we'll write a simple virtual machine: a program which takes this binary IR and executes it.

As always, the complete source code is [available on GitHub](https://github.com/nurkiewicz/writing-compiler/tree/part-iii) (`part-iii` branch).
