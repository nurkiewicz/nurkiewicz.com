---
title: "Your First Virtual Machine: Write yourself a compiler, Part IV"
category: writing-compiler
tags: compiler interpreter go virtual-machine
---

In the previous article [we emitted intermediate representation (IR) for our programming language]({% post_url 2026-08-17-compiling-to-intermediate-representation-write-yourself-a-compiler %}) which is supposedly easier to parse than source code.
However, we did not build a program to actually read that IR and interpret it.
Such a program is called a virtual machine.
Technically, it's still an interpreter.
But it doesn't interpret source code, but IR.
IR is binary, more compact, more structured, and, in general, faster to interpret.
Moreover, as you'll see later, VM might be more capable that the language producing the IR in the first place!

## How IR works

As a reminder, an expression like this `2 + 3` is translated to the following IR:


| Bytes | Explanation |
|--|--|
| `01 00 00 00 02` | `PUSH 2` |
| `01 00 00 00 03` | `PUSH 3` | 
| `2B`             | `ADD`    |

Now we need a fairly simple program to read that binary code and actually execute it.
The main loop is pretty simple:

1. Read one byte
2. If it's a `PUSH` instruction, push the next 4 bytes (integer) onto operand stack
3. If it's an arithmetic instruction like `ADD`, pop the last two integers from the stack, perform operation (add numbers), push the result back onto stack
4. If there are no more IR bytes to read, print the topmost value from the stack and terminate
5. Go to step 1

To visualize this, here's how operand stack looks like after each instruction:


| Instruction | Stack after execution |
|--|--|
| `PUSH 2` | `2` |
| `PUSH 3` | `2`, `3` |
| `ADD`    | `5` |

## Core loop

Stripping all error handling code and edge cases, this is how the main loop of our VM looks like:

```go
var stack []int32
for ip := 0; ip < len(program); {
  opcode := program[ip]
  ip++

  if opcode == pushOpcode {
    stack = append(stack, int32(binary.BigEndian.Uint32(program[ip:ip+4])))
    ip += 4
    continue
  }

  right := stack[len(stack)-1]
  left := stack[len(stack)-2]
  stack = stack[:len(stack)-2]

  var result int32
  switch opcode {
  case '+':
    result = left + right
  ... //other operators follow
  }
  stack = append(stack, result)
}

return stack[0], nil
```

`ip` stands for _instruction pointer_ - it's basically an index iterating over the file containing IR code.
You can see how we navigate through the file, either accumulating operands on the stack, or popping the values back, in order to compute the result.
It might not be clear why we use this weird postfix notation (number, number, operator), rather than storing operators in infix notation, e.g.: `PUSH 2`, `ADD` `PUSH 3`.
Be patient, you'll soon realize how powerful such notation is.

## Taking our VM for the test drive

The source code above is incomplete, as usual, you'll find the complete program on GitHub (branch `part-iv`).
But rather than inspecting every `err != nil` let's run some code!

```bash
$ echo '2 + 3' | ./compiler | ./vm
5
```

Or, if you want to take it step-by-step:

```bash
$ echo '2 + 3' > file.pl0
cat file.pl0 | ./compiler > file.ir
cat file.ir | ./vm
5
```

Technically speaking, the `file.ir` is _THE_ executable.
It contains runnable code (just like your `.exe` file).
It just so happens that this runnable code targets a CPU/machine that doesn't exist.
It's emulated by our `vm` process.
If you think it's cheating, this is exactly how `.class`/`.jar` files or DLL files are "executable" in Java and C# respectively.

## VM outgrows the source language

There's some interesting feature that we created by accident in our VM.
It turns out it's not limited to simple `number op number` expressions.
For example, our source language doesn't support (yet) adding three numbers, like so: `1 + 2 + 3`.
But the VM is perfectly capable of running such IR code!


| Instruction | Stack after execution |
|--|--|
| `PUSH 1` | `1` |
| `PUSH 2` | `1`, `2` |
| `PUSH 3` | `1`, `2`, `3` |
| `ADD`    | `1`, `5` |
| `ADD`    | `6` |


