---
layout: post
title: Java Coding Conventions considered harmful
date: '2012-10-18T20:03:00.001+02:00'
author: Tomasz Nurkiewicz
tags:
- sun
- oracle
modified_time: '2015-12-08T16:03:59.206+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5444026390381816081
blogger_orig_url: https://www.nurkiewicz.com/2012/10/java-coding-conventions-considered.html
image:
  path: /assets/img/java-coding-conventions-considered/hero.jpg
  alt: "Tjuvholmen seen from a boat"
---

There is an official [Code Conventions for the Java Programming Language](http://www.oracle.com/technetwork/java/codeconvtoc-136057.html) guide published on Oracle site.
You would expect this 20+ pages document to be the most complete, comprehensive and authoritative source of good practices, hints and tips with regards to the Java language.
But once you start to read it, disappointment followed by frustration and anger increases.
I would like to point out the most obvious mistakes, bad practices, poor and outdated advices given in this guide.
In case you are a Java beginner, just forget about this tutorial and look for better and more up-to-date reference materials.
Let the horror begin!

------------------------------------------------------------------------

[*2.2 Common File Names*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-137760.html#253):

> `GNUmakefile` The preferred name for makefiles.
> We use `gnumake` to build our software.

`gnumake` to build Java projects?
[ant](http://ant.apache.org/) is considered old-school, so is [maven](http://maven.apache.org/).
Who uses `make` to build WARs, JARs, generate JavaDocs...?

------------------------------------------------------------------------

[*3.1.1 Beginning Comments*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-141855.html#3441):

> All source files should begin with a c-style comment that lists the class name, version information, date, and copyright notice:

Putting a class name in the comment starting a file?
What if I change my mind and rename the class later?
And what should that "*date*" represent?
Some people use various placeholders to insert last modification time of a file automatically by version control system.
Well, VCS is there to tell you when the file was created or last modified - and modifying the same line over and over again makes merging a huge pain.

------------------------------------------------------------------------

[*4 - Indentation*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-136091.html#262):

> Four spaces should be used as the unit of indentation.
> The exact construction of the indentation (spaces vs. tabs) is unspecified.
> Tabs must be set exactly every 8 spaces (not 4).

Probably the most counterintuitive part of the document.
Some prefer spaces, others (including me) - tabs.
A matter of taste and team arrangements.
But this guide suggests to use both and replace spaces with tabs, sometimes.
It's "*unspecified*".
My advice: use tabs and let each developer configure his IDE to have as big or as small indentations as desired.

------------------------------------------------------------------------

[*4.1 Line Length*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-136091.html#313):

> Avoid lines longer than 80 characters, since they're not handled well by many terminals and tools.

80 characters?
My laptop can easily fit three times as much.
Strive for 120-140 characters in one line, but don't use hard-wraps.
Personally I just display vertical margin and the *right* line length is dictated by readability.
BTW here are few examples of classes from various libraries and frameworks:

- [`SQLIntegrityConstraintViolationException`](http://docs.oracle.com/javase/7/docs/api/java/sql/SQLIntegrityConstraintViolationException.html) (JDK 7, 40 characters)
- [`AbstractInterruptibleBatchPreparedStatementSetter`](http://static.springsource.org/spring/docs/current/javadoc-api/org/springframework/jdbc/core/support/AbstractInterruptibleBatchPreparedStatementSetter.html) (Spring framework, 50 characters)
- [`AbstractDataSourceBasedMultiTenantConnectionProviderImpl`](http://docs.jboss.org/hibernate/orm/4.1/javadocs/org/hibernate/service/jdbc/connections/spi/AbstractDataSourceBasedMultiTenantConnectionProviderImpl.html) (Hibernate, 56 characters)
- [`PreAuthenticatedGrantedAuthoritiesWebAuthenticationDetails`](http://static.springsource.org/spring-security/site/docs/3.1.x/apidocs/org/springframework/security/web/authentication/preauth/PreAuthenticatedGrantedAuthoritiesWebAuthenticationDetails.html) (Spring Security, 58 characters)

And we are suppose to fit whole line in 80 characters?

------------------------------------------------------------------------

[*5.1.2 Single-Line Comments*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-141999.html#341):

```java
if (condition) {

    /* Handle the condition. */
    ...
}
```

Just in case the code is not self-descriptive enough, I suggest even better comment:

```java
if (condition) {

    /* This block is executed if condition == true. */
    ...
}
```

------------------------------------------------------------------------

[*5.1.3 Trailing Comments*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-141999.html#342):

```java
if (a == 2) {
    return TRUE;            /* special case */
} else {
    return isPrime(a);      /* works only for odd a */
}
```

Did you mean (and don't tell me it's less readable, even without comments)?

```java
return a == 2 || isPrime(a);
```

------------------------------------------------------------------------

[*6.1 Number Per Line*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-141270.html#2992):

```java
int level; // indentation level
int size;  // size of table
```

Why use descriptive variable names, when we have *comments*!
Consider this instead:

```java
int indentationLevel;
int tableSize;
```

Later in that section:

> In absolutely no case should variables and functions be declared on the same line.
> Example:
>
> ``` java
> long dbaddr, getDbaddr(); // WRONG!
> ```

Sure it's wrong, it doesn't even compile.
I'm surprised that "*don't put spaces in variable names*" is not mentioned as a good practice...

------------------------------------------------------------------------

[*6.3 Placement*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-141270.html#16817):

> Put declarations only at the beginning of blocks.
> \[...\]
> Don't wait to declare variables until their first use; it can confuse the unwary programmer \[...\]

This is how the coding conventions want you to write your code:

```java
int min;            //inclusive
int max;            //exclusive
int distance;
List<String> list;  //one per each item

min = findMin();
max = findMax();
distance = max - min;
list = new ArrayList<>(distance);
//...
```

And this is how it *should* be written to *avoid* confusion:

```java
final int minInclusive = findMin();
final int maxExclusive = findMax();
final int distance = maxExclusive - minInclusive;
final List<String> listOfItems = new ArrayList<>(distance);
//...
```

Besides we can finally (*nomen est omen*) use `final` keyword.
[Later in this section](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-141270.html#381) code sample is shown with class fields missing `private` modifier (default, package private access).
Package private field?

------------------------------------------------------------------------

[*7.3 return Statements*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-142311.html#438):

```java
return (size ? size : defaultSize);
```

Maybe you haven't noticed, but from the context we can tell that both `size` and `defaultSize` are of `boolean` type.
That's right, `size` and `defaultSize` can be either `true` or `false` (!)
How counterintuitive is that!
From such a document I would expect not only syntactical correctness, but also meaningful code and good practices!
Moreover, the expression can be greatly simplified, *step-by-step*:

```java
size ? size : defaultSize
size ? true : defaultSize
size || defaultSize
```

------------------------------------------------------------------------

[*7.5 for Statements*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-142311.html#454):

> An empty `for` statement (one in which all the work is done in the initialization, condition, and update clauses) should have the following form:
>
> ``` java
> for (initialization; condition; update);
> ```

"*empty `for` statement*"?
Why would you ever use an empty `for` statement?
This is [confusing](http://stackoverflow.com/questions/12772221) and should be avoided, not encouraged and described in the official language guide.
Bonus quiz: what's the purpose of this code in C?

```java
while(*dst++ = *src++);
```

I believe every computer programmer should understand the code snippet above.
Even if you program in Ruby or TSQL.

------------------------------------------------------------------------

[*7.8 switch Statements*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-142311.html#468):

> Every time a `case` falls through (doesn't include a `break` statement), add a comment where the `break` statement would normally be.

I understand the intentions, but the approach is wrong.
Instead of documenting unexpected and error-prone code-fragments, just avoid them.
Don't depend on fall through, don't use it at all.

------------------------------------------------------------------------

[*8.1 Blank Lines*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-141388.html#487):

> One blank line should always be used in the following circumstances:
> \[...\]
>
> - Between the local variables in a method and its first statement
> - Before a block \[...\]
>   or single-line \[...\]
>   comment
> - Between logical sections inside a method to improve readability

Looks like the authors suggest using blank lines to separate "*logical sections of a method*".
Well, I call these sections: "**methods**".
Don't group statements inside methods in blocks, comment them and separate from each other.
Instead extract them into separate, well named methods!
Placing a blank line between variable declarations and the first statement sounds like taken from a C language book.

------------------------------------------------------------------------

[*8.2 Blank Spaces*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-141388.html#682):

> - All binary operators except `.`
>   should be separated from their operands by spaces.
>   Blank spaces should never separate unary operators such as unary minus, increment ("`++`"), and decrement ("`--`") from their operands.
>   Example:
>
> \[...\]
>
> ``` java
> while (d++ = s++) {
>   n++;
> }
> ```

This doesn't even **compile** in Java...

------------------------------------------------------------------------

[*9 - Naming Conventions*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-135099.html#367) (only in [PDF version](http://www.oracle.com/technetwork/java/codeconventions-150003.pdf)):

```java
char *cp;
```

A good name for a `char` pointer in Java is `cp`.
Wait, *WAT*?
`char` **pointer** in Java?

------------------------------------------------------------------------

[*10.1 Providing Access to Instance and Class Variables*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-137265.html#177):

> Don't make any instance or class variable public without good reason.

Really, *really* good reason!
Did I ever used `public` field?

------------------------------------------------------------------------

[*10.4 Variable Assignments*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-137265.html#547):

```java
if (c++ = d++) {        // AVOID! (Java disallows)
    ...
}
```

Great advice: please avoid using constructs that do not even compile in Java.
This makes our lives so much easier!

------------------------------------------------------------------------

[*10.5.2 Returning Values*](http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-137265.html#333):

```java
if (booleanExpression) {
    return true;
} else {
    return false;
}
```

> should instead be written as

```java
return booleanExpression;
```

Holy cow, **I AGREE!**

------------------------------------------------------------------------

##### Summary

It's not that the official *Code Conventions for the Java Programming Language* are completely wrong.
They are just outdated and obsolete.
In the second decade of the XXI century we have better hardware, deeper understanding of code quality and more modern [sources of wisdom](http://www.amazon.com/gp/product/0132350882/ref=as_li_ss_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=0132350882&linkCode=as2&tag=javaandneighb-20).
*Code Conventions...*
were last published in 1999, they are heavily inspired by C language, unaware of billions of lines of code yet to be written by millions of developers.
Code conventions should emerge over time, just like design patterns, rather than be given explicitly.
So please, don't quote or follow advices from official guide ever again.
