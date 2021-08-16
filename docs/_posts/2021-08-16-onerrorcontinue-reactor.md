---
title: When and how to use onErrorContinue() in Reactor?
tags: Reactor faq onErrorContinue onErrorResume flatMap
layout: post
---

The short answer is: _probably never_.

I got a question recently about the behaviour of `onErrorContinue()` operator in Reactor.
To be honest, I never had to use it in production code.
Being even more honest, I'm not entirely sure how it works.
So I dug deeper into the documentation and some online discussions.
In principle, `onErrorContinue()` operator is suppose to ignore an error and, you know, continue running.
So if you have a stream that produces thousands events and you got an error on the hundredth event, you may continue processing the remaining nine hundred.
That sounds great, especially compared to `onErrorResume()`.
The latter simply stops the stream and _replaces_ it with a different one.
Technically the replacement stream can be the same one that just failed.
This is essentially how `retry()` operator works.
When the stream fails, resubscribe to it.

Sadly, both `onErrorResume()` and `retry()` do not save the state of the failed stream.
This means retrying may produce the same events that we already processed, or miss some events.
It depends on how the initial stream was built.
In short, whether it was _hot_ or _cold_.
From that perspective `onErrorContinue()` sound like a great idea.
Just swallow broken events and move on!
Unfortunately, `onErrorContinue()` operator is quite tricky and may cause subtle bugs.
Check out this great [Reactor onErrorContinue VS onErrorResume](https://devdojo.com/ketonemaniac/reactor-onerrorcontinue-vs-onerrorresume) article for some juicy examples.

Seeing how unobvious this operator is, I stumbled upon GitHub discussion: [onErrorContinue() design](https://github.com/reactor/reactor-core/issues/2184).
A year-long chat between confused developers and the contributors of Reactor library has this [wonderful quote](https://github.com/reactor/reactor-core/issues/2184#issuecomment-641921007) from one of the creators:

> `onErrorContinue` is my billion dollar mistake :(

Now, don't blame [Simon Baslé](https://github.com/simonbasle), designing an API and how it'll evolve is unbelievably hard.
Both Reactor and RxJava had multiple operators removed throughout the history.
But this quote probably explains best how you should approach this operator.
With caution, with care, probably avoiding altogether.
`onErrorContinue()` promises to skip invalid inputs.
Let's take this as an example:

```java
Flux
	.just("one.txt", "two.txt", "three.txt")
	.flatMap(file -> Mono.fromCallable(() -> new FileInputStream(file)))
	.doOnNext(e -> log.info("Got file {}", e))
	.onErrorContinue(FileNotFoundException.class, (ex, o) -> log.warn("Not found? {}", ex.toString()))
	.onErrorContinue(IOException.class, (ex, o) -> log.warn("I/O error {}", ex.toString()));
```

Only the file `two.txt` exists.
The output is somewhat to be expected:

```
WARN - Not found? java.io.FileNotFoundException: one.txt (No such file or directory)
INFO - Got file java.io.FileInputStream@6933b6c6
WARN - Not found? java.io.FileNotFoundException: three.txt (No such file or directory)
```

Sidenote: I intentionally swallow exception's stack traces.
**This is almost never a good idea**, apart from blog posts.

Without `onErrorContinue()` the stream would have failed on the first file.
`onErrorContinue()` swallows the exception and keeps producing more items.
Sounds about right?
Well, what about this slightly modified snippet that doesn't throw `FileNotFoundException` but instead the more generic `IOException`?
Luckily, we have two `onErrorContinue()`s?

```java
Flux
	.just("one.txt", "two.txt", "three.txt")
	.flatMap(file -> Mono.fromCallable(() -> new File("/dev", file).createNewFile()))
	.doOnNext(e -> log.info("Got file {}", e))
	.onErrorContinue(FileNotFoundException.class, (ex, o) -> log.warn("Not found? {}", ex.toString()))
	.onErrorContinue(IOException.class, (ex, o) -> log.warn("I/O error {}", ex.toString()));
```

Creating a file inside `/dev` is not permitted.
So do you expect to see `I/O error` three times?
No.
For reasons I don't fully comprehend the second `onErrorContinue` is ignored and the chain is prematurely terminated:

```
Exception in thread "main" reactor.core.Exceptions$ErrorCallbackNotImplemented: java.io.IOException: Operation not permitted
Caused by: java.io.IOException: Operation not permitted
	at java.base/java.io.UnixFileSystem.createFileExclusively(Native Method)
	at java.base/java.io.File.createNewFile(File.java:1026)
```

If you don't think this is odd, consider almost identical snippet, but without `FileNotFoundException` handling.
It shouldn't matter, after all `createNewFile()` throws generic `IOException`.
But what's the result?

```
WARN - I/O error java.io.IOException: Operation not permitted
WARN - I/O error java.io.IOException: Operation not permitted
WARN - I/O error java.io.IOException: Operation not permitted
```

To be honest, I don't quite understand what's going on.
Why removing seemingly ignored `FileNotFoundException` handling suddenly changes the behaviour of `IOException` handling?
I'd rather use slightly less efficient, but much more readable `onErrorResume()` that is quite predictable.
Notice how I split `doOnError()` for e.g. logging and metrics and `onErrorResume()` for actual handling:

```java
public static void main(String[] args) {
  Flux
      .just("one.txt", "two.txt", "three.txt")
      .flatMap(file -> createFile(file))
      .doOnNext(e -> log.info("Got file {}", e))
      .subscribe();
}

private static Mono<Boolean> createFile(String file) {
  return Mono
      .fromCallable(() -> new File("/dev", file).createNewFile())
      .doOnError(FileNotFoundException.class, ex -> log.warn("Not found? {}", ex.toString()))
      .doOnError(IOException.class, ex -> log.warn("I/O error {}", ex.toString()))
      .onErrorResume(IOException.class, ex -> Mono.empty());
}
```

We get the same pleasant response, without `onErrorContinue()` behaving unexpectedly:

```
WARN I/O error for one.txt: java.io.IOException: Operation not permitted
WARN I/O error for two.txt: java.io.IOException: Operation not permitted
WARN I/O error for three.txt: java.io.IOException: Operation not permitted
```

So, long story short.
`onErrorContinue()` was created to improve performance of error handling.
It is achieved by avoiding wrapping of actions in `Mono.fromCallable()`.
How, its behaviour is sometimes hard to reason about.
Also, not every upstream operator supports resuming after failure.
If you don't quite get the sentence above, I'd stay away from `onErrorContinue()`.
Actually, I recommend avoiding `onErrorContinue()` in general.
You can most likely achieve the same thing with `onErrorResume()` or `onErrorReturn()`.