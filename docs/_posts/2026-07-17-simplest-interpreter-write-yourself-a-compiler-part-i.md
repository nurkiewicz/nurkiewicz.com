---
title: "The simplest interpreter: Write yourself a compiler, Part I"
layout: post
category: writing-compiler
tags: compiler interpreter lexer go
---

I've always felt that writing a compiler is the most romantic software engineering task.
You're writing a program that reads textual instructions describing precisely what a computer should do.
Do not confuse this with prompting an LLM, where you write vague, verbose instructions that only loosely describe what a computer might do.
But I digress.

I'm starting a new series of articles in which each part will bring us one tiny step closer to a full-blown compiler.
I'll make small, incremental improvements in each step.
They'll be easy to grasp, but each will still add some value.
It's going to be the most agile compiler ever.

We'll start by creating an extremely simple interpreter.
It will read a string containing an addition (e.g. `40 + 2`), parse it, evaluate it, and print the answer (`42`).
This doesn't sound like a compiler, that's for sure.
More like a dumb calculator.
But, believe it or not, it's a giant step toward building an actual standalone compiler.

Theory aside, let's dive into code.
We need two components: a lexer that also recognizes our one-rule grammar and an evaluator.

## Lexer

The example code is written in Go.
We need a piece of logic that takes a string and splits it into three tokens:

```go
const numberPattern = `\s*([+-]?\d*\.?\d+)\s*`

var exprRegex = regexp.MustCompile(`^` + numberPattern + `([+])` + numberPattern + `$`)
```

We start by defining a number and an expression using regular expressions.
Like it or not, regular languages are at the heart of many lexers, and regexes are a convenient way to describe them.
They let us group sequences of characters into logical units (_tokens_).
In our case, an expression always consists of three tokens: the first number, `+`, and the second number.

For this tiny language, one regex both validates the expression's structure and tokenizes the input:

```go
func interpret(line string) (float64, error) {
	matches := exprRegex.FindStringSubmatch(line)
	if matches == nil {
		if strings.TrimSpace(line) == "" {
			return 0, errors.New("error: empty expression")
		}
		return 0, fmt.Errorf("error: expected \"number + number\", got %q", line)
	}

	left, _, right := matches[1], matches[2], matches[3]
}
```

As you can see, we successfully extracted logical tokens from a simple string.
The actual evaluation is unsurprisingly straightforward:

```go
a, err := strconv.ParseFloat(left, 64)
if err != nil {
	return 0, fmt.Errorf("error: invalid number %q", left)
}
b, err := strconv.ParseFloat(right, 64)
if err != nil {
	return 0, fmt.Errorf("error: invalid number %q", right)
}

return a + b, nil
```

For the time being, the only thing our _interpreter_ can do is add two numbers:

```bash
echo '2 + 1' | go run main.go
3
```

It works!
I omitted some plumbing related to reading from `stdin`; you can find it on [GitHub](https://github.com/nurkiewicz/writing-compiler/tree/part-i) (`part-i` branch).
In the next episode, we'll handle all arithmetic operations, not just addition.
If you are a bit disappointed, bear with me.
We will soon learn how to skip the interpretation step and generate runnable artifacts (executables).
