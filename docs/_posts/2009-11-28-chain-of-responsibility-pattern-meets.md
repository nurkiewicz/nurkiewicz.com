---
layout: post
title: Chain of responsibility pattern meets Spring, JPA, Wicket and Apache CXF part
  1/2
date: '2009-11-28T19:24:00.009+01:00'
author: Tomasz Nurkiewicz
tags:
- jpa
- web services
- design patterns
- spring
modified_time: '2009-12-01T21:16:00.361+01:00'
thumbnail: /assets/img/chain-of-responsibility-pattern-meets/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-864940446407161601
blogger_orig_url: https://www.nurkiewicz.com/2009/11/chain-of-responsibility-pattern-meets.html
---

Chain of responsibility behavioral design pattern is a wonderful solution for complex logic of processing a requests.
In this pattern single request (message, database record, external system call, etc.)
is being passed to the first handler in the chain.
This handler can:

- process request and return result
- process request partially and run subsequent handler
- ignore the request and pass the control further as above
- run next handler and, after it returns, process already handled request
- simply return, without processing and passing control down the chain
- throw an exception

Of course, if the first handler decides to pass control down the chain to the second one, the second handler has the same set of options.
The most important feature of handlers is that each handler is only aware of itself – it does not know its position in chain (whether it is first, last or somewhere in the middle) and particularly not know what is the next handler down the chain.
Because each handler is available only through the same abstract interface, this design promotes louse coupling (handlers are independent of each other) and high cohesion (every handler has one, well known responsibility).

So, what is this chain after all?
Actually, it is just a ordered list of handlers.
The biggest advantage of the pattern is that this list can be easily modified.
You may change the order, remove or add handlers in no time, altering the system behavior.
Although some combinations of handlers in chain will be incorrect (as we will see later), ability to change the chain without changing lots of code makes the system very flexible.

