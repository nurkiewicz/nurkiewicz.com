---
title: "Arithmetic interpreter: Write yourself a compiler, Part II"
layout: post
category: writing-compiler
tags: compiler interpreter go
---

In the 

[previous article]({% raw %}{% link _posts/2026-07-17-simplest-interpreter-write-yourself-a-compiler-part-i.md %}{% endraw %})

previous article we created the most naive interpreter which can basically execute `number + number` expressions.
A logic extension is obviously handling all basic operations: addition, subtraction, multiplication and division.
The time has come!

First of all, we need to teach our proto-compiler how to tokenize all basic operators.
The simple:

```go
const numberPattern = `\s*([+-]?(?:\d+\.?\d*|\.\d+))\s*`

var exprRegex = regexp.MustCompile(`^` + numberPattern + `([+])` + numberPattern + `$`)
```

Becomes:

```go
var exprRegex = regexp.MustCompile(`^` + numberPattern + `([+\-*/])` + numberPattern + `$`)
```

Very similar, the only difference is that a regular expression now supports all sorts of expressions, like `-2 * 3`, `3 - 5`, etc.
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
```


