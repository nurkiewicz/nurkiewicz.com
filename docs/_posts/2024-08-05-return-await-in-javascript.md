---
title: "Is 'return await' redundant or necessary in JavaScript?"
tags: JavaScript
layout: post
---

In JavaScript, should we `await` on a returned promise or not?

```js
async function foo() {
    //...
    return await waitAndMaybeReject();
}
```

If we remove `await`, the code compiles and behaves exactly the same way.
Almost.

## TL;DR:

Always add `await` and gain better async stack traces.

## Longer version

I went through the rabbit hole of `return` followed by `await` or not.
Until today I thought it was redundant.
Now I know it's crucial.
I thought it's complicated, but actually it's not.
Although there are [many (wrong) articles](https://jakearchibald.com/2017/await-vs-return-vs-return-await/) claiming `await` is unnecessary, it actually is very valuable.

For starters, `await` is definitely needed when wrapped within `try-catch`:

```js
async function foo() {
    try {
        return await waitAndMaybeReject();
 } catch(error) {
        console.error(error);
 }
}
```

Without `await`, errors thrown from `waitAndMaybeReject()` will not be captured by `catch` statement.
But that's the basics.
Aside from error checking, `return` followed by `await` seemed redundant.
There even used to be an eslint rule [`no-return-await`](https://eslint.org/docs/latest/rules/no-return-await) that suggested removing redundant `return await` instead of simple `await`.
However, the rule [became deprecated](https://github.com/eslint/eslint/pull/17417), as explained in [Remove no-return-await rule #12246](https://github.com/eslint/eslint/issues/12246), as well as in [Documentation of "no-return-await" #11878](https://github.com/eslint/eslint/issues/11878).
This rule was also [removed](https://github.com/standard/standard/issues/1442) from [JavaScript Standard Style](https://github.com/standard/standard) guide.

There's one big reason to keep `await` - a more descriptive stack trace when promise got rejected.
Example taken from [this ticket](https://github.com/eslint/eslint/issues/11878#issuecomment-505363819):

```js
(function () {
  async function foo() {
    return await bar();
 }

  async function bar() {
    await Promise.resolve();
    throw new Error('BEEP BEEP');
 }

  foo().catch(error => console.log(error.stack));
})()
```

This yields proper stack trace (tested on Node 21.6.2):

```
> Error: BEEP BEEP
 at bar (REPL13:9:11)
 at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
 at async foo (REPL13:4:12)
```

However, if we remove `await` from `foo()` function:

```js
(function () {
  async function foo() {
    return bar();
 }

  async function bar() {
    await Promise.resolve();
    throw new Error('BEEP BEEP');
 }

  foo().catch(error => console.log(error.stack));
})()
```

The stack trace no longer shows `foo`, which is pretty bad:

```
> Error: BEEP BEEP
 at bar (REPL26:8:11)
 at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
```

It turns out that improved stack traces were [introduced in V8 engine version 7.3](https://stackoverflow.com/questions/44806135/why-no-return-await-vs-const-x-await/44806230#44806230) (since Node 12) with `--async-stack-traces` option.
The only reason I was semi-automatically removing `await` was WebStorm suggesting that by default and obsolete `eslint` rule.
But these days the recommendation is the opposite.
Always keep `await` and enjoy a better troubleshooting experience of asynchronous code.

## But performance!

There also used to be a tiny performance penalty of including `await`.
It had something to do with one extra microtask on the event loop.
However, this optimization is no longer valid, and probably even [counterproductive](https://v8.dev/blog/fast-async).
