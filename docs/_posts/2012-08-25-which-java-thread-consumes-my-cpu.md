---
layout: post
title: Which Java thread consumes my CPU?
date: '2012-08-25T12:28:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- jvm
- performance
- bash
modified_time: '2012-08-26T11:26:50.979+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-7125053624951455923
blogger_orig_url: https://www.nurkiewicz.com/2012/08/which-java-thread-consumes-my-cpu.html
---

What do you do when your Java application consumes 100% of the CPU?
Turns out you can easily find the problematic thread(s) using built-in UNIX and JDK tools.
No profilers or agents required.
For the purpose of testing we'll use this simple program:

```java
public class Main {
    public static void main(String[] args) {
        new Thread(new Idle(), "Idle").start();
        new Thread(new Busy(), "Busy").start();
    }
}

class Idle implements Runnable {

    @Override
    public void run() {
        try {
            TimeUnit.HOURS.sleep(1);
        } catch (InterruptedException e) {
        }
    }
}

class Busy implements Runnable {
    @Override
    public void run() {
        while(true) {
            "Foo".matches("F.*");
        }
    }
}
```

As you can see, it starts two threads.
`Idle` is not consuming any CPU (remember, sleeping threads consume memory, but not CPU) while `Busy` eats the whole core as regular expression parsing and executing is a surprisingly complex process.
Let's run this program and forget about it.
How can we quickly find out that `Busy` is the problematic piece of our software?
First of all we use [top](http://www.linuxmanpages.com/man1/top.1.php) to find out the process id (`PID`) of the `java` process consuming most of the CPU.
This is quite straightforward:

```bash
$ top -n1 | grep -m1 java
```

This will display the first line of `top` output containing "`java`" sentence:

```bash
22614 tomek     20   0 1360m 734m  31m S    6 24.3   7:36.59 java
```

The first column is the PID, let's extract it.
Unfortunately it turned out that `top` uses [ANSI escape codes for colors](http://en.wikipedia.org/wiki/ANSI_escape_code#Colors) - invisible characters that are breaking tools like `grep` and `cut`.
Luckily I found a [perl script to remove these characters](http://unix.stackexchange.com/questions/4527) and was finally able to extract the PID of `java` process exhausting my CPU:

```bash
$ top -n1 | grep -m1 java | perl -pe 's/\e\[?.*?[\@-~] ?//g' | cut -f1 -d' '
```

The `cut -f1 -d' '` invocation simply takes the first value out of space-separated columns:

```bash
22614
```

Now when we now the problematic JVM PID, we can use `top -H` to find problematic Linux threads.
The `-H` option prints a list of all *threads* as opposed to *processes*, the PID column now represents the internal Linux thread ID:

```bash
$ top -n1 -H | grep -m1 java
$ top -n1 -H | grep -m1 java | perl -pe 's/\e\[?.*?[\@-~] ?//g' | cut -f1 -d' '
```

The output is surprisingly similar, but the first value is now the thread ID:

```bash
25938 tomek     20   0 1360m 748m  31m S    2 24.8   0:15.15 java
25938
```

So we have a process ID of our busy JVM and Linux thread ID (most likely from that process) consuming our CPU.
Here comes the best part: if you look at [jstack](http://docs.oracle.com/javase/1.5.0/docs/tooldocs/share/jstack.html) output (available in JDK), each thread has some mysterious ID printed next to its name:

```bash
"Busy" prio=10 tid=0x7f3bf800 nid=0x6552 runnable [0x7f25c000]
    java.lang.Thread.State: RUNNABLE
        at java.util.regex.Pattern$Node.study(Pattern.java:3010)
```

That's right, the `nid=0x645a` parameter is the same as thread ID printed by `top -H`.
Of course to not make it too simple, `top` uses decimal notation while `jstack` prints in hex.
Again there is a simple solution, [printf "%x"](http://ss64.com/bash/printf.html):

```bash
$ printf "%x" 25938
6552
```

Let's wrap all we have now into a script and combine the results:

```bash
#!/bin/bash
PID=$(top -n1 | grep -m1 java | perl -pe 's/\e\[?.*?[\@-~] ?//g' | cut -f1 -d' ')
NID=$(printf "%x" $(top -n1 -H | grep -m1 java | perl -pe 's/\e\[?.*?[\@-~] ?//g' | cut -f1 -d' '))
jstack $PID | grep -A500 $NID | grep -m1 "^$" -B 500
```

`PID` holds the `java` PID and `NID` holds the thread ID, most likely from that JVM.
The last line simply dumps the JVM stack trace of the given PID and filters out (using `grep`) the thread which has matching `nid`.
Guess what, it works:

```bash
$ ./profile.sh
"Busy" prio=10 tid=0x7f3bf800 nid=0x6552 runnable [0x7f25c000]
    java.lang.Thread.State: RUNNABLE
        at java.util.regex.Pattern$Node.study(Pattern.java:3010)
        at java.util.regex.Pattern$Curly.study(Pattern.java:3854)
        at java.util.regex.Pattern$CharProperty.study(Pattern.java:3355)
        at java.util.regex.Pattern$Start.<init>(Pattern.java:3044)
        at java.util.regex.Pattern.compile(Pattern.java:1480)
        at java.util.regex.Pattern.<init>(Pattern.java:1133)
        at java.util.regex.Pattern.compile(Pattern.java:823)
        at java.util.regex.Pattern.matches(Pattern.java:928)
        at java.lang.String.matches(String.java:2090)
        at com.blogspot.nurkiewicz.Busy.run(Main.java:27)
        at java.lang.Thread.run(Thread.java:662)
```

Running the script multiple times (or with `watch`, see below) will capture `Busy` thread in different places, but almost always inside regular expression parsing - which is our problematic piece!

#### Multiple threads

In case your application has multiple CPU-hungry threads, you can use [`watch -n1`](http://ss64.com/bash/watch.html)` ./profile.sh` command to run the script every second and get semi real-time stack dumps, most likely from different threads.
Testing with the following program:

```java
new Thread(new Idle(), "Idle").start();
new Thread(new Busy(), "Busy-1").start();
new Thread(new Busy(), "Busy-2").start();
```

you'll see stack traces either of `Busy-1` or of `Busy-2` threads (in different places inside `Pattern` class), but never `Idle`.
