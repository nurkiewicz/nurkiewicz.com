---
layout: post
title: Accessing Meetup's streaming API with RxNetty
date: '2014-12-08T23:20:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- Netty
- RxNetty
- Meetup
- JSON
- rxjava
modified_time: '2014-12-09T09:14:05.322+01:00'
thumbnail: /assets/img/accessing-meetups-streaming-api-with/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-7106214796549101172
blogger_orig_url: https://www.nurkiewicz.com/2014/12/accessing-meetups-streaming-api-with.html
---

This article will touch upon multiple subjects: reactive programming, HTTP, parsing JSON and integrating with social API.
All in one use case: we will load and process new [meetup.com](http://www.meetup.com/) events in real time via non-bloking [RxNetty](https://github.com/ReactiveX/RxNetty) library, combining the power of [Netty](http://netty.io/) framework and flexibility of [RxJava](https://github.com/ReactiveX/RxJava) library.
Meetup provides publicly available [streaming API](http://www.meetup.com/meetup_api/docs/stream/2/open_events/) that pushes every single Meetup registered all over the world in real-time.
Just browse to [stream.meetup.com/2/open_events](https://stream.meetup.com/2/open_events) and observe how chunks of JSON are slowly appearing on your screen.
Every time someone creates new event, self-containing JSON is pushed from the server to your browser.
This means such request never ends, instead we keep receiving partial data as long as we want.
We already examined similar scenario in [*Turning Twitter4J into RxJava's Observable*](http://www.nurkiewicz.com/2014/01/turning-twitter4j-into-rxjavas.html).
Each new meetup event publishes a standalone JSON document, similar to this (lots of details omitted):

```json
{ "id" : "219088449",
  "name" : "Silver Wings Brunch",
  "time" : 1421609400000,
  "mtime" : 1417814004321,
  "duration" : 900000,
  "rsvp_limit" : 0,
  "status" : "upcoming",
  "event_url" : "http://www.meetup.com/Laguna-Niguel-Social-Networking-Meetup/events/219088449/",
  "group" : { "name" : "Former Flight Attendants South Orange and North San Diego Co",
              "state" : "CA"
              ...
  },
  "venue" : { "address_1" : "26860 Ortega Highway",
              "city" : "San Juan Capistrano",
              "country" : "US"
              ...
  },
  "venue_visibility" : "public",
  "visibility" : "public",
  "yes_rsvp_count" : 1
  ...
}
```

Every time our long-polling HTTP connection (with `Transfer-Encoding: chunked` response header) pushes such piece of JSON, we want to parse it and somehow pass further.
We hate callbacks, thus RxJava seems like a reasonable alternative (think: `Observable<Event>`).

# Step 1: Receiving raw data with RxNetty

We can't use ordinary HTTP client as they are focused on request-response semantics.
There is no response here, we simply leave opened connection forever and consume data when it comes.
RxJava has an out-of-the-box [RxApacheHttp](https://github.com/ReactiveX/RxApacheHttp) library, but it assumes [`text/event-stream` content type](https://developer.mozilla.org/en-US/docs/Server-sent_events/Using_server-sent_events).
Instead we will use quite low-level, versatile RxNetty library.
It's a wrapper around Netty (duh!)
and is capable of [implementing arbitrary](https://github.com/ReactiveX/RxNetty/tree/0.x/rxnetty-examples) TCP/IP (including HTTP) and UDP clients and servers.
If you don't know Netty, it's packet- rather than stream-oriented, so we can expect one Netty event per each Meetup push.
The API certainly isn't straightforward, but makes sense once you grok it:

```java
HttpClient<ByteBuf, ByteBuf> httpClient = RxNetty.<ByteBuf, ByteBuf>newHttpClientBuilder("stream.meetup.com", 443)
        .pipelineConfigurator(new HttpClientPipelineConfigurator<>())
        .withSslEngineFactory(DefaultFactories.trustAll())
        .build();

final Observable<HttpClientResponse<ByteBuf>> responses = 
    httpClient.submit(HttpClientRequest.createGet("/2/open_events"));
final Observable<ByteBuf> byteBufs = 
    responses.flatMap(AbstractHttpContentHolder::getContent);
final Observable<String> chunks = 
    byteBufs.map(content -> content.toString(StandardCharsets.UTF_8));
```

First we create `HttpClient` and set up SSL (keep in mind that `trustAll()` with regards to server certificates is probably not the best production setting).
Later we `submit()` GET request and receive `Observable<HttpClientResponse<ByteBuf>>` in return.
`ByteBuf` is Netty's abstraction over a bunch of bytes sent or received over the wire.
This observable will tell us immediately about every piece of data received from Meetup.
After extracting `ByteBuf` from response we turn it into a `String` containing aforementioned JSON.
So far so good, it works.

# Step 2: Aligning packets with JSON documents

Netty is very powerful because it doesn't hide inherent complexity over leaky abstractions.
Every time *something* is received over the TCP/IP wire, we are notified.
You might believe that when server sends 100 bytes, Netty on the client side will notify us about these 100 bytes received.
However TCP/IP stack is free to split and merge data you send over wire, especially since it is suppose to be a stream, so how it is split into packets should be irrelevant.
This caveat is greatly explained in [Netty's documentation](http://netty.io/wiki/user-guide-for-4.x.html#wiki-h3-11).
What does it mean to us?
When Meetup sends a single event, we might receive just one `String` in `chunks` observable.
But just as well it can be divided into arbitrary number of packets, thus `chunks` will emit multiple `String`s.
Even worse, if Meetup sends two events right after another, they might fit in one packet.
In that case `chunks` will emit one `String` with two independent JSON documents.
As a matter of fact we can't assume any alignment between JSON strings and networks packets received.
All we know is that individual JSON documents representing events are separated by newlines.
Amazingly, [`RxJavaString`](https://github.com/ReactiveX/RxJavaString) official add-on has a method precisely for that:

```java
Observable<String> jsonChunks = StringObservable.split(chunks, "\n");
```

Actually there is even simpler `StringObservable.byLine(chunks)`, but it uses platform-dependent end-of-line.
What `split()` does is best explained in [official documentation](http://reactivex.io/documentation/string.html):

[![](/assets/img/accessing-meetups-streaming-api-with/1.png)](/assets/img/accessing-meetups-streaming-api-with/1.png)

Now we can safely parse each `String` emitted by `jsonChunks`:

# Step 3: Parsing JSON

Interestingly this step is not so straightforward.
I admit, I *sort-of* enjoyed WSDL times because I could easily and predictably generate Java model that follows web-service's contract.
JSON, especially taking marginal market penetration of [JSON schema](http://json-schema.org/), is basically the Wild West of integration.
Typically you are left with informal documentation or samples of requests and responses.
No type information or format, whether fields are mandatory, etc. Moreover because I reluctantly work with *maps of maps* (hi there, fellow Clojure programmers), in order to work with JSON based REST services I have to write mapping POJOs myself.
Well, there are workarounds.
First I took one representative example of JSON produced by Meetup streaming API and placed it in `src/main/json/meetup/event.json`.
Then I used [`jsonschema2pojo-maven-plugin`](https://github.com/joelittlejohn/jsonschema2pojo) ([Gradle and Ant](http://www.jsonschema2pojo.org/) versions exist as well).
Plugin's name is confusing, it can also work with JSON example, not only schema, to produce Java models:

```xml
<plugin>
    <groupId>org.jsonschema2pojo</groupId>
    <artifactId>jsonschema2pojo-maven-plugin</artifactId>
    <version>0.4.7</version>
    <configuration>
        <sourceDirectory>${basedir}/src/main/json/meetup</sourceDirectory>
        <targetPackage>com.nurkiewicz.meetup.generated</targetPackage>
        <includeHashcodeAndEquals>true</includeHashcodeAndEquals>
        <includeToString>true</includeToString>
        <initializeCollections>true</initializeCollections>
        <sourceType>JSON</sourceType>
        <useCommonsLang3>true</useCommonsLang3>
        <useJodaDates>true</useJodaDates>
        <useLongIntegers>true</useLongIntegers>
        <outputDirectory>target/generated-sources</outputDirectory>
    </configuration>
    <executions>
        <execution>
            <id>generate-sources</id>
            <phase>generate-sources</phase>
            <goals>
                <goal>generate</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

At this point Maven will create `Event.java`, `Venue.java`, `Group.java`, etc. compatible with Jackson:

```java
private Event parseEventJson(String jsonStr) {
    try {
        return objectMapper.readValue(jsonStr, Event.class);
    } catch (IOException e) {
        throw new UncheckedIOException(e);
    }
}
```

It just works, sweet:

```java
final Observable<Event> events = jsonChunks.map(this::parseEventJson);
```

# Step 4: ???<sup>[\[1\]](http://knowyourmeme.com/memes/profit)</sup>

# Step 5: PROFIT!!!

Having `Observable<Event>` we can implement some really interesting use cases.
Want to find names of all meetups in Poland that were just created?
Sure!

```java
events
        .filter(event -> event.getVenue() != null)
        .filter(event -> event.getVenue().getCountry().equals("pl"))
        .map(Event::getName)
        .forEach(System.out::println);
```

Looking for statistics how many events are created per minute?
No problem!

```java
events
        .buffer(1, TimeUnit.MINUTES)
        .map(List::size)
        .forEach(count -> log.info("Count: {}", count));
```

Or maybe you want to continually search for meetups furthest in the future, skipping those closer than ones already found?

```java
events
        .filter(event -> event.getTime() != null)
        .scan(this::laterEventFrom)
        .distinct()
        .map(Event::getTime)
        .map(Instant::ofEpochMilli)
        .forEach(System.out::println);

//...

private Event laterEventFrom(Event first, Event second) {
    return first.getTime() > second.getTime() ?
            first :
            second;
}
```

This code filters out events without known time, emits either current event or the previous one (`scan()`), depending on which one was later, filters out duplicates and displays time.
This tiny program running for few minutes already found one just created meetup scheduled for November 2015 - and it's December 2014 as of this writing.
Possibilities are endless.

I hope I gave you a good grasp of how you can mashup various technologies together easily: reactive programming to write super fast networking code, type-safe JSON parsing without boiler-plate code and RxJava to quickly process streams of events.
Enjoy!
