---
layout: post
title: Streaming large JSON file with Jackson - RxJava FAQ
date: '2017-09-04T08:48:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- backpressure
- Jackson
- JSON
- rxjava
modified_time: '2017-09-04T08:48:46.231+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8528775892007617321
blogger_orig_url: https://www.nurkiewicz.com/2017/09/streaming-large-json-file-with-jackson.html
image:
  path: /assets/img/streaming-large-json-file-with-jackson/hero.jpg
  alt: "Oslo coast"
---

In the previous article, we learned [how to parse excessively large XML files](http://www.nurkiewicz.com/2017/08/loading-files-with-backpressure-rxjava.html) and turn them into RxJava streams.
This time let's look at a large JSON file.
We will base our examples on tiny [colors.json](https://github.com/corysimmons/colors.json/blob/master/colors.json) containing almost 150 records of such format:

```java
{
  "aliceblue": [240, 248, 255, 1],
  "antiquewhite": [250, 235, 215, 1],
  "aqua": [0, 255, 255, 1],
  "aquamarine": [127, 255, 212, 1],
  "azure": [240, 255, 255, 1],
  //...
```

Little known fact: *azure* is also a colour and *python* is a snake.
But back to RxJava.
This file is tiny but we'll use it to learn some principles.
If you follow them you'll be capable of loading and continually processing arbitrarily large, even infinitely long JSON files.
First of all the standard ["*Jackson*" way](https://github.com/FasterXML/jackson) is similar to JAXB: loading the whole file into memory and mapping it to Java beans.
However, if your file is in megabyte or gigabytes (because somehow you found JSON to be the best format for storing gigabytes of data...)
this technique won't work.
Luckily Jackson provides streaming mode similar to StAX.

## Loading JSON files token-by-token using Jackson

There is nothing wrong with a standard `ObjectMapper` that takes JSON and turns it into a collection of objects.
But in order to avoid loading everything into memory, we must use lower-level API used by `ObjectMapper` underneath.
Let's look again at the JSON example:

```java
{
  "aliceblue": [240, 248, 255, 1],
  "antiquewhite": [250, 235, 215, 1],
  //...
```

From the disk and memory perspective this is a single-dimension stream of bytes that we can logically aggregate into JSON tokens:

```java
START_OBJECT        '{'
FIELD_NAME          'aliceblue'
START_ARRAY         '['
VALUE_NUMBER_INT    '240'
VALUE_NUMBER_INT    '248'
VALUE_NUMBER_INT    '255'
VALUE_NUMBER_INT    '1'
END_ARRAY           ']'
FIELD_NAME          'antiquewhite'
START_ARRAY         '['
VALUE_NUMBER_INT    '250'
VALUE_NUMBER_INT    '235'
VALUE_NUMBER_INT    '215'
VALUE_NUMBER_INT    '1'
END_ARRAY           ']'
...
```

You get the idea.
If you are familiar with compiler theory this is one of the first steps during compilation.
The compiler transforms source code from characters to tokens.
But, if you know compiler theory you are probably not parsing JSON for a living.
Anyway!
Jackson library works this way and we can use it without transparent object mapping:

```java
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;

JsonParser parser = new JsonFactory().createParser(new File("colors.json"));
parser.nextToken(); // JsonToken.START_OBJECT;
while (parser.nextToken() != JsonToken.END_OBJECT) {
    final String name = parser.getCurrentName();
    parser.nextToken(); // JsonToken.START_ARRAY;
    parser.nextValue();
    final int red = parser.getIntValue();
    parser.nextValue();
    final int green = parser.getIntValue();
    parser.nextValue();
    final int blue = parser.getIntValue();
    parser.nextValue();
    parser.getIntValue();
    System.out.println(name + ": " + red + ", " + green + ", " + blue);
    parser.nextToken(); // JsonToken.END_ARRAY;
}
parser.close();
```

...or if you get rid of some duplication and make the code a little bit easier to read:

```java
import lombok.Value;


JsonParser parser = new JsonFactory().createParser(new File("colors.json"));
parser.nextToken(); // JsonToken.START_OBJECT;
while (parser.nextToken() != JsonToken.END_OBJECT) {
    System.out.println(readColour(parser));
}
parser.close();

//...

private Colour readColour(JsonParser parser) throws IOException {
    final String name = parser.getCurrentName();
    parser.nextToken(); // JsonToken.START_ARRAY;
    final Colour colour = new Colour(
            name,
            readInt(parser),
            readInt(parser),
            readInt(parser),
            readInt(parser)
    );
    parser.nextToken(); // JsonToken.END_ARRAY;
    return colour;
}

private int readInt(JsonParser parser) throws IOException {
    parser.nextValue();
    return parser.getIntValue();
}

@Value
class Colour {
    private final String name;
    private final int red;
    private final int green;
    private final int blue;
    private final int alpha;
}
```

What does it have to do with RxJava?
You can probably guess - we can read this JSON file on demand, chunk-by-chunk.
This enables backpressure mechanism to work seamlessly:

```java
final Flowable<Colour> colours = Flowable.generate(
        () -> parser(new File("colors.json")),
        this::pullOrComplete,
        JsonParser::close);
```

Let me explain what these three lambda expressions are doing.
The first one sets up `JsonParser` - our mutable state that will be used to produce (*pull*) more items:

```java
private JsonParser parser(File file) throws IOException {
    final JsonParser parser = new JsonFactory().createParser(file);
    parser.nextToken(); // JsonToken.START_OBJECT;
    return parser;
}
```

Nothing fancy.
The second lambda expression is crucial.
It is invoked every time subscriber wishes to receive more items.
If it asks for 100 items, this lambda expression will be invoked 100 times:

```java
private void pullOrComplete(JsonParser parser, Emitter<Colour> emitter) throws IOException {
    if (parser.nextToken() != JsonToken.END_OBJECT) {
        final Colour colour = readColour(parser);
        emitter.onNext(colour);
    } else {
        emitter.onComplete();
    }
}
```

Of course, if we reach `END_OBJECT` (closing whole JSON file) we signal that the stream is over.
The last lambda expression simply allows to clean up the state, for example by closing `JsonParser` and underlying `File`.
Now imagine this JSON file is hundreds of gigabytes in size.
Having `Flowable<Colour>` we can consume it safely in arbitrary speed without risking memory overload.
