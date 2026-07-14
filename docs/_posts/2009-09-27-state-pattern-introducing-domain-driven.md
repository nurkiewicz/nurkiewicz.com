---
layout: post
title: 'State pattern: introducing domain-driven design'
date: '2009-09-27T14:46:00.006+02:00'
author: Tomasz Nurkiewicz
tags:
- design patterns
- ddd
modified_time: '2013-04-07T13:23:12.039+02:00'
thumbnail: /assets/img/state-pattern-introducing-domain-driven/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5561718808315316801
blogger_orig_url: https://www.nurkiewicz.com/2009/09/state-pattern-introducing-domain-driven.html
---

Some domain objects in many enterprises applications include a concept of state.
State has two main characteristics: the behavior of domain object (how it responds to business methods) depends on the state and business methods may change the state forcing the object to behave differently after being invoked.

If you can’t image any real-life example of domain objects’ state, think of a Car entity in rental company.
The Car, while remaining the same object, has additional flag called status, which is crucial for the company.
The flag may have three values: AVAILABLE, RENTED and MISSING.
It is obvious that the Car in RENTED or MISSING state cannot be rented at the moment and rent() method should fail.
But when the car is back and its status is AVAILABLE, calling rent() on Car instance should clearly, apart from remembering customer who rented the car, changing the car status to RENTED.
The status flag (probably single character or int in your database) is an example of objects’ state, as it influences the business methods and vice-versa, business methods can change it.

Now think for a while, how would you implement this scenario which, I am sure, you have seen many times at work.
You have many business methods depending on current state and probably many states.
If you love object oriented programming, you might immediately thought about inheritance and creating AvailableCar, RentedCar and MissingCar extending Car.
It looks good, but is very impractical, especially when Car is persistent object.
And actually this approach is not well designed: it is not the whole object that changes, but only a piece of its internal state – we are not replacing object, only changing it.
Maybe you thought about cascade of if-else-if-else...
in each method performing different task depending on state.
Don’t go there, believe me, it is the path to the Code Maintenance Hell.

But we are going to use inheritance and polymorphism though, but in more clever way: using State GoF pattern.
As an example I have chosen Reservation entity which can have following statuses:

[![](/assets/img/state-pattern-introducing-domain-driven/1.png)](/assets/img/state-pattern-introducing-domain-driven/1.png)

Flow is simple – when the reservation is created, it has NEW status (state).
Then some authorized person can accept the reservation, causing (let’s say) seat to be temporarily reserved and sending user an e-mail asking to pay for the reservation.
Then, when user performs money transfer, money is accounted, ticket printed and second e-mail sent to the client.
Of course you are aware that some actions have dramatically different side-effects depending on Reservation current status.
For example you can cancel reservation at any time, but depending on Reservation status this may result in transferring money back and cancelling reservation or only in sending user an e-mail.
Also some actions have no sense in particular statuses (what if user transferred money to already-cancelled reservation?)
or should be ignored.
Now image how hard it would be to write each business method exposed on state machine diagram above, if you had to use if-else construct for every status and every method...

