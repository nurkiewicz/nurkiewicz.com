---
layout: post
title: Turning recursive file system traversal into Stream
date: '2014-07-07T20:09:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- java 8
- functional programming
modified_time: '2014-07-07T20:13:24.415+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8912631488289942250
blogger_orig_url: https://www.nurkiewicz.com/2014/07/turning-recursive-file-system-traversal.html
---

When I was learning programming, back in the days of Turbo Pascal, I managed to list files in directory using [`FindFirst`](http://www.freepascal.org/docs-html/rtl/sysutils/findfirst.html), [`FindNext`](http://www.freepascal.org/docs-html/rtl/sysutils/findnext.html) and [`FindClose`](http://www.freepascal.org/docs-html/rtl/sysutils/findclose.html) functions.
First I came up with a procedure printing contents of a given directory.
You can imagine how proud I was to discover I can actually call that procedure from itself to traverse file system recursively.
Well, I didn't know the term *recursion* back then, but it worked.
Similar code in Java would look something like this:

```java
public void printFilesRecursively(final File folder) {
    for (final File entry : listFilesIn(folder)) {
        if (entry.isDirectory()) {
            printFilesRecursively(entry);
        } else {
            System.out.println(entry.getAbsolutePath());
        }
    }
}

private File[] listFilesIn(File folder) {
    final File[] files = folder.listFiles();
    return files != null ? files : new File[]{};
}
```

Didn't know [`File.listFiles()`](http://docs.oracle.com/javase/8/docs/api/java/io/File.html#listFiles--) can return `null`, did ya?
That's how it signals I/O errors, like if `IOException` never existed.
But that's not the point.
`System.out.println()` is rarely what we need, thus this method is neither reusable nor composable.
It is probably the best counterexample of [Open/Closed principle](http://en.wikipedia.org/wiki/Open/closed_principle).
I can imagine several use cases for recursive traversal of file system:

1.  Getting a complete list of all files for display purposes
2.  Looking for all files matching given pattern/property (also check out [`File.list(FilenameFilter)`](http://docs.oracle.com/javase/8/docs/api/java/io/File.html#list-java.io.FilenameFilter-))
3.  Searching for one particular file
4.  Processing every single file, e.g. sending it over network

Every use case above has a unique set of challenges.
For example we don't want to build a list of all files because it will take a significant amount of time and memory before we can start processing it.
We would like to process files as they are discovered and lazily - by pipe-lining computation (but without clumsy visitor pattern).
Also we want to short-circuit searching to avoid unnecessary I/O.
Luckily in Java 8 some of these issues can be addressed with streams:

```java
final File home = new File(FileUtils.getUserDirectoryPath());
final Stream<Path> files = Files.list(home.toPath());
files.forEach(System.out::println);
```

Remember that [`Files.list(Path)`](http://docs.oracle.com/javase/8/docs/api/java/nio/file/Files.html#list-java.nio.file.Path-) (new in Java 8) does not look into subdirectories - we'll fix that later.
The most important lesson here is: `Files.list()` returns a `Stream<Path>` - a value that we can pass around, compose, map, filter, etc. It's extremely flexible, e.g. it's fairly simple to count how many files I have in a directory per extension:

```java
import org.apache.commons.io.FilenameUtils;

//...

final File home = new File(FileUtils.getUserDirectoryPath());
final Stream<Path> files = Files.list(home.toPath());
final Map<String, List<Path>> byExtension = files
        .filter(path -> !path.toFile().isDirectory())
        .collect(groupingBy(path -> getExt(path)));

byExtension.
        forEach((extension, matchingFiles) ->
                System.out.println(
                        extension + "\t" + matchingFiles.size()));

//...

private String getExt(Path path) {
    return FilenameUtils.getExtension(path.toString()).toLowerCase();
}
```

OK, just another API, you might say.
But it becomes really interesting once *we need to go deeper*, recursively traversing subdirectories.
One amazing feature of streams is that you can combine them with each other in various ways.
Old Scala saying [*"flatMap that shit"*](http://stackoverflow.com/questions/8559537) is applicable here as well, check out this recursive Java 8 code:

```java
//WARNING: doesn't compile, yet:

private static Stream<Path> filesInDir(Path dir) {
    return Files.list(dir)
            .flatMap(path ->
                    path.toFile().isDirectory() ?
                            filesInDir(path) :
                            singletonList(path).stream());
}
```

`Stream<Path>` lazily produced by `filesInDir()` contains all files within directory including subdirectories.
You can use it as any other stream by calling `map()`, `filter()`, `anyMatch()`, `findFirst()`, etc. But how does it really work?
`flatMap()` is similar to `map()` but while `map()` is a straightforward 1:1 transformation, `flatMap()` allows replacing single entry in input `Stream` with multiple entries.
If we had used `map()`, we would have end up with `Stream<Stream<Path>>` (or maybe `Stream<List<Path>>`).
But `flatMap()` flattens this structure, in a way exploding inner entries.
Let's see a simple example.
Imagine `Files.list()` returned two files and one directory.
For files `flatMap()` receives a one-element stream with that file.
We can't simply return that file, we have to wrap it, but essentially this is no-operation.
It gets way more interesting for a directory.
In that case we call `filesInDir()` recursively.
As a result we get a stream of contents of that directory, which we inject into our outer stream.

Code above is short, sweet and...
doesn't compile.
These pesky checked exceptions again.
Here is a fixed code, wrapping checked exceptions for sanity:

```java
public static Stream<Path> filesInDir(Path dir) {
    return listFiles(dir)
            .flatMap(path ->
                    path.toFile().isDirectory() ?
                            filesInDir(path) :
                            singletonList(path).stream());
}

private static Stream<Path> listFiles(Path dir) {
    try {
        return Files.list(dir);
    } catch (IOException e) {
        throw Throwables.propagate(e);
    }
}
```

Unfortunately this quite elegant code is not lazy enough.
`flatMap()` evaluates eagerly, thus it always traverses all subdirectories, even if we barely ask for first file.
You can try with my tiny [`LazySeq`](https://github.com/nurkiewicz/LazySeq) library that tries to provide even lazier abstraction, similar to streams in Scala or `lazy-seq` in Clojure.
But even standard JDK 8 solution might be really helpful and simplify your code significantly.
