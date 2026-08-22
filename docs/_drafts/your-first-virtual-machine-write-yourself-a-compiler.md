---
title: "Your First Virtual Machine: Write yourself a compiler, Part IV"
category: writing-compiler
tags: compiler interpreter go virtual-machine clojure reverse-polish-notation
---

In the previous article, [we emitted an intermediate representation (IR) for our programming language]({% post_url 2026-08-17-compiling-to-intermediate-representation-write-yourself-a-compiler %}) that is easier to process than source code.
However, we did not build a program that could read and execute that IR.
Such a program is called a virtual machine.
Technically, it's still an interpreter.
But instead of interpreting source code, it interprets IR.
Our IR is binary, compact, structured, and generally faster to interpret than the original source.
Moreover, as you'll see later, the VM's instruction set can express programs that our source language cannot produce yet!

## How IR works

As a reminder, an expression like this `2 + 3` is translated to the following IR:


| Bytes | Explanation |
|--|--|
| `01 00 00 00 02` | `PUSH 2` |
| `01 00 00 00 03` | `PUSH 3` | 
| `2B`             | `ADD`    |

Now we need a fairly simple program to read that binary code and actually execute it.
The main loop is quite simple:

1. Read one byte.
2. If it's a `PUSH` instruction, read the next four bytes as an integer and push it onto the operand stack.
3. If it's an arithmetic instruction such as `ADD`, pop the top two integers from the stack, perform the operation, and push the result back onto the stack.
4. If there are no more IR bytes to read, return the top value from the stack and terminate.
5. Go to step 1.

To visualize this, here's what the operand stack looks like after each instruction:


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
  case '-':
    result = left - right
  case '*':
    result = left * right
  case '/':
    result = left / right
  }
  stack = append(stack, result)
}

return stack[0], nil
```

`ip` stands for _instruction pointer_: it's an index into the byte array containing the IR code.
You can see how we move through the program, either pushing operands onto the stack or popping them to compute a result.
This simplified loop assumes valid bytecode, enough operands for every operation, and exactly one result on the stack.
It might not be clear why we use this unusual postfix notation (number, number, operator) rather than infix notation, such as `2 + 3`.
Be patient, you'll soon realize how powerful such notation is.

## Taking our VM for a test drive

The source code above is incomplete.
As usual, you'll find the complete [program on GitHub](https://github.com/nurkiewicz/writing-compiler/tree/part-iv) (branch `part-iv`).
But rather than inspecting every `err != nil`, let's run some code!

```bash
$ echo '2 + 3' | ./compiler | ./vm
5
```

Or, if you want to take it step-by-step:

```bash
$ echo '2 + 3' > file.pl0
$ cat file.p10 | ./compiler > file.ir
$ cat file.ir | ./vm 
5
```

In a sense, `file.ir` is our executable: it contains instructions for a virtual machine rather than for a physical CPU.
The operating system cannot execute it directly; our `vm` process must load and interpret it.
JVM `.class` files and .NET assemblies follow the same general model.

## The VM outgrows the source language

We accidentally created an interesting feature in our VM.
It isn't limited to simple `number op number` expressions.
For example, our source language doesn't support (yet) adding three numbers, like so: `1 + 2 + 3`.
But the VM is perfectly capable of executing the corresponding IR!

| Instruction | Stack after execution |
|--|--|
| `PUSH 1` | `1` |
| `PUSH 2` | `1`, `2` |
| `PUSH 3` | `1`, `2`, `3` |
| `ADD`    | `1`, `5` |
| `ADD`    | `6` |

Because our compiler doesn't support such expressions, we need to construct the binary IR code by hand.
That's fairly simple; we end up with the following `.ir` file:

```text
$ xxd -u -g1 -c 32 add.ir
00000000: 50 4C 2F 30 00 01 01 00 00 00 01 01 00 00 00 02 01 00 00 00 03 2B 2B
```

Let's break it down, instruction by instruction:

| Binary | Instruction | Operand stack after executing |
|--|--|--|
| 50 4C 2F 30 00 01 | Header | |
| 01 00 00 00 01 | `PUSH 1` | `1` |
| 01 00 00 00 02 | `PUSH 2` | `1`, `2` |
| 01 00 00 00 03 | `PUSH 3` | `1`, `2`, `3` |
| 2B | `ADD` | `1`, `5` |
| 2B | `ADD` | `6` |

Let's run this file to prove the VM is capable of loading it:

```sh
$ cat add.ir | ./vm
6
```

Amazing!
Our bytecode can already express more than the source language.
OK, but maybe you are still not convinced why our instructions use this unusual _Reverse Polish Notation_ (RPN)?
What's the point of having an operand stack and operators at the end?
Who the hell writes `1 + 2 + 3` as `1 2 3 + +`?
Stack-based virtual machines do, as do users of [many real calculators](https://lestallion.com/blogs/product-reviews/best-rpn-calculators-for-engineers-and-scientists).
Clojure's `(+ 1 2 3)` may look similar as well, but it uses prefix notation rather than RPN.

## Handling arbitrary arithmetic expressions

Our language is definitely not ready for them, but what about expressions like `2 * 3 + 4`?
Or `2 * (3 + 4)` (parentheses!), or even `2 + 3 * 4` (operator precedence!)?
It turns out that our VM is already capable of evaluating arbitrarily complex expressions composed of integer literals and its four arithmetic operators.
Let's take `2 * 3 + 4` as an example.
The following instructions compute it just fine:

| Instruction | Stack after execution |
|--|--|
| `PUSH 2` | `2` |
| `PUSH 3` | `2`, `3` |
| `MUL`    | `6` |
| `PUSH 4` | `6`, `4` |
| `ADD`    | `10` |

What if we add parentheses, turning `2 * 3 + 4` into `2 * (3 + 4)`?
No worries: the bytecode does not need to encode parentheses or precedence explicitly.
The compiler represents the intended evaluation order simply by arranging the instructions:


| Instruction | Stack after execution |
|--|--|
| `PUSH 2` | `2` |
| `PUSH 3` | `2`, `3` |
| `PUSH 4` | `2`, `3`, `4` |
| `ADD`    | `2`, `7` |
| `MUL`    | `14` |

I'll leave `2 + 3 * 4` as an exercise for the reader.
To illustrate how the same convention extends to variables, let's represent `b^2 - 4ac` symbolically.
Our current VM cannot load variables yet, so treat `PUSH a`, `PUSH b`, and `PUSH c` below as placeholders for future load instructions:

| Instruction | Stack after execution |
|--|--|
| `PUSH b` | `b` |
| `PUSH b` | `b`, `b` |
| `MUL`    | `b^2` |
| `PUSH 4` | `b^2`, `4` |
| `PUSH a` | `b^2`, `4`, `a` |
| `PUSH c` | `b^2`, `4`, `a`, `c` |
| `MUL`    | `b^2`, `4`, `a*c` |
| `MUL`    | `b^2`, `4*a*c` |
| `SUB`    | `b^2 - 4*a*c` |

As you can see, this awkward postfix notation lets bytecode encode the evaluation order without retaining parentheses or precedence rules.
Those rules still matter when the compiler parses the source expression, but the VM no longer needs to know about them.
Moreover, we can imagine other programming languages compiling to our admittedly primitive IR.
Supporting multiple source languages is one major advantage of mature runtime platforms such as the JVM and .NET.
We'll leave compiling to an existing virtual machine for the next part.
