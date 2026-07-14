---
layout: post
title: Logging exceptions root cause first
date: '2011-09-23T22:43:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- stack traces
- logging
- logback
modified_time: '2012-10-06T12:25:24.059+02:00'
thumbnail: /assets/img/logging-exceptions-root-cause-first/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5094207683393029370
blogger_orig_url: https://www.nurkiewicz.com/2011/09/logging-exceptions-root-cause-first.html
---

The [0.9.30](http://logback.qos.ch/news.html) release of [Logback](http://logback.qos.ch/) logging library brings new awesome feature: logging stack traces starting from root (innermost) exception rather than from the outermost one.
Of course my excitement has nothing to do with the fact that [I contributed](http://logback.qos.ch/apidocs/ch/qos/logback/classic/pattern/RootCauseFirstThrowableProxyConverter.html) this feature...

To paraphrase Cecil B.
de Mille: “*The way to make a blog post is to begin with a stack trace and work up to a climax*” - here it goes:

[![](/assets/img/logging-exceptions-root-cause-first/1.png)](/assets/img/logging-exceptions-root-cause-first/1.png)

The details aren't important yet, but from 100ft view you can see long stack trace with several exceptions wrapping each other (*causing*).
We'll go back to this stack trace, but first some basics.
If you throw an exception it will be logged in a way showing how the stack was looking in the moment when the exception was from.
At the very bottom you will either see static main() or Thread.run() proceeded by methods invoked up to the first stack trace line indicating the place where the actual exception was thrown.
This is very convenient since you can see the whole control flow that resulted in the exception:

```java

public class BookController {

  private final BookService bookService = new BookService();

  public void alpha() { beta(); }

  private void beta() { gamma(); }

  private void gamma() { bookService.delta(); }

  public static void main(String[] args) {
    new BookController().alpha();
  }
}

class BookService {

  private final BookDao bookDao = new BookDao();

  public void delta() { epsilon(); }

  private void epsilon() { zeta(); }

  private void zeta() { bookDao.eta(); }
}

class BookDao {

  public void eta() { theta(); }

  private void theta() { iota(); }

  public void iota() { throw new RuntimeException("Omega server not available"); }
}
```

If you don't know the [Greek alphabet](http://en.wikipedia.org/wiki/Greek_alphabet), you can start learning from the stack trace (remember, the control flow starts at the bottom and works its way up):

```text

java.lang.RuntimeException: Omega server not available
  at BookDao.iota(BookController.java:50)
  at BookDao.theta(BookController.java:48)
  at BookDao.eta(BookController.java:46)
  at BookService.zeta(BookController.java:41)
  at BookService.epsilon(BookController.java:39)
  at BookService.delta(BookController.java:37)
  at BookController.gamma(BookController.java:22)
  at BookController.beta(BookController.java:20)
  at BookController.alpha(BookController.java:18)
  at BookController.main(BookController.java:26)
```

Wonderful, right?
When reading from top to bottom you can say: *iota() was called by theta() was called by eta()*...
Clear and simple.
However what if somebody decides to wrap the original exception and re-throw it?

```java

public class BookController {

  private static final Logger log = LoggerFactory.getLogger(BookController.class);

  private final BookService bookService = new BookService();

  public void alpha() { beta(); }

  private void beta() { gamma(); }

  private void gamma() {
    try {
      bookService.delta();
    } catch (Exception e) {
      throw new RuntimeException("Sorry, try again later", e);
    }
  }

  public static void main(String[] args) {
    try {
      new BookController().alpha();
    } catch (Exception e) {
      log.error("", e);
    }
  }
}

class BookService {

  private final BookDao bookDao = new BookDao();

  public void delta() { epsilon(); }

  private void epsilon() { zeta(); }

  private void zeta() {
    try {
      bookDao.eta();
    } catch (Exception e) {
      throw new RuntimeException("Unable to save order", e);
    }
  }
}

class BookDao {

  public void eta() { theta(); }

  private void theta() { iota(); }

  public void iota() {
    try {
      throw new RuntimeException("Omega server not available");
    } catch (Exception e) {
      throw new RuntimeException("Database problem", e);
    }
  }
}
```

Now quickly: find the root cause in the stack trace!

```text

java.lang.RuntimeException: Sorry, try again later
  at BookController.gamma(BookController.java:26)
  at BookController.beta(BookController.java:20)
  at BookController.alpha(BookController.java:18)
  at BookController.main(BookController.java:32)
Caused by: java.lang.RuntimeException: Unable to save order
  at BookService.zeta(BookController.java:51)
  at BookService.epsilon(BookController.java:45)
  at BookService.delta(BookController.java:43)
  at BookController.gamma(BookController.java:24)
  ... 8 common frames omitted
Caused by: java.lang.RuntimeException: Database problem
  at BookDao.iota(BookController.java:66)
  at BookDao.theta(BookController.java:60)
  at BookDao.eta(BookController.java:58)
  at BookService.zeta(BookController.java:49)
  ... 11 common frames omitted
Caused by: java.lang.RuntimeException: Omega server not available
  at BookDao.iota(BookController.java:64)
  ... 14 common frames omitted
```

Turns out that main() is no longer the last line.
Even worse, everything seems garbled, try to read the Greek alphabet again...
Now let's go back to our original stack trace.
It comes from Spring framework startup failure, imagine it can be several pages long.

[![](/assets/img/logging-exceptions-root-cause-first/2.png)](/assets/img/logging-exceptions-root-cause-first/2.png)

For you convenience I added arrows to mark you the path you should follow to reconstruct the control flow: starting from the red arrow's tail (Thread.run()) somewhere in the middle you go up and then...
jump to the tail of orange arrow.
From the head of the orange arrow you jump to the tail of the green one and so on...
Not very intuitive, don't you think?
And what is this red ellipse showing?
Yes, it is the root cause of the failure (the innermost exception).
On the other hand the exception printed at the very beginning (the one you typically read on the first place) says something about an *error creating DefaultAnnotationHandlerMapping#0* (*what?*) The true error (*No matching bean of type...*) is cleverly hidden...

So what is this [new feature](http://logback.qos.ch/manual/layouts.html#rootException) all about?
Again our simple example.
After upgrading to 0.9.30 just add **[%rEx](http://logback.qos.ch/manual/layouts.html#rootException)**(or equivalent **%rootException**) at the end of your logging pattern:

`<appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">`
`  <encoder>`
`    <pattern>%d %level %m%n`**`%rEx`**`</pattern>`
`  </encoder>`
`</appender>`

This will replace the default stack trace printing routing with the one I humbly contributed.
The same Greek program will now print:

```text

java.lang.RuntimeException: Omega server not available
  at BookDao.iota(BookController.java:64)
Wrapped by: java.lang.RuntimeException: Database problem
  at BookDao.iota(BookController.java:66)
  at BookDao.theta(BookController.java:60)
  at BookDao.eta(BookController.java:58)
  at BookService.zeta(BookController.java:49)
Wrapped by: java.lang.RuntimeException: Unable to save order
  at BookService.zeta(BookController.java:51)
  at BookService.epsilon(BookController.java:45)
  at BookService.delta(BookController.java:43)
  at BookController.gamma(BookController.java:24)
Wrapped by: java.lang.RuntimeException: Sorry, try again later
  at BookController.gamma(BookController.java:26)
  at BookController.beta(BookController.java:20)
  at BookController.alpha(BookController.java:18)
  at BookController.main(BookController.java:32)
```

Please compare it carefully with the previous output.
First of all, the very first line points to the problem.
No digging in the “Caused by” exceptions, most of the time you will probably skip the rest.
Secondly, the control flow is uninterrupted and continuous – you can still read it from top to bottom or vice-versa.
And last but not least – the fact that exceptions were wrapped in the meantime is preserved but does not garble the stack trace.

Now you deserve to see the original Spring exception taking advantage of %rEx printing:

[![](/assets/img/logging-exceptions-root-cause-first/3.png)](/assets/img/logging-exceptions-root-cause-first/3.png)

The observations are exactly the same: root cause of the problem appears at the very beginning, shortening the time the problem needs to be investigated.
Also when analysing the control flow there is not jumping – Thread.main() is at the bottom and you can read the trace from bottom to top continuously.

If you “work” a lot with stack traces (either in development or in production/support) – consider switching to root cause first logging.
It will save you few seconds every time you analyse particular exception.
But I also noticed inexperienced developers sometimes aren't even aware of “*Caused by*” rule: *find first exception and look at the last Caused by* – remaining clueless what the problem is, looking only at the outermost, least specific, most generic error.
This will help them as well.

By the way – all this hustle can be avoided if you avoid wrapping and re-throwing exception altogether.
I know, all too often we are forced to do so by checked exceptions...