Unlike my previous posts I will not explain [original](http://en.wikipedia.org/wiki/State_pattern) GoF State design pattern.
Instead I will introduce my little variation over this pattern using Java 5 enum capabilities.
In lieu of creating abstract class/interface for state abstraction and writing implementation for each state, I have simply created enum containing all available states/statuses:

```java
public enum ReservationStatus {

 NEW,

 ACCEPTED,

 PAID,

 CANCELLED;

}
```

Also I created interface for all business methods depending on status, which seems to be a good idea.
Treat this interface as abstract base for all states, but we are going to use it in a bit different way:

```java
public interface ReservationStatusOperations {

 ReservationStatus accept(Reservation reservation);

 ReservationStatus charge(Reservation reservation);

 ReservationStatus cancel(Reservation reservation);

}
```

And finally Reservation domain object, which happens to be JPA entity (getters/setters omitted, or maybe we can just use Groovy and forget about them?):

```java
public class Reservation {

 private int id;

 private String name;

 private Calendar date;

 private BigDecimal price;

 private ReservationStatus status = ReservationStatus.NEW;



 //getters/setters



}
```

[![](/assets/img/state-pattern-introducing-domain-driven/2.png)](/assets/img/state-pattern-introducing-domain-driven/2.png)

If Reservation is persistent domain object, its status (ReservationStatus) should obviously be persistent as well.
This observation brings us to the first big advantage of using enum instead of abstract class: JPA/Hibernate can easily serialize and persist Java enum in database using enum’s name or ordinal value (by default).
In original GoF pattern we would rather put ReservationStatusOperations direcly in domain object and switch implementations when status changes.
I suggest to use enum and only change enum value.
Another (less framework-centric and more important) advantage of using enum is that all possible states are listed in one place.
You don’t have to crawl your source code in search for all implementations of base State class – everything can be seen in one, comma-separated list.

OK, take a deep breath, now I will explain how all the pieces work together and why, on earth, business operations in ReservationStatusOperations return ReservationStatus.
First, you must recall what actually enum’s are.
They are not just a collection of constants in single namespace like in C/C++.
In Java, enum is rather a closed set of classes that inherit from common base class (e.g.
ReservationStatus), which in turns inherits from [Enum](http://java.sun.com/javase/6/docs/api/java/lang/Enum.html).
So while using enums, we might take advantage of polymorphism and inheritance:

```java
public enum ReservationStatus implements ReservationStatusOperations {



 NEW {

   public ReservationStatus accept(Reservation reservation) {

       //..

   }



   public ReservationStatus charge(Reservation reservation) {

       //..

   }



   public ReservationStatus cancel(Reservation reservation) {

       //..

   }

 },



 ACCEPTED {

   public ReservationStatus accept(Reservation reservation) {

    //..

   }



   public ReservationStatus charge(Reservation reservation) {

       //..

   }



   public ReservationStatus cancel(Reservation reservation) {

       //..

   }

 },



 PAID {/*...*/},



 CANCELLED {/*...*/};

}
```

Although it’s tempting to write ReservationStatusOperations in such a manner, it’s a bad idea for a long term development.
Not only the enum source code would be extensively long (total number of implemented methods would be equal to a number of statuses multiplied by number of business methods), but also badly designed (business logic for all states in single class).
Also, enum implementing interface and rest of this fancy syntax may be counterintuitive for anyone who didn’t passed SCJP exam in last 2 weeks.
Instead, we will provide some simple level of indirection, because "Any problem in computer science can be solved with another layer of indirection" [\[\*\]](http://en.wikipedia.org/wiki/David_Wheeler_%28computer_scientist%29):

```java
public enum ReservationStatus implements ReservationStatusOperations {



  NEW(new NewRso()),

  ACCEPTED(new AcceptedRso()),

  PAID(new PaidRso()),

  CANCELLED(new CancelledRso());



  private final ReservationStatusOperations operations;



  ReservationStatus(ReservationStatusOperations operations) {

     this.operations = operations;

  }



  @Override

  public ReservationStatus accept(Reservation reservation) {

     return operations.accept(reservation);

  }



  @Override

  public ReservationStatus charge(Reservation reservation) {

     return operations.charge(reservation);

  }



  @Override

  public ReservationStatus cancel(Reservation reservation) {

     return operations.cancel(reservation);

  }

}
```

This is the final source code for our ReservationStatus enum (implementing ReservationStatusOperations is not necessary).
To put things simple: each enum value has its own distinct implementation of ReservationStatusOperations (Rso for short); this implementation is passed as a constructor argument and assigned to final field operations.
Now, whenever business method is called on enum, it will be delegated to ReservationStatusOperations implementation dedicated to this enum:

```java
ReservationStatus.NEW.accept(reservation);        //will call NewRso.accept()

ReservationStatus.ACCEPTED.accept(reservation);        //will call AcceptedRso.accept()
```

The last piece of the puzzle is Reservation domain object including business methods:

```java
public void accept() {

  setStatus(status.accept(this));

}



public void charge() {

  setStatus(status.charge(this));

}



public void cancel() {

  setStatus(status.cancel(this));

}



public void setStatus(ReservationStatus status) {

  if (status != null && status != this.status) {

     log.debug("Reservation#" + id + ": changing status from " + this.status + " to " + status);

     this.status = status;

  }
```

What happens here?
When you call any business method on Reservation domain object instance, corresponding method is being called on ReservationStatus enum value.
Depending on current status, different method (of different ReservationStatusOperations implementation) will be called.
But there is no switch-case or if-else construct, only pure polymorphism.
For example if you call charge() when status field points to ReservationStatus.ACCEPTED, AcceptedRso.charge() is being called, the customer who made the reservation will be charged and reservation status changes to PAID.
But what happens if we call charge() again on the same instance?
status field now points to ReservationStatus.PAID, so PaidRso.charge() will be executed, which throws exception (charging already paid reservation is invalid).
With no conditional code, we implemented state-aware domain object with business methods included in the object itself.

One thing I haven’t mentioned yet is how to change the status from business method.
This is the second difference from original GoF pattern.
Instead of passing StateContext instance to each state-aware operation (like accept() or charge()), which can be used to change the status, I simply return new status from business method.
If the status is not null and different from the previous one (setStatus() method), reservation transits to a given status.
Let’s take a look at how it works on AcceptedRso object (its methods are being executed when Reservation is in ReservationStatus.ACCEPTED status):

```java
public class AcceptedRso implements ReservationStatusOperations {



@Override

public ReservationStatus accept(Reservation reservation) {

   throw new UnsupportedStatusTransitionException("accept", ReservationStatus.ACCEPTED);

}



@Override

public ReservationStatus charge(Reservation reservation) {

   //charge client's credit card

   //send e-mail

   //print ticket

   return ReservationStatus.PAID;

}



@Override

public ReservationStatus cancel(Reservation reservation) {

   //send cancellation e-mail

   return ReservationStatus.CANCELLED;

}



}
```

Behavior of Reservation in ACCEPTED status can be easily followed by reading class above: accepting for the second time (reservation is already accepted) will throw an exception, charging will charge client’s credit card, print him a ticket and send e-mail etc. Also, charging returns PAID status, which will cause the Reservation to transit to this state.
This means another call to charge() will be handled by different ReservationStatusOperations implementation (PaidRso) with no conditional code.

This would be all about the State pattern.
If you are not convinced to this design pattern, compare the amount of work and how error-prone it is with classic approach using conditional code.
Also think for a while what is needed when adding new state or state-dependent operation and how easy it is to read such a code.

I didn’t show all ReservationStatusOperations implementations, but if you would like to introduce this approach in your Spring or EJB based JEE application, you have probably saw a big lie out there.
I gave comments on what should happen in each business methods, but not provided actual implementations.
I didn’t, because I would come across big problem: Reservation instance is created by hand (using new) or by persistence framework like Hibernate.
It uses statically created enum which creates manually ReservationStatusOperations implementations.
There is no way to inject any dependencies, DAOs and services, to this classes, as their lifecycle is controlled out of the Spring or EJB container scope.
Actually, there is a simple yet powerful solution, using Spring and AspectJ.
But be patient, I will explain it in details in the next post soon, adding some domain-driven flavor to our application.
