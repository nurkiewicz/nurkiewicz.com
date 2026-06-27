# The simplest interpreter: Write yourself a compiler, Part I

I always felt that writing a compiler is the most romantic software engineering task.
You're writing a program which reads some textual instructions describing precisely what computer can do.
Do not confuse with LLM, where you write vague, verbose instructions somewhat describing what computer might do.
But I digress.

I'm starting a new series of articles, where each part will bring us one step closer to a full-blown compiler.
In each step I'll try to make small, incremental improvements.
So small that they are easy to grasp, but always bringing some value.
It's going to be the most agile compiler ever.

We'll start by creating an extremely simple interpreter.
It will read a string with addition (e.g. `40 + 2`), parse it, execute it, and print the answer (`42`).
This doesn't sound like a compiler, that's for sure.
More like a dumb calculator.
But, believe it or not, it's a giant step for building the actual standalone compiler.

Theory aside, let's dive into code.
We actually need two components: lexer and evaluator.

## Lexer

The example code is written in Go.
We need a piece of logic which takes a string and splits it into two numbers:

```go
const numberPattern = `\s*([+-]?(?:\d+\.?\d*|\.\d+))\s*`

var exprRegex = regexp.MustCompile(`^` + numberPattern + `([+])` + numberPattern + `$`)
```

We start by defining what's a number and what's an expression, using regular expressions.
You like it or not, regexes are at the heart of every compiler.
They group sequences of characters into logical units (_tokens_).
In our case the expression always consist of 3 tokens: number, `+` and second number.

After describing all valid tokens, using regular expressions, we can finally tokenize our input:

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
Now the actual execution, which is unsurprisingly pretty straightforward:

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
For the time being, the only thing our _interpret_ can do is adding two numbers:

```bash
echo '2 + 1' | go run main.go
3
```

It works!
I omitted some plumbing related to reading `stdin`, you can find it on GitHub
We can almost call 

- `2 + 3` - interpreter in Go
- Add minus, multiplication and division. Show operator precedence is not obeyed (`2 + 2 * 2`)
- `2 + 3` - using arbitrary binary opcodes
- `2 + 3` - custom virtual machine using JVM opcodes
- `2 + 3` - wrap with JVM `.class` file
- Show that sequence of opcodes (`2 + 3 + 4 + 5...`) also works
- `2 + 3` compiled as LLVM
- `2 + 3` compiled to target assembly (show it's not portable and not optimized), e.g. every compiler will just replace 2 + 3 with `5`
- Modularization - proper lexer
- Add proper grammar with operator precedence for binary multiplication and addition
- Add support for parentheses, proper lexer
- Support for assignment (no re-assignment?)
- Is our language Turing-complete?
