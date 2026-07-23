---
layout: post
image: /assets/img/mongodb-and-recording-appenders-for/class-diagram.svg
title: MongoDB and recording appenders for Logback
date: '2011-04-08T19:50:00.003+02:00'
author: Tomasz Nurkiewicz
tags:
- mongodb
- logging
- logback
- nosql
modified_time: '2011-11-17T19:19:28.907+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8544619098801066319
blogger_orig_url: https://www.nurkiewicz.com/2011/04/mongodb-and-recording-appenders-for.html
---

Today I am giving you two new [appenders](http://logback.qos.ch/manual/appenders.html) for [Logback](http://logback.qos.ch/): one for [MongoDB](http://www.mongodb.org/) and one which I called *recording appender*.
Just as a reminder, appenders (both in Log4J and Logback) are an abstraction of your application logs destination.
The most common are [file](http://logback.qos.ch/manual/appenders.html#FileAppender) and [console](http://logback.qos.ch/manual/appenders.html#ConsoleAppender) appenders, followed by several others built-in.
MongoDB appender is pretty straightforward, so I will start by describing the recording appender.

#### Recording appender

As you already [know](http://nurkiewicz.com/2010/05/clean-code-clean-logs-logging-levels.html), one of the biggest benefits of using logging frameworks are logging levels.
By carefully choosing levels for each logging statement we can easily filter which logs should be present in our log files and which shouldn't.
Also we can apply different logging strategies for different environments.
This is in theory.
In practice we often face the choice between: log everything just in case and handle gigabytes of meaningless log files ***or*** log only warnings and errors but when they actually occur, they are meaningless as well, lacking important debugging context.
The idea isn't new (see [\[1\]](http://stackoverflow.com/questions/690431/how-to-configure-log4j-to-dump-debug-info-when-an-error-occurs), [\[2\]](http://www.mail-archive.com/logback-user@qos.ch/msg00606.html) and [\[3\]](http://www.mail-archive.com/logback-user@qos.ch/msg02027.html) for example), but somehow decent implementation is missing in both Log4J and Logback.
And the idea is simple – as long as there is nothing wrong happening with the system: do not log anything or log very little – but silently memorize all debug logs in some cyclic buffer.
And whenever disaster occurs (any log with ERROR level, probably an exception), dump the buffer first to provide meaningful context.

Writing custom logging appenders is pretty straightforward.
Following is the essence of my recording appender:

```java

public class RecordingAppender extends UnsynchronizedAppenderBase<ILoggingEvent> {

  private ThreadLocal<CyclicBuffer<ILoggingEvent>> recordedEvents = new ThreadLocal<CyclicBuffer<ILoggingEvent>>() {
    @Override
    protected CyclicBuffer<ILoggingEvent> initialValue() {
      return new CyclicBuffer<ILoggingEvent>(maxEvents);
    }
  };

  @Override
  protected void append(ILoggingEvent eventObject) {
    if (triggersDump(eventObject)) {
      dumpRecordedEvents();
      dump(eventObject);
    } else
      recordedEvents.get().add(eventObject);
  }

  //...

}
```

I hope the code is self-explanatory, if not – I failed as a developer, not you as a reader.
The only detail worth explaining is the usage of ThreadLocal.
Logging history is stored ThreadLocal, so only logs from current thread will be dumped in case of error.
This seems reasonable in most cases (and eliminates the need for synchronization).
Why the appender is parametrized with generic ILoggingEvent type will be described later.
The full source code of this appender is, as always, available on my Logback [fork](https://github.com/nurkiewicz/logback/blob/recording-appender/logback-classic/src/main/java/ch/qos/logback/classic/RecordingAppender.java) at GitHub ([recording-appender](https://github.com/nurkiewicz/logback/tree/recording-appender) branch).

Using this appender is really simple – just declare ch.qos.logback.classic.RecordingAppender and define one or more delegating appenders to be used when dump is required.
As a side note: which GoF pattern is it?

With the configuration below every log statement with level WARN or higher will trigger dump.
The configuration also states that up to 1000 records will be kept in memory, unless some of them are older than 15 seconds.
When warning or error is encountered, it will be printed on the console, preceded by more detailed logs.
It really works (in addition of having [100%](https://github.com/nurkiewicz/logback/blob/recording-appender/logback-classic/src/test/java/ch/qos/logback/classic/RecordingAppenderTest.java) code coverage).

```xml

<?xml version="1.0" encoding="UTF-8" ?>
<configuration>
  <appender name="REC" class="ch.qos.logback.classic.RecordingAppender">
    <appender-ref ref="STDOUT"/>

    <maxEvents>1000</maxEvents>
    <dumpThreshold>WARN</dumpThreshold>
    <expiryTimeMs>15000</expiryTimeMs>
  </appender>

  <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
    <encoder>
      <pattern>%-4relative [%thread] %-5level - %msg%n</pattern>
    </encoder>
  </appender>

  <root level="DEBUG">
    <appender-ref ref="REC"/>
  </root>
</configuration>
```

#### MongoDB appender

MongoDB, being document oriented database focused on performance and scalability seems like a great storage for application and server logs – much better than [DbAppender](http://logback.qos.ch/manual/appenders.html#DBAppender) using traditional relational database.
Why?
Quickly count how many tables and rows you need to store normalized logging event containing stack trace with several frames and MDC map?
And what if you just want to store some properties, leaving others as optional?
Sacrificing absolute durability and ACID constraints, in MongoDB you just store document – with nested properties, skipping optional parameters – and extremely fast.
Also, once again, the idea isn't [new](http://www.slideshare.net/WombatNation/logging-app-behavior-to-mongo-db).

But again, why would you like to store application or web server HTTP access logs (be patient!)
in database altogether?
Well, with a little help of [sharding](http://www.mongodb.org/display/DOCS/Sharding) and [MapReduce](http://www.mongodb.org/display/DOCS/MapReduce), searching, aggregating and transforming *a lot* of data is a pleasure.

The implementation is trivial (excerpt from [MongoDBAppenderBase.java](https://github.com/nurkiewicz/logback/blob/mongodb-appender/logback-core/src/main/java/ch/qos/logback/core/db/mongo/MongoDBAppenderBase.java), see [mongo-appender](https://github.com/nurkiewicz/logback/tree/mongodb-appender) branch):

[](http://draft.blogger.com/post-create.g?blogID=6753769565491687768)

```java

public abstract class MongoDBAppenderBase<E> extends UnsynchronizedAppenderBase<E> {

  //...

  @Override
  public void start() {
    try {
      connectToMongoDB();
      super.start();
    } catch (UnknownHostException e) {
      addError("Error connecting to MongoDB server: " + host + ":" + port, e);
    }
  }

  private void connectToMongoDB() throws UnknownHostException {
    mongo = new Mongo(new ServerAddress(host, port), buildOptions());
    DB db = mongo.getDB(dbName);
    if (username != null && password != null)
      db.authenticate(username, password.toCharArray());
    eventsCollection = db.getCollection(collectionName);
  }

  protected abstract BasicDBObject toMongoDocument(E event);

  @Override
  protected void append(E eventObject) {
    eventsCollection.insert(toMongoDocument(eventObject));
  }

  //...

}
```

[](http://draft.blogger.com/post-create.g?blogID=6753769565491687768) Appender doesn't have to be synchronized (it only uses native MongoDB [Java driver](http://www.mongodb.org/display/DOCS/Java+Language+Center), which is thread safe and even handles connection pooling) and all it does is connecting to MongoDB server/cluster and insert logging events as documents in the database.
Abstract toMongoDocument() method and E generic type?
- looks suspicious...
Logback has a pretty clever architecture.
In logback-core you place general logging logic, like connecting and storing documents in MongoDB in our case.
Then one can simply subclass the base appender to define logic specific to a given logging object type.

![MongoDB appender class hierarchy](/assets/img/mongodb-and-recording-appenders-for/class-diagram.svg)

So what object types does Logback support?
The traditional (classic) logging is what we are familiar with.
logback-access on the other hand allows us to log web container [access logs](http://httpd.apache.org/docs/2.2/logs.html#accesslog) using Logback infrastructure.
And because MongoDB has no schema and creates collections (table-like structures) the first time they are used, we can essentially store anything.
Following is the toMongoDocument() implementation excerpt for classic logs (note the generic type):

```java

public class MongoDBAppender extends MongoDBAppenderBase<ILoggingEvent> {

  public MongoDBAppender() {
    super("loggingEvents");
  }

  @Override
  protected BasicDBObject toMongoDocument(ILoggingEvent event) {
    final BasicDBObject doc = new BasicDBObject();
    doc.append("timeStamp", new Date(event.getTimeStamp()));
    doc.append("level", event.getLevel().levelStr);
    doc.append("thread", event.getThreadName());
    if (event.getMdc() != null && !event.getMdc().isEmpty())
      doc.append("mdc", event.getMdc());
    //...
    return doc;
    }
}
```

...and here is what you can expect to find your MongoDB database:

```javascript

{
    "_id" : ObjectId("4d9cbcbf7abb3abdaf9679cd"),
    "timeStamp" : ISODate("2011-04-06T19:19:27.006Z"),
    "level" : "ERROR",
    "thread" : "main",
    "logger" : "ch.qos.logback.classic.db.mongo.MongoDBAppenderTest",
    "message" : "D" 
}
```

Very similar implementation for access logs follows.
Once again look carefully – both appenders are extending MongoDBAppenderBase with different generic type, only implementing *log-to-document* logic, whereas common database connection logic is handled once in base class.
Pretty elegant design (it's Logback design, not mine, I am just following it), seems like OOP is not dead after all:

```java

public class MongoDBAppender extends MongoDBAppenderBase<IAccessEvent> {

  public MongoDBAppender() {
    super("accessEvents");
  }

  @Override
  protected BasicDBObject toMongoDocument(IAccessEvent event) {
    final BasicDBObject doc = new BasicDBObject();
    doc.append("timeStamp", new Date(event.getTimeStamp()));
    if(server)
      doc.append("server", event.getServerName());
    //...
    return doc;
  }
}
```

You can compare [classic](https://github.com/nurkiewicz/logback/blob/mongodb-appender/logback-classic/src/main/java/ch/qos/logback/classic/db/mongo/MongoDBAppender.java) and [access](https://github.com/nurkiewicz/logback/blob/mongodb-appender/logback-access/src/main/java/ch/qos/logback/access/db/mongo/MongoDBAppender.java) implementations to see how similar they are, although they cope with really different data.
Here is what you might find in accessEvents collections in MongoDB:

```javascript

{
    "_id" : ObjectId("4d98cc4f7abb95e59279e183"),
    "timeStamp" : ISODate("2011-04-03T19:36:47.339Z"),
    "server" : "localhost",
    "remote" : {
        "host" : "0:0:0:0:0:0:0:1",
        "user" : "tomcat",
        "addr" : "0:0:0:0:0:0:0:1" 
    },
    "request" : {
        "uri" : "/manager/images/tomcat.gif",
        "protocol" : "HTTP/1.1",
        "method" : "GET",
        "sessionId" : "1C6357816D9EEFD31F6D9D154D87308A",
        "userAgent" : "Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.2.16) Gecko/20110323 Ubuntu/10.10 (maverick) Firefox/3.6.16",
        "referer" : "http://localhost:8080/manager/html" 
    },
    "response" : {
        "contentLength" : NumberLong(1934),
        "statusCode" : 200 
    } 
}
```

You might ask yourself a question: why would I store access logs in crazy, JSON-like documents stored in database driven by C++?
The answer is: scalability.
MongoDB speed and sharding capabilities make it a great choice for storing lots of free-form data.
Now, using built-in MapReduce framework you might search, aggregate, or maybe even look for suspicious usage patterns across thousands of servers in parallel.
Be warned thou that timeStamp, although looks promising, isn't very good candidate for sharding key.
Assuming all your web servers have similar system clock, at a given point in time all of them will be writing to the same shard.
After a moment or two, they will all switch to a different one.
At the same time, all other shards are dying of boredom.
But timeStamp+serverName looks nice (order of keys in compound key is really important, just like with indexes in RDBMS).

Another tip is using [capped collections](http://www.mongodb.org/display/DOCS/Capped+Collections) in MongoDB.
There is no obvious natural key for logging events (both classic and access), so we need to use generated keys, which aren't useful as they don't form any particular order.
But if you use capped collections, order of records in the database is guaranteed to be the same as insertion order.
Also, capped collections are limited in size and automatically remove the oldest entries, which seems like a great fit for logging use case.

MongoDBAppender has many other features, including:

- Fully configurable MongoDB connection
- For access logger you can define which access parameters (like response status code, URI, session id, etc.)
  should be persisted
- For classic logger: should caller data be persisted

See for yourself how many optional parameters are [provided](https://github.com/nurkiewicz/logback/blob/mongodb-appender/logback-classic/src/test/input/joran/mongodb/all_params.xml).
If you like the idea of recording appender (*your application very own [flight data recorder](http://en.wikipedia.org/wiki/Flight_data_recorder)*), please take a look and vote for [LBCLASSIC-260](http://jira.qos.ch/browse/LBCLASSIC-260).
I also filed an issue for MongoDB appender, [LBCLASSIC-261](http://jira.qos.ch/browse/LBCLASSIC-261).
Oh, if I'm into advertising myself already, maybe [this](http://jira.qos.ch/browse/LBCLASSIC-217) will catch your attention as well.
Have a great time playing with my appenders (you can even combine them) and I'm waiting for your comments.
