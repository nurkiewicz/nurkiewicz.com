---
title: "#64: TypeScript: will it entirely replace JavaScript?"
category: podcast
redirect_from:
  - /64
tags: typescript javascript dart elm node.js deno transpiling
description: >
    TypeScript is a programming language, a superset of JavaScript.
    This means any valid JavaScript program is also valid TypeScript.
    But not vice-versa!
    TypeScript adds a ton of features, addressing the shortcomings of JavaScript.
    The most important one is optional static typing, including `null`-safety.
    The fact that you can take any JavaScript code and turn it into TypeScript by simply changing a file extension is crucial.
    It means you can gradually start using TypeScript's features without rewriting your whole application.
---

{% include player.html spotify_id="5bcelZXuwnmklCXCjp3KPj" youtube_id="sdfH-DTedpg" %}

{{ page.description }}

OK, but what's the big deal with static typing?
Well, did you ever come across the dreadful `Undefined is not a function` error?
In JavaScript, everything is an object of an unknown shape.
This is sometimes useful.
But knowing in advance that a given variable is a React component rather than a, I don't know, a string proved to be really valuable.
Having type annotations makes reading and maintaining code so much easier.
The extra hassle of creating types and occasionally fighting with the compiler really pays off.

Static vs. dynamic typing is actually a decades-old debate.
No matter which side you are on, the popularity of TypeScript is astounding.
As a matter of fact, all new frontend projects I know use TypeScript these days.

TypeScript also has great interoperability with the JavaScript ecosystem.
Of course, you can use JavaScript packages.
But also, most popular packages have TypeScript type definitions available.
Essentially, even though the package is written in JavaScript, it exposes statically-typed public API.
It makes using new packages much easier.
The IDE gives you hints and guides you through.

The type system offered by TypeScript is actually quite advanced.
It supports:

* union types
* inheritance
* interfaces
* generics
* null-safety
* structural typing

...and much more.

Null-safety is especially worth mentioning.
Basically, TypeScript compiler (`tsc` for short) tracks possible `null` and `undefined` variables.
Where JavaScript fails at runtime `tsc` fails at build tiem with a type error.
Programs that don't compile can't fail on production.

OK, but there's one problem.
Web browsers and node.js do not understand TypeScript.
They speak JavaScript.
Luckily, TypeScript is not a dead language.
When you want to run it, the compiler translates it into... JavaScript.
First, all type information is stripped.
JavaScript has no types, so it's unnecessary.
Other high-level language features are translated to JavaScript automatically.
This process is technically called _transpilation_.

Actually, there's a node.js competitor called Deno.
It supports TypeScript out-of-the-box.
However, the translation to JavaScript simply happens behind the scenes.
Theoretically, a native TypeScript runtime could improve performance, but we are yet to see such an engine.

TypeScript was originally created by Microsoft.
By the way, Microsoft also gave us Visual Studio Code and AJAX.
AJAX being the father of `fetch` API
Also GitHub, after being acquired, improved significantly.
And Microsoft was once the top Linux kernel contributor.
So I think Internet Explorer and Windows Millenium Edition should be forgiven.

Finally, to be honest, there are plenty of languages transpiling back to JavaScript.
The most popular ones are Dart, CoffeeScript and Elm.
But it seems TypeScript won.

That's it, thanks for listening, bye!

# More materials

* [Official website](https://www.typescriptlang.org/)
* `Null`: [billion-dollar mistake](https://en.wikipedia.org/wiki/Null_pointer#History)
* [TypeScript](https://en.wikipedia.org/wiki/TypeScript) on Wikipedia
* [Deno running TypeScript](https://deno.land/manual@v1.17.1/typescript/overview#how-does-it-work)
* [`strictNullChecks`](https://www.typescriptlang.org/tsconfig#strictNullChecks)
* [Top Five Linux Contributor: Microsoft](https://www.zdnet.com/article/top-five-linux-contributor-microsoft/)
* [A Comparison of Different Javascript Transpilers](http://www.discoversdk.com/blog/a-comparison-of-different-javascript-transpilers)
* [Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
* [_undefined is not a function_](https://stackoverflow.com/search?q=%22undefined+is+not+a+function%22) on StackOverflow
* Selected languages transpiling to JavaScript:
    * [CoffeeScript](https://coffeescript.org/)
    * [Dart](https://dart.dev/)
    * [Elm](https://elm-lang.org/)
* [#14: Static, Dynamic, Strong and Weak Type Systems](https://nurkiewicz.com/14)
* [#45: Node.js: running JavaScript on the server (!)](https://nurkiewicz.com/45)
