---
layout: post
title: Loading files with backpressure - RxJava FAQ
date: '2017-08-31T21:38:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- StAX
- backpressure
- rxjava
modified_time: '2017-08-31T21:38:32.476+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5339580397662156286
blogger_orig_url: https://www.nurkiewicz.com/2017/08/loading-files-with-backpressure-rxjava.html
image:
  path: /assets/img/loading-files-with-backpressure-rxjava/hero.jpg
  alt: "Oslofjord"
---

Processing file as a stream turns out to be tremendously effective and convenient.
Many people seem to forget that since Java 8 (3+ years!)
we can very easily turn any file into a stream of lines:

```java
String filePath = "foobar.txt";
try (BufferedReader reader = new BufferedReader(new FileReader(filePath))) {
    reader.lines()
            .filter(line -> !line.startsWith("#"))
            .map(String::toLowerCase)
            .flatMap(line -> Stream.of(line.split(" ")))
            .forEach(System.out::println);
}
```

`reader.lines()` returns a `Stream<String>` which you can further transform.
In this example, we discard lines starting with `"#"` and *explode* each line by splitting it into words.
This way we achieve stream of words as opposed to stream of lines.
Working with text files is almost as simple as working with normal Java collections.
In RxJava [we already learned](http://www.nurkiewicz.com/2017/08/generating-backpressure-aware-streams.html) about `generate()` operator.
It can be used here as well to create robust stream of lines from a file:

```java
Flowable<String> file = Flowable.generate(
        () -> new BufferedReader(new FileReader(filePath)),
        (reader, emitter) -> {
            final String line = reader.readLine();
            if (line != null) {
                emitter.onNext(line);
            } else {
                emitter.onComplete();
            }
        },
        reader -> reader.close()
);
```

`generate()` operator in aforementioned example is a little bit more complex.
The first argument is a state factory.
Every time someone subscribes to this stream, a factory is invoked and stateful `BufferedReader` is created.
Then when downstream operators or subscribers wish to receive some data, second lambda (with two parameters) is invoked.
This lambda expression tries to *pull* exactly one line from a file and either send it downstream (`onNext()`) or complete when end of file is encountered.
It's fairly straightforward.
The third optional argument to `generate()` is a lambda expression that can do some cleanup with state.
It's very convenient in our case as we have to close the file not only when end of file is reached but also when consumers prematurely unsubscribe.

## Meet `Flowable.using()` operator

This seems like a lot of work, especially when we already have a stream of lines from JDK 8.
Turns out there is a similar factory operator named `using()` that is quite handy.
First of all the simplest way of translating `Stream` from Java to `Flowable` is by converting `Stream` to an `Iterator` (checked exception handling ignored):

```java
Flowable.fromIterable(new Iterable<String>() {
    @Override
    public Iterator<String> iterator() {
        final BufferedReader reader = new BufferedReader(new FileReader(filePath));
        final Stream<String> lines = reader.lines();
        return lines.iterator();
    }
});
```

This can be simplified to:

```java
Flowable.<String>fromIterable(() -> {
    final BufferedReader reader = new BufferedReader(new FileReader(filePath));
    final Stream<String> lines = reader.lines();
    return lines.iterator();
});
```

But we forgot about closing `BufferedReader` thus `FileReader` thus file handle.
Thus we introduced resource leak.
Under such circumstances `using()` operator works like a charm.
In a way it's similar to `try-with-resources` statement.
You can create a stream based on some external resource.
The lifecycle of this resource (creation and disposal) will be managed for you when someone subscribes or unsubscribes:

```java
Flowable.using(
        () -> new BufferedReader(new FileReader(filePath)),
        reader -> Flowable.fromIterable(() -> reader.lines().iterator()),
        reader -> reader.close()
);
```

It's fairly similar to last `generate()` example, however the most important lambda expression in the middle is quite different.
We get a resource (`reader`) as an argument and are suppose to return a `Flowable` (not a single element).
This lambda is called only once, not every time downstream requests new item.
What `using()` operator gives us is managing `BufferedReaders`'s lifecycle.
`using()` is useful when we have a piece of state (just like with `generate()`) that is capable of producing whole `Flowable` at once, as opposed to one item at a time.

## Streaming XML files

...or JSON for that matter.
Imagine you have a very large XML file that consists of the following entries, hundreds of thousands of them:

```java
<trkpt lat="52.23453" lon="21.01685">
    <ele>116</ele>
</trkpt>
<trkpt lat="52.23405" lon="21.01711">
    <ele>116</ele>
</trkpt>
<trkpt lat="52.23397" lon="21.0166">
    <ele>116</ele>
</trkpt>
```

This is a snippet from standard [GPS Exchange Format](https://en.wikipedia.org/wiki/GPS_Exchange_Format) that can describe geographical routes of arbitrary length.
Each `<trkpt>` is a single point with latitude, longitude and elevation.
We would like to have a stream of track points (ignoring elevation for simplicity) so that the file can be consumed partially, as opposed to loading everything at once.
We have three choices:

- DOM/JAXB - everything must be loaded into memory and mapped to Java objects.
  Won't work for infinitely long files (or even very large ones)
- SAX - a push-based library that invokes callbacks whenever it discovers XML tag opening or closing.
  Seems a bit better but can't possibly support backpressure - it's the library that decides when to invoke callbacks and there is no way of slowing it down
- StAX - like SAX, but we must actively pull for data from XML file.
  This is essential to support backpressure - we decide when to read next chunk of data

Let's try to implement parsing and streaming of possibly very large XML file using StAX and RxJava.
First we must learn [how to use StAX](http://www.nurkiewicz.com/2014/07/testing-code-for-excessively-large.html) in the first place.
The parser is called `XMLStreamReader` and is created with the following sequence of spells and curses:

```java
XMLStreamReader staxReader(String name) throws XMLStreamException {
    final InputStream inputStream = new BufferedInputStream(new FileInputStream(name));
    return XMLInputFactory.newInstance().createXMLStreamReader(inputStream);
}
```

Just close your eyes and make sure you always have a place to copy-paste the snippet above from.
It gets even worse.
In order to read the first `<trkpt>` tag including its attributes we must write quite some complex code:

```java
import lombok.Value;

@Value
class Trackpoint {
    private final BigDecimal lat;
    private final BigDecimal lon;
}

Trackpoint nextTrackpoint(XMLStreamReader r) {
    while (r.hasNext()) {
        int event = r.next();
        switch (event) {
            case XMLStreamConstants.START_ELEMENT:
                if (r.getLocalName().equals("trkpt")) {
                    return parseTrackpoint(r);
                }
                break;
            case XMLStreamConstants.END_ELEMENT:
                if (r.getLocalName().equals("gpx")) {
                    return null;
                }
                break;
        }
    }
    return null;
}

Trackpoint parseTrackpoint(XMLStreamReader r) {
    return new Trackpoint(
            new BigDecimal(r.getAttributeValue("", "lat")),
            new BigDecimal(r.getAttributeValue("", "lon"))
    );
}
```

The API is quote low-level and almost adorably antique.
Everything happens in a gigantic loop that reads...
*something* of type `int`.
This `int` can be `START_ELEMENT`, `END_ELEMENT` or few other things which we are not interested in.
Remember we are reading XML file, but not line-by-line or char-by-char but by logical XML tokens (tags).
So, if we discover opening of `<trkpt>` element we parse it, otherwise we continue.
The second important condition is when we find closing `</gpx>` which should be the last thing in GPX file.
We return `null` in such case, signaling end-of-XML-file.

Feels complex?
This is actually the simplest way to read large XML with constant memory usage, irrespective to file size.
How does all of this relate to RxJava?
At this point we can very easily build a `Flowable<Trackpoint>`.
Yes, `Flowable`, not `Observable` (see: [`Obsevable` vs. `Observable`](http://www.nurkiewicz.com/2017/08/1x-to-2x-migration-observable-vs.html)).
Such a stream will have full support for backpressure, meaning it will read file at appropriate speed:

```java
Flowable<Trackpoint> trackpoints = generate(
        () -> staxReader("track.gpx"),
        this::pushNextTrackpoint,
        XMLStreamReader::close);

void pushNextTrackpoint(XMLStreamReader reader, Emitter<Trackpoint> emitter) {
    final Trackpoint trkpt = nextTrackpoint(reader);
    if (trkpt != null) {
        emitter.onNext(trkpt);
    } else {
        emitter.onComplete();
    }
}
```

Wow, so simple, such backpressure!<sup>[\[1\]](http://knowyourmeme.com/memes/doge)</sup> We first create an `XMLStreamReader` and make sure it's being closed when file ends or someone unsubscribes.
Remember that each subscriber will open and start parsing the same file over and over again.
The lambda expression in the middle simply takes the state variables (`XMLStreamReader`) and emits one more trackpoint.
All of this seems quite obscure and it is!
But we now have a backpresure-aware stream taken from a possibly very large file using very little resources.
We can process trackpoint concurrently or combine them with other sources of data.
In the next article we will learn how to load JSON in very similar way.
