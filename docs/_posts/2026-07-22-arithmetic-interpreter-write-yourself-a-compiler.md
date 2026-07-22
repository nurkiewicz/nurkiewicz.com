---
title: "Arithmetic interpreter: Write yourself a compiler, Part II"
layout: post
category: writing-compiler
tags: compiler interpreter go
---

In the [previous article]({% link _posts/2026-07-17-simplest-interpreter-write-yourself-a-compiler-part-i.md %}), we created the most naive interpreter, which can basically execute `number + number` expressions.
A logical extension is obviously to handle all basic operations: addition, subtraction, multiplication and division.
The time has come!

First, we need to teach our proto-compiler how to recognize all basic operators.
This simple code:

```go
const numberPattern = `\s*([+-]?(?:\d+\.?\d*|\.\d+))\s*`

var exprRegex = regexp.MustCompile(`^` + numberPattern + `([+])` + numberPattern + `$`)
```

becomes:

```go
var exprRegex = regexp.MustCompile(`^` + numberPattern + `([+\-*/])` + numberPattern + `$`)
```

The code is very similar; the only difference is that the regular expression now supports all sorts of expressions, such as `-2 * 3`, `3 - 5`, etc.
To break down this regular expression, let's extract even more primitives:

```go
const (
	ws       = `\s*`
	number   = `[+-]?\d+`
	operator = `[+\-*/]`
)

func c(pattern string) string {
	return `(` + pattern + `)`
}

var exprRegex = regexp.MustCompile(`^` + ws + c(number) + ws + c(operator) + ws + c(number) + ws + `$`)

```

The `exprRegex` looks a bit more high-level and better explains what we're actually trying to achieve.
Only `ws` (whitespace) and `c()` (_capture_) leak through the abstraction.

The second necessary change is in the interpreter itself.
It now needs to take the operator into account:

```go
switch op {
case '+':
	return a + b, nil
case '-':
	return a - b, nil
case '*':
	return a * b, nil
case '/':
	if b == 0 {
		return 0, errors.New("error: division by zero")
	}
	return a / b, nil
default:
	return 0, fmt.Errorf("error: unknown operator %q", string(op))
}
```

OK, once again, the outcome seems disappointing.
After all, we just parsed a string using a regular expression and, well, interpreted it.
But our tiny programming language is taking shape.
In the next installment, we'll actually try to "compile" it into an intermediate representation (IR).

The source code is available [here](https://github.com/nurkiewicz/writing-compiler/tree/part-ii) on the `part-ii` branch.
