---
layout: post
title: Guide to time and date in Java
date: '2016-08-05T10:58:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- java.time
modified_time: '2016-08-05T10:59:36.832+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1680525005904435933
blogger_orig_url: https://www.nurkiewicz.com/2016/08/guide-to-time-and-date-in-java.html
---

Properly handling dates, time, time zones, daylight saving time, leap years and such has been my pet peeve for a long time.
This article is not a comprehensive guide to time domain, see [Date and time in Java](http://www.odi.ch/prog/design/datetime.php) - much more detailed but slightly, *ekhem*, dated.
It's still relevant, but doesn't cover `java.time` from Java 8.
I want to cover the absolute minimum that every junior Java developer should be aware of.

# When did an event happen?

Philosophy and quantum physics aside, we may treat time as a one-dimensional metric, a real number value.
This value keeps growing when time passes by.
If one event appeared after another, we assign greater time to that event.
Two events happening simultaneously have the same time value.
For practical reasons in computer systems we store time in discrete integer, mainly because computer clocks tick discretely.
Therefore we can store time as an integer value.
By convention we assign time = 0 to January 1st, 1970 but in Java we increment this value every millisecond, not second like in [UNIX time](https://en.wikipedia.org/wiki/Unix_time).
Historically using 32-bit signed integer in UNIX time will cause [year 2038 problem](https://en.wikipedia.org/wiki/Year_2038_problem).
Thus Java stores time in 64-bit integer, which is sufficient even if you increment it thousand times more often.
That being said the simplest, yet valid way of storing time in Java is...
`long` primitive:

```java
long timestamp = System.currentTimeMillis();
```

The problem with `long` is that it's so prevalent that using it for storing time undermines the type system.
It may be an ID, may be hash value, can be anything.
Also `long` doesn't have any meaningful methods related to time domain.
The very first approach to wrap `long` in more meaningful object was `java.util.Date` known since Java 1.0:

```java
Date now = new Date();
```

`Date` class however has numerous flaws:

1.  It does not represent...
    date.
    Seriously, officially date is "\[...\]
    the day of the month or year as specified by a number \[...\]"
    [\[1\]](http://www.oxforddictionaries.com/definition/english/date) whereas in Java it represents point in time without any specific calendar (day/month/year).
2.  Its `toString()` is misleading, displaying calendar date and time in system timezone.
    Not only it misled thousands of developers to think that `Date` has a timezone attached.
    Moreover it shows time, but *date* should only represent day, not hour.
3.  It has 20+ deprecated methods, including `getYear()`, `parse(String)` and many constructors.
    These methods are deprecated for a reason, because they lead you to believe `Date` represents, you know, *date*.
4.  `java.sql.Date` extends `java.util.Date` and is actually much more accurate because it indeed represents calendar *date* (`DATE` in SQL).
    However this narrows the functionality of base class `Date`, thus violating [Liskov substitution principle](https://en.wikipedia.org/wiki/Liskov_substitution_principle).
    Don't believe me?
    `java.util.Date.toInstant()` works as expected but `java.sql.Date.toInstant()` fails unconditionally with `UnsupportedOperationException`...
5.  Worst of them all, `Date` is **mutable**.

Ever wondered why old and grumpy developers in your team are so excited about immutability?
Imagine a piece of code that adds one minute to any `Date`.
Simple, huh?

```java
Date addOneMinute(Date in) {
    in.setTime(in.getTime() + 1_000 * 60);
    return in;
}
```

Looks fine, right?
All test cases pass because who on earth would ever validate that input parameters are intact after testing code?

```java
    Date now = new Date();
    System.out.println(now);
    System.out.println(addOneMinute(now));
    System.out.println(now);
```

The output may look as follows:

```text
Tue Jul 26 22:59:22 CEST 2016
Tue Jul 26 23:00:22 CEST 2016
Tue Jul 26 23:00:22 CEST 2016
```

Did you notice that `now` value was actually changed after adding one minute?
When you have a function that takes `Date` and returns `Date` you would never expect it to modify its parameters!
It's like having a function taking `x` and `y` numbers and retuning sum of them.
If you discover that `x` was somehow modified during the course of addition, all your assumptions are ruined.
By the way that is the reason why `java.lang.Integer` is immutable.
Or `String`.
Or `BigDecimal`.

This is not a contrived example.
Imagine a `ScheduledTask` class with a single method:

```java
class ScheduledTask {
    Date getNextRunTime();
}
```

What happens if I say:

```java
ScheduledTask task = //...
task.getNextRunTime().setTime(new Date());
```

Does changing the returned `Date` have effect on next run time?
Or maybe `ScheduledTask` returns a copy of its internal state that you are free to modify?
Maybe we will leave `ScheduledTask` in some inconsistent state?
If `Date` was immutable no such problem would ever arise.

Interestingly, every Java developer will become furious if you confuse Java with JavaScript.
But guess what, [`Date` in JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date) has the exact same flaws as `java.util.Date` and seems like a bad example of copy-paste.
`Date` in JavaScript is mutable, has misleading `toString()` and no support for time zones whatsoever.

A great alternative to `Date` is `java.time.Instant`.
It does precisely what it claims: stores an instant in time.
`Instant` does not have date or calendar related methods, its `toString()` uses familiar ISO format in UTC time zone (more on that later) and most importantly: it's immutable.
If you want to remember when a particular event happened, `Instant` is the best you can get in plain Java:

```java
Instant now = Instant.now();
Instant later = now.plusSeconds(60);
```

Notice that `Instant` does not have `plusMinutes()`, `plusHours()` and so on.
Minutes, hours and days are concepts related to calendar systems, whereas `Instant` is geographically and culturally agnostic.

# Human readable calendars with `ZonedDateTime`

Sometimes you do need a human representation of an instant in time.
This includes month, day of week, current hour and so on.
But here is a major complication: date and time varies across countries and regions.
`Instant` is simple and universal, but not very useful for human beings, it's just a number.
If you have business logic related to calendar, like:

- ...must happen during office hours...
- ...up to one day...
- ...two business days...
- ...valid for up to one year...
- ...

then you must use some calendar system.
`java.time.ZonedDateTime` is the best alternative to absolutely awful `java.util.Calendar`.
As a matter of fact `java.util.Date` and `Calendar` are so broken by design that they are considered to be [deprecated entirely](https://bugs.openjdk.java.net/browse/JDK-8065614) in JDK 9.
You can create `ZonedDateTime` from `Instant` **only** by providing a time zone.
Otherwise default system time zone is used which you have no control over.
Converting `Instant` to `ZonedDateTime` in any way without providing explicit `ZoneId` is probably a bug:

```java
Instant now = Instant.now();
System.out.println(now);

ZonedDateTime dateTime = ZonedDateTime.ofInstant(
        now,
        ZoneId.of("Europe/Warsaw")
    );

System.out.println(dateTime);
```

The output is as follows:

```text
2016-08-05T07:00:44.057Z
2016-08-05T09:00:44.057+02:00[Europe/Warsaw]
```

Notice that `Instant` (for convenience) displays date formatted in UTC whereas `ZonedDateTime` uses supplied `ZoneId` (+2 hours during summer, more on that later).

# Calendar misconceptions

There are many misconceptions and myths related to time and calendars.
For example some people believe that the time difference between two locations is always constant.
There are at least two reasons for that not being true.
First the daylight saving time, aka summer time:

```java
LocalDate localDate = LocalDate.of(2016, Month.AUGUST, 5);
LocalTime localTime = LocalTime.of(10, 21);
LocalDateTime local = LocalDateTime.of(localDate, localTime);
ZonedDateTime warsaw = ZonedDateTime.of(local, ZoneId.of("Europe/Warsaw"));

ZonedDateTime sydney = warsaw.withZoneSameInstant(ZoneId.of("Australia/Sydney"));

System.out.println(warsaw);
System.out.println(sydney);
```

The output reveals that the difference between Warsaw and Sydney is exactly 8 hours:

```text
2016-08-05T10:21+02:00[Europe/Warsaw]
2016-08-05T18:21+10:00[Australia/Sydney]
```

Or is it?
Change August to February and the difference becomes 10 hours:

```text
2016-02-05T10:21+01:00[Europe/Warsaw]
2016-02-05T20:21+11:00[Australia/Sydney]
```

That's because Warsaw does not observe DST in February (it's winter) whereas in Sydney it's summer so they use DST (+1 hour).
In August it's vice-versa.
To make things even more complex, the time to switch to DST varies and it's always during night of local time so there must be a moment where one country already switched but not the other, for example in October:

```text
2016-10-05T10:21+02:00[Europe/Warsaw]
2016-10-05T19:21+11:00[Australia/Sydney]
```

9 hours of difference.
Another reason why time offset differs is political:

```java
LocalDate localDate = LocalDate.of(2014, Month.FEBRUARY, 5);
LocalTime localTime = LocalTime.of(10, 21);
LocalDateTime local = LocalDateTime.of(localDate, localTime);
ZonedDateTime warsaw = ZonedDateTime.of(local, ZoneId.of("Europe/Warsaw"));

ZonedDateTime moscow = warsaw.withZoneSameInstant(ZoneId.of("Europe/Moscow"));

System.out.println(warsaw);
System.out.println(moscow);
```

The time difference between Warsaw and Moscow on February 5th, 2014 was 3 hours:

```text
2014-02-05T10:21+01:00[Europe/Warsaw]
2014-02-05T13:21+04:00[Europe/Moscow]
```

But the difference on the exact same day year later is 2 hours:

```text
2015-02-05T10:21+01:00[Europe/Warsaw]
2015-02-05T12:21+03:00[Europe/Moscow]
```

That's because Russia is changing their DST policy and time zone [like crazy](http://www.timeanddate.com/time/zone/russia/moscow).

Another common misconception about dates is that a day is 24 hours.
This is again related to daylight saving time:

```java
LocalDate localDate = LocalDate.of(2017, Month.MARCH, 26);
LocalTime localTime = LocalTime.of(1, 0);
ZonedDateTime warsaw = ZonedDateTime.of(localDate, localTime, ZoneId.of("Europe/Warsaw"));

ZonedDateTime oneDayLater = warsaw.plusDays(1);

Duration duration = Duration.between(warsaw, oneDayLater);
System.out.println(duration);
```

What do you know, the difference between 1 AM on March 26th and 27th, 2017 is...
23 hours (`PT23H`).
But if you change the time zone to `Australia/Sydney` you'll get familiar 24 hours because nothing special happens that day in Sydney.
That special day in Sydney happens to be 2nd of April, 2017:

```java
LocalDate localDate = LocalDate.of(2017, Month.APRIL, 2);
LocalTime localTime = LocalTime.of(1, 0);
ZonedDateTime warsaw = ZonedDateTime.of(localDate, localTime, ZoneId.of("Australia/Sydney"));
```

Which results in one day being equal to...
25 hours.
But not in Brisbane (`"Australia/Brisbane"`), thousand km north to Sydney, which does not observe DST.
Why is all of this important?
When you make an agreement with your client that something is suppose to take one day vs. 24 hours this may actually make a huge difference at certain day.
You must be precise, otherwise your system will become inconsistent twice a year.
And don't get me started on [leap second](https://en.wikipedia.org/wiki/Leap_second).

The lesson to learn here is that every time you enter calendar domain you **must** think about time zones.
There are convenience methods that use default system time zone but in cloud environments you may not have control over that.
The same applies to default character encoding, but that's a different story.

# Storing and transmitting time

By default you should store and send time either as timestamp (`long` value) or as [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) which is basically what `Instant.toString()` does as per the documentation.
Prefer `long` value as it is more compact, unless you need more readable format in some text encoding like JSON.
Also `long` is timezone-agnostic so you are not pretending that the timezone you send/store has any meaning.
This applies both to transmitting time and storing it in database.

There are cases where you may want to send full calendar information, including timezone.
For example when you build a chatting application you might want to tell the client what was the local time when the message was sent if your friend lives in a different timezone.
Otherwise you know it was sent at 10 AM your time, but what was the time in your friend's location?
Another example is flight ticket booking website.
You want to tell your clients when flight departs and arrives in local time and it's only the server that knows the exact timezone at departure and destination.

# Local time and date

Sometimes you want express date or time without any specific time zone.
For example my birthday is:

```java
//1985-12-25
LocalDate.of(1985, Month.DECEMBER, 25)
```

I will celebrate my birthday that day no matter where I am.
This means party will start at approximately:

```java
//20:00
LocalTime.of(20, 0, 0)      
```

Irrespective to time zone.
I can even say that my birthday party this year will be precisely at:

```java
//2016-12-25T20:00
LocalDateTime party = LocalDateTime.of(
        LocalDate.of(2016, Month.DECEMBER, 25),
        LocalTime.of(20, 0, 0)
);
```

But as long as I don't provide you a location, you don't know what is the time zone I live in, thus what is the actual start time.
It's impossible (or very foolish) to convert from `LocalDateTime` to `Instant` or `ZonedDateTime` (which both point to a precise moment in time) without giving a time zone.
So local times are useful, but they don't really represent any moment in time.

# Testing

I just scratched the surface of pitfalls and issues one might have with time an date.
For example we didn't cover leap years which can become a serious source of bugs.
I find [property-based testing](http://www.nurkiewicz.com/2014/09/property-based-testing-with-scalacheck.html) extremely useful when testing dates:

```java
import spock.lang.Specification
import spock.lang.Unroll

import java.time.*

class PlusMinusMonthSpec extends Specification {

    static final LocalDate START_DATE =
            LocalDate.of(2016, Month.JANUARY, 1)

    @Unroll
    def '#date +/- 1 month gives back the same date'() {
        expect:
            date == date.plusMonths(1).minusMonths(1)
        where:
            date << (0..365).collect {
                day -> START_DATE.plusDays(day)
            }
    }

}
```

This test makes sure adding and subtracting one month to any date in 2016 gives back the same date.
Pretty straightforward, right?
This test fails for a number of days:

```text
date == date.plusMonths(1).minusMonths(1)
|    |  |    |             |
|    |  |    2016-02-29    2016-01-29
|    |  2016-01-30
|    false
2016-01-30


date == date.plusMonths(1).minusMonths(1)
|    |  |    |             |
|    |  |    2016-02-29    2016-01-29
|    |  2016-01-31
|    false
2016-01-31


date == date.plusMonths(1).minusMonths(1)
|    |  |    |             |
|    |  |    2016-04-30    2016-03-30
|    |  2016-03-31
|    false
2016-03-31

...
```

Leap years cause all sorts of issues and break the laws of math.
Another similar example is adding two months to a date that is not always equal to adding one month two times.

# Summary

Once again we barely scratched the surface.
If there is just one thing I want you to learn from this article: mind the time zone!