The last important thing to mention are the scenarios in which this pattern can work.
In the first variation, each handler has only two options: either handler the request and return result or ignore request and pass control down the chain.
In the second variation (which I have chosen for the example) chain works more like a [filter](http://java.sun.com/blueprints/patterns/InterceptingFilter.html), where each handler alters the request and/or has some side effects, but no handler (except the special last one) fully takes care of the message.

Enough of theory, this is our artificial example: we are designing a web service for registering car.
There are at least two business steps in this process: storing a car data passed to WS (this is our request, also called the message) in the database and registering the in Car Department using their remote EJB.
There is also lots of technical steps: logging, validation, exception handling, transactions, profiling, timeouts, retrying, etc. Good design would promote louse coupling, so all this steps should be decoupled (AOP, anybody?).
Also, some steps are optional and the order of others is not obvious.
Besides, some other business routines are planned to be added in the future, so web service implementation must be very flexible.

Let us start from the handler abstraction:

```java
public interface RegistrationChainHandler {
   long handle(Car car, RegistrationChain chain) throws Exception;
}
```

Seems very straightforward: handler takes the argument of the message type (Car POJO in this case) and returns the chain result value (some id).
But what is this RegistrationChain?
In classic chain of responsibility pattern each handler simply has a reference to the next handler in chain.
I found this approach less flexible to the one I present.
So, what this object after all?
In short, RegistrationChain is a simple wrapper around handlers list, remembering the position (next handler to be executed; see [Iterator](http://en.wikipedia.org/wiki/Iterator_pattern) pattern).
By invoking its proceed() method we simply ask it to run next handler in chain.
Here is a part of not-so-obvious implementation:

```java
public class RegistrationChain {
   private final ListIterator<RegistrationChainHandler> currentHandlerIter;

   public long proceed(Car car) throws Exception {
       if (!currentHandlerIter.hasNext())
           return handleEndOfChain();
       RegistrationChainHandler handler = currentHandlerIter.next();
       try {
           return handler.handle(car, this);
       } finally {
           currentHandlerIter.previous();
       }
   }

   protected long handleEndOfChain() {
       throw new IllegalStateException("No handler fulfilled the request");
   }

}
```

The proceed() method first tries to obtain next handler from the chain.
If no such exists, handleEndOfChain() method is called.
Of course, I could simply throw an exception directly from proceed(), but doing so from protected method allows user to alter the end of chain behavior by subclassing the RegistrationChain.
This is a good practice following [Open/closed principle](http://en.wikipedia.org/wiki/Open/closed_principle).

If the handler is found, its handle() method is being called and the return value returned further.
This is not complicated if you think for a while: handler A calls proceed() method inside its handle() method.
The proceed() method finds handler B succeeding A and runs its handle() method passing itself as a second argument.
The cycle repeats.

Only the finally clause might not be obvious at first.
Think about aforementioned chain A -\> B -\> C.
If handler A calls proceed(), B.handle() is being called and chain iterator forwards.
If B.handle() calls proceed(), chain will call C.handle(), as this is the next handler in chain.
If the chain iterator only forwards, why move it back when returning?
Let’s move a bit further.
When A.handle() call to proceed() finishes, what would be the position of chain iterator?
Without going back after each proceed(), it would point to some undetermined place in the chain (probably past the end).
Now think what would happen if A.handle(), for some reason, calls proceed() once again?
You would expect to re-run the chain starting from B, but the next handler iterator points "somewhere"...
Think about it, as this is the cause for moving the iterator back.

We have the infrastructure, it is time for real implementation.
First, two main business processes: storing car in database using JPA and accessing remote EJB:

```java
public class StoreCarHandler implements RegistrationChainHandler {
   @PersistenceContext
   private EntityManager em;

   @Override
   @Transactional(propagation = Propagation.MANDATORY)
   public long handle(Car car, RegistrationChain chain) throws Exception {
       em.persist(car);
       return chain.proceed(car);
   }
}
```

As you can see, MANDATORY transaction propagation level has been used to ensure the method runs within a transaction and fails if not.
Transaction management will be held by different handler.

```java
public class RegisterInCarDeptHandler implements RegistrationChainHandler {

   @Resource
   private CarRegisterRemote carRegisterRemote;

   @Override
   public long handle(Car car, RegistrationChain chain) throws Exception {
       String carDeptId = carRegisterRemote.register(car.getRegistrationNo(), car.getEngineCapacity().doubleValue());
       car.setCarDeptId(carDeptId);
       return chain.proceed(car);
   }
}
```

This handler uses remote EJB proxy injected by Spring and runs its business method.
Value returned from this method is then assigned to the car being processed.
There are also several other handlers having different, well specified responsibilities:

```java
public class ValidationHandler implements RegistrationChainHandler {

   @Override
   public long handle(Car car, RegistrationChain chain) throws Exception {
       Validate.notNull(car, "Car can't be null");
       Validate.notEmpty(car.getRegistrationNo(), "Registration number can't be empty");
       Validate.notNull(car.getColor(), "Color can't be null");
       Validate.notNull(car.getEngineCapacity(), "Engine capacity can't be null");
       Validate.notNull(car.getWeight(), "Weight can't be null");
       return chain.proceed(car);
   }
}
```

This handler simply validates input argument.
You might consider this as assertion.
Logging handler simply logs input argument:

```java
public class LoggingHandler implements RegistrationChainHandler {

   private static final Logger log = LoggerFactory.getLogger(LoggingHandler.class);

   @Override
   public long handle(Car car, RegistrationChain chain) throws Exception {
       log.debug("Processing car: {}", car);
       return chain.proceed(car);
   }
}
```

This handler uses [Perf4j](http://perf4j.codehaus.org/) to monitor the time of remaining part of chain execution.
Perf4j is a wonderful tool for measuring your application performance and gathering statistics.
I will try to write something more about it in the future.
By using different tag attribute values you might create several copies of this handler and monitor different parts of the chain:

```java
public class Perf4jHandler implements RegistrationChainHandler {

   private String tag;

   @PostConstruct
   public void init() {
       if(StringUtils.isBlank(tag))
       tag = Perf4jHandler.class.getName();
   }

   @Override
   public long handle(Car car, RegistrationChain chain) throws Exception {
       StopWatch watch = new Slf4JStopWatch(tag);
       try {
           return chain.proceed(car);
       } finally {
           watch.stop();
       }
   }

   public void setTag(String tag) {
       this.tag = tag;
   }
}
```

Exception translation is a common pattern used to hide the details of your system and provide less verbose messages to the client.
Surely, you don’t want to expose parts of your SQL or JMS queues names, etc., which often occur in exception messages.

```java
public class ExceptionTranslatorHandler implements RegistrationChainHandler {

   @Override
   public long handle(Car car, RegistrationChain chain) throws Exception {
       try {
           return chain.proceed(car);
       } catch (CarRegistrationException e) {
           throw e;
       } catch (Exception e) {
           throw new CarRegistrationException("Error while registering car", e);
       }
   }
}
```

Two handlers that left are particularly important.
The first one handles transactions, which was already mentioned:

```java
public class TransactionalHandler implements RegistrationChainHandler {

   @Override
   @Transactional
   public long handle(Car car, RegistrationChain chain) throws Exception {
       return chain.proceed(car);
   }
}
```

That’s it!
[@Transactional](http://nurkiewicz.com/2009/08/spring-aop-riddle.html) annotation around handle() handles transaction transparently, so all the handlers down the chain are run within this transaction.
The reason to have a separate handler for that instead of putting the transaction directly over StoreCarHandler is to have a better control over transaction boundaries (the handler can be put anywhere in the chain).
Also, it makes the example more interesting :-).

If you look closely to the implementations of all handlers and RegistrationChain, you will notice that the chain never ends...
Every handler passed the control further and does not take responsibility of handling the car completely.
Although I found it more flexible (no handler is obligated to be the last, because it will never pass control), we need a way to successfully stop processing.
This can be done on RegistrationChain level (by overriding handleEndOfChain(), see above), but I chose to have a special catch-all handler:

```java
public class CatchAllHandler implements RegistrationChainHandler {
   private boolean fail;
   private String failMessage;

   @Override
   public long handle(Car car, RegistrationChain chain) throws Exception {
       if(fail)
           throw new IllegalStateException(failMessage);
       return car.getId();
   }

   public void setFail(boolean fail) {
       this.fail = fail;
   }
}
```

This handler can also be used to stop processing with exception, depending on configuration.
The last, but most sophisticated handler has been added when our client requested us to provide some time SLA for the web service method.
Although HTTP timeouts could have been used, we decided to implement our own mechanism, so it can be reused in the future.
This handler instead of running proceed() method immediately, creates a [Callable\<Long\>](http://java.sun.com/javase/6/docs/api/java/util/concurrent/Callable.html) instance wrapping it ([Adapter](http://nurkiewicz.com/2009/09/adapter-pattern-accesing-ehcache-via.html) pattern!)
and submitting to the thread pool.
Then, using [Future\<Long\>](http://java.sun.com/javase/6/docs/api/java/util/concurrent/Future.html) we wait configured time for the result.
If the task reaches the available thread in pool and is fully executed (it means, all handlers below are run), everything works transparently for the client.
But if the invocation has not finished and the timeout is reached, client will get only error message.

```java
public class HandlerWithTimeout implements RegistrationChainHandler {

   @Resource
   private ExecutorService executorService;
   private long timeoutInMillis = 5000;

   @Override
   public long handle(final Car car, final RegistrationChain chain) throws Exception {
       Future<Long> registrationResult = executorService.submit(new Callable<Long>() {
           @Override
           public Long call() throws Exception {
              return chain.proceed(car);
           }});

       try {
           return registrationResult.get(timeoutInMillis, TimeUnit.MILLISECONDS);
       } catch (ExecutionException e) {
           if(e.getCause() instanceof Exception)
              throw ((Exception) e.getCause());
           else
              throw new CarRegistrationException(e.getCause());
       } catch (TimeoutException e) {
           registrationResult.cancel(true);
           throw new CarRegistrationException("Registration did not finished after " + timeoutInMillis + "ms");
       }
   }
}
```

That was a lot of code!
Let us get everything together and test it.
First we define web service interface and implementation:

```java
@WebService
public interface CarRegistrationWs {
   long registerCar(Car car);
}
```

```java
public class CarRegistrationWsImpl implements CarRegistrationWs {
   @Override
   public long registerCar(Car car) {
       return car.register();
   }
}
```

Not much, everything interesting happens in Car entity.
Actually, in real implementation I used [DTO](http://en.wikipedia.org/wiki/Data_transfer_object) structural design pattern for WS argument, which is slightly different than the JPA Car POJO, but this is not important.
Since Car is a JPA entity, I use [@Configurable](http://nurkiewicz.com/2009/10/ddd-in-spring-made-easy-with-aspectj.html) annotation to inject the chain.
The traditional way would be to have CarService.register(Car) service layer object, but isn’t running Car.register() more fun?

```java
@Configurable
public class Car implements Serializable {

   private List<RegistrationChainHandler> handlers;

   public void setHandlers(List<RegistrationChainHandler> handlers) {
       this.handlers = handlers;
   }

   public long register() {
       try {
           return new RegistrationChain(handlers).proceed(this);
       } catch (CarRegistrationException e) {
           throw e;
       } catch (RuntimeException e) {
           throw e;
       } catch (Exception e) {
           throw new RuntimeException(e);
       }

   }
   /*  */
}
```

The final touch is a piece of code in, well, Spring XML:

```xml
<bean id="carRegistrationWs" class="com.blogspot.nurkiewicz.cars.registration.ws.CarRegistrationWsImpl"/>
<jaxws:endpoint id="helloWorld" implementor="#carRegistrationWs" address="/Registration"/>

<bean id="car" class="com.blogspot.nurkiewicz.cars.Car" scope="prototype" lazy-init="true">
   <property name="handlers" ref="handlersList"/>
</bean>
 
<util:list id="handlersList">
   <ref bean="exceptionTranslatorHandler"/>
   <ref bean="validationHandler"/>
   <ref bean="handlerWithTimeout"/>
   <ref bean="perf4jHandler"/>
   <ref bean="loggingHandler"/>
   <ref bean="transactionalHandler"/>
   <ref bean="storeCarHandler"/>
   <ref bean="registerInCarDeptHandler"/>
   <ref bean="catchAllHandler"/>
</util:list>
```

First bean is the web service implementation.
Second one creates a web service endpoint and publishes it under given name.
As you can see Apache CXF is very easy to set up.
CXF-Spring integration is briefly covered [here](http://cwiki.apache.org/CXF20DOC/writing-a-service-with-spring.html), also remember to [configure CXF to use Log4j](http://www.techper.net/2008/01/30/configuring-cxf-logging-to-go-through-log4j).

As you probably guessed, the handlersList is our chain configuration.
Each handler shown before is actually a Spring bean, which is very helpful: for example I can easily inject remote EJB proxy or ExecutorService for asynchronous invocation.
Managing the whole business process is just a matter of manipulating this list.

Finally!
– I run the application using mvn jetty:run and immediately browse to <http://localhost:8080/cars/ws/Registration?WSDL>.
Seems everything is OK, so I run [SoapUI](http://www.soapui.org/) for some functional testing.
Pasting the WSDL above and filling the example request XML is enough to see the chain in action:

[![](/assets/img/chain-of-responsibility-pattern-meets/1.png)](/assets/img/chain-of-responsibility-pattern-meets/1.png)On the right there is a response with car unique id, obtained in StoreCarHandler.
If I look into the application logs, I see every handler in chain being invoked successfully.
Now, I remove the \<weight\> tag causing corresponding Car attribute to be null:

[![](/assets/img/chain-of-responsibility-pattern-meets/2.png)](/assets/img/chain-of-responsibility-pattern-meets/2.png)Great, ValidationHandler worked and if you took a closer look at the application logs, no further handlers were invoked, stopping the process.
But now let us play a bit with the chain itself.
First, I turn off TransactionalHandler to see whether MANDATORY propagation works.
By "turning off" I mean removing from handlersList in Spring context file.
Quick application restart and...

[![](/assets/img/chain-of-responsibility-pattern-meets/3.png)](/assets/img/chain-of-responsibility-pattern-meets/3.png)The error message isn’t very descriptive, hiding the true cause of the problem.
If you feel your application should be more verbose, simply turn off ExceptionTranslatorHandler, and after restarting the same message will produce:

[![](/assets/img/chain-of-responsibility-pattern-meets/4.png)](/assets/img/chain-of-responsibility-pattern-meets/4.png)Even though I have shown a negative example of how to break the application by inappropriately modifying the chain, this simple case study still gives you a lot of flexibility.
For example whether LoggingHandler should go before or rather after ValidationHandler?
The other open question is the place to put Perf4jHandler.
Because part of the request is processed asynchronously in a thread pool, should we measure only the time the task was executed (Perf4jHandler after HandlerWithTimeout) or maybe whole processing time (including the time the task spent in queue, waiting for available thread while all are busy – the opposite sequence of handlers).
Or maybe we should duplicate Perf4jHandler and monitor both, because significant difference would mean that many executions are awaiting in queues...

That is all about chain of responsibility pattern – in this part of the article.
To sum things up, advantages of the chain of responsibility pattern are:

- Flexibility – chain can be easily configured, altering the system behavior without or with a little modification in code
- Testability – thanks to louse coupling promoted by this pattern each handler can be unit tested as well as easy integration testing of any handlers combination
- Readability – It is much easier to read a single class focused on one purpose rather than having a big class, even properly divided into methods
- Maintainability – adding, removing and changing the order of handlers is very easy.
  Also modifying existing handlers is easier
- ...also logging, profiling, etc. is centralized in a single place (RegistrationChain)

Disadvantages:

- Some people find it harder (?)
  to follow the process when it is split into several classes, especially when the order is configured somewhere else
- Wrong chain configuration might harm the application, I showed an example

I hope you felt a bit annoyed by the need of restarting the application after each chain modification.
I also hope you were disappointed about how primitive this process was (modifying Spring XML).
All your concerns are going to be addressed in the [second part](http://nurkiewicz.com/2009/12/chain-of-responsibility-pattern-meets.html) (did you notice Wicket in the title?)
And in the mean time feel free to ask questions about this wonderful pattern.
