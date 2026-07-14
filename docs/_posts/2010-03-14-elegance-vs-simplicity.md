---
layout: post
title: Elegance vs. simplicity
date: '2010-03-14T19:59:00.004+01:00'
author: Tomasz Nurkiewicz
tags:
- esb
- warsaw-jug
- mule
- design patterns
modified_time: '2010-05-16T18:42:16.614+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-7545374834689080778
blogger_orig_url: https://www.nurkiewicz.com/2010/03/elegance-vs-simplicity.html
---

Few weeks ago I had pleasure to give a speech "Mule ESB vs. Apache ServiceMix" at [Warsaw Java Users Group](http://groups.google.com/group/warszawa-jug), together with [Łukasz Dywicki](http://blog.dywicki.pl/).
During this live coding session I have been implementing some simple integration logic using [Mule ESB](http://www.mulesoft.org/display/MULE), while Łukasz did the same with [ServiceMix](http://servicemix.apache.org/).
The presentation went pretty good, you can find source code [here](http://github.com/nurkiewicz/wjug-money).

While preparing for the speech I have discovered some bug (see [MULE-4708](http://www.mulesoft.org/jira/browse/MULE-4708)) in Mule ESB 2.2.1.
My patch has been applied in less than 10 hours after submitting, which is quite impressive.
Sadly, the ESB’s code I had to study to track down the bug was not so impressive, at least that was my first impression.
Just take a look at this excerpt from org.mule.transport.jms.JmsMessageUtils, that takes literally any object and converts it into proper JMS message type:

```java
public static Message toMessage(Object object, Session session) throws JMSException {
      if (object instanceof Message) {
          return (Message) object;
      } else if (object instanceof String) {
          return session.createTextMessage((String) object);
      } else if (object instanceof Map) {
          MapMessage mMsg = session.createMapMessage();
          Map src = (Map) object;
          //...
          return mMsg;
      } else if (object instanceof InputStream) {
          StreamMessage sMsg = session.createStreamMessage();
          InputStream temp = (InputStream) object;
          return sMsg;
      } else if (object instanceof List) {
          StreamMessage sMsg = session.createStreamMessage();
          List list = (List) object;
          //...
          return sMsg;
      } else if (object instanceof byte[]) {
          BytesMessage bMsg = session.createBytesMessage();
          bMsg.writeBytes((byte[]) object);
          return bMsg;
      } else if (object instanceof Serializable) {
          ObjectMessage oMsg = session.createObjectMessage((Serializable) object);
          return oMsg;
      } else if (object instanceof OutputHandler) {
          BytesMessage bMsg = session.createBytesMessage();
          //...
          return bMsg;
      } else {
          throw new JMSException("");
      }
}
```

Something is obviously wrong with this code.
When doing OOP you should never depend on exact type of objects, and certainly not ask them about it.
In OOP each object should be responsible for itself and make decisions – here, client code makes decision externally.
Of course there is no toJmsMessage() method in Object class (similar to toString()), ready to be overridden.
[Visitor pattern](http://nurkiewicz.com/2009/03/wzorzec-visitor-realny-przykad.html) is also not applicable here, so not much can be done.
Least we can do is to make this if-else-if-else monster go away.
Instead my idea is to use a map from class to class-specific transformer.
This map could be modified externally, so other types of JMS messages and supported types can be added without the need to add another conditional branch.

This map would look something like this:

```java
private Map<Class<?>, MessageTransformer> transformers = new LinkedHashMap<Class<?>, MessageTransformer>();

public Message toMessage(Object object, Session session) throws JMSException {
      Validate.notNull(object);
      for (Map.Entry<Class<?>, MessageTransformer> transformerEntry : transformers.entrySet()) {
          if (transformerEntry.getKey().isInstance(object))
              return transformerEntry.getValue().transform(object, session);
      }
      throw new IllegalArgumentException("No transformer found for type: " + object.getClass().getName() + " ('" + object + "')");
}
```

where MessageTransformer is an abstraction for converting one specific type into JMSMessage (by the way do you know why I used [LinkedHashMap](http://java.sun.com/javase/6/docs/api/java/util/LinkedHashMap.html)?)
Here is the example:

```java
interface MessageTransformer {
    Message transform(Object object, Session session) throws JMSException;
}

public class StringMessageTransformer implements MessageTransformer {

      public Message transform(Object object, Session session) throws JMSException {
          return session.createTextMessage((String) object);
      }

}
```

We successfully replaced 8-level-if with a map, that can be easily injected by any IoC container.
Also new implementation of MessageTransformer might be written and added to transformation algorithm without modifying (adding another if-else construct) the original class.
Code is cleaner, more flexible and generic.
No code duplication, easier to maintain, blah, blah, blah – really?

Look at the original code snippet and the one after my refactorings.
Which version is easier to read, in which version would you find the bug earlier?
If you were to made some minor change, which code base is more programmer-friendly?
One huge if or one interface with eight trivial implementations?

The biggest value of the source code is readability.
Not 100% test coverage, because bad code is still hard to maintain when you simply can’t understand the implementation.
I would really prefer having easy to understand code with no unit tests (because I can write them as soon as I understand the code) rather than the Rain Forest Class.
The Rain Forest Class works perfectly and has a full suite of unit tests; as long as you don’t touch it, it looks beautiful.
But as soon as you change the smallest piece of code, the forest collapses, lots of unit tests fail.
Great, but you still don’t know how to fix this, because you don’t understand the code.
The frustration increases.

Writing great code, with absolutely no code duplication, using design patterns and following good practices and principles is a sign of a good programmer.
But not the best one.
The best programmer knows he is better than most of the people who will read his code in the future and use the language suitable for his "readers".
It is like with a database normalization: sometimes [denormalized database](http://www.codinghorror.com/blog/2008/07/maybe-normalizing-isnt-normal.html) if faster and the corresponding schema is (you’ve guessed!)
easier to understand.

I am trying to apply design patterns to become a good programmer.
But to become a great one, sometimes I must forget about them and write the simplest code possible.
Sacrificing code readability is almost never justified.
Strive for simplicity, reduce code duplication and apply patterns only when it is necessary and actually increases readability and maintainability.
Don’t think in terms of flexibility and reusability all the time, don’t make unnecessary levels of abstraction.
Refactoring of a simple code is much cheaper than using already existing Rain Forest Class:

"he’s written a bunch of templates, and all you have to do is multiply-inherit from 17 of his templates, each taking an average of 4 arguments, and you barely even have to write the body of the function"
[Joel Spolsky](http://www.joelonsoftware.com/items/2009/09/23.html)
