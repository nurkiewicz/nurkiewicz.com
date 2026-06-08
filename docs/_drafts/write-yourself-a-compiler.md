# Write yourself a compiler

## Table of contents

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
