---
layout: post
title: Injecting methods at runtime to Java class in Groovy
date: '2009-09-03T22:16:00.004+02:00'
author: Tomasz Nurkiewicz
tags:
- groovy
- grails
- gorm
modified_time: '2009-09-04T08:20:57.848+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2901628059548618993
blogger_orig_url: https://www.nurkiewicz.com/2009/09/injecting-methods-at-runtime-to-java.html
---

I recently finished reading "[Programming Groovy: Dynamic Productivity for the Java Developer](http://www.amazon.com/Programming-Groovy-Productivity-Developer-Programmers/dp/1934356093)" and this book really opened my eyes on what Groovy language really is.
Most tutorials or lectures I have attended are focused on syntactical sugar: closures, operator overloading, easier access to bean properties or maps.
Elvis operator, spread operator, spaceship operator...

But the strength of Groovy is not syntactic sugar on a Java cake.
Groovy is a brand new dish with really exotic taste, which not everybody would enjoy.
The gap between Java and Groovy is really huge, although they integrate tightly and seamlessly.
But remember, Firefox did not became so popular because it was so similar to IE, but because it was different [\[1\]](http://linux.oneandoneis2.org/LNW.htm).
Maybe Groovy is not better than Java, but is certainly worth trying.
Thanks to "Programming Groovy..." I realized what amazing things can be done using Groovy which you would never even thought about in Java.

As Chinese said, Java code is worth more than a thousand words (or something like that[...](http://en.wikipedia.org/wiki/A_picture_is_worth_a_thousand_words)), I’ll give you some short example announced in post title.
Suppose you have some POJO:

```java
public class Person {
  private String name;
  private Calendar dateOfBirth;
  private BigDecimal salary;

  public String getName() {
   return name;
  }

  public void setName(String name) {
   this.name = name;
  }

  public Calendar getDateOfBirth() {
   return dateOfBirth;
  }

  public void setDateOfBirth(Calendar dateOfBirth) {
   this.dateOfBirth = dateOfBirth;
  }

  public BigDecimal getSalary() {
   return salary;
  }

  public void setSalary(BigDecimal salary) {
   this.salary = salary;
  }
}
```

Yes, this is Java class, remember that.
Our task is to create simple validator, which will check whether all properties are not-null of a particular Java Bean instance (e.g Person).
If any null field found, exception should be thrown.

Doing this in the classic way, you would write some sort of utility class with method like:

```java
public static void validate(Object pojo) throws IllegalStateException {/*...*/}
```

This approach is so obvious, that I won’t even explain this API.
Behind the scenes some nasty reflection with tons of exception handling and method name parsing code will be used to make the method generic.
If you are clever, you would use [Commons-BeanUtils](http://commons.apache.org/beanutils/api/org/apache/commons/beanutils/PropertyUtils.html).
But this is still poor object-oriented design, as data (properties of a JavaBean) and operations (validate() method operating on data) are separated.
Wouldn’t it be great to have validate() method in Person and every other bean you wish?
To achieve this, you would probably think about inheritance and placing validate() in some abstract base class of all your Java Beans.

No, stop that!
This is still bad design, although much more subtle.
Inheritance represents is-a relationship.
If you want to use the same operation in many objects, you should rather use delegation.
See "Replace Inheritance with Delegation" chapter in Fowler’s "[Refactoring: improving the design of existing code](http://www.amazon.com/Refactoring-Improving-Design-Existing-Code/dp/0201485672)" (I know, I know, some parts of the book are not so [outdated](http://nurkiewicz.com/2009/08/java-concurrency-in-practice-written-by.html) :-)).
But if you are not so sensitive about code design (why?!?), there is another problem – this approach cannot be applied to third-party classes, which you are not allowed to change.

This is the place where Groovy comes in with its amazing dynamic capabilities.
First I will prepare some Groovy test case, which will explain what I am trying to achieve.
Test-driven development, anybody?

```java
public class PersonTest extends GroovyTestCase {

void testAllPropertiesNullShouldThrow() {
 def person = new Person();
 shouldFail(IllegalStateException) {person.validate()}
}

void testSingleNullPropertyShouldThrow() {
 def person = new Person(name: "John Smith", salary: 1234d)
 shouldFail(IllegalStateException) {person.validate()}
}

void testAllPropertiesSetShouldNotThrow() {
 def person = new Person(name: "John Smith", dateOfBirth: Calendar.instance, salary: 1234d)
 person.validate()
}

}
```

Read those tests carefully.
Not because I use elegant shouldFail() template nor very concise way of initializing POJO (even though it does not have any non-default constructor!)
The most surprising fact is that I run validate() method on Person class instance and the code compiles just fine!
It doesn’t matter this method does not exist on compile time, even if it is Java object.
Groovy’s dynamic.
But what happen if I run this test?

```java
groovy.lang.MissingMethodException: No signature of method: Person.validate() is applicable for argument types: () values: []
at org.codehaus.groovy.runtime.ScriptBytecodeAdapter.unwrap(ScriptBytecodeAdapter.java:54)
at org.codehaus.groovy.runtime.callsite.PojoMetaClassSite.call(PojoMetaClassSite.java:46)
at org.codehaus.groovy.runtime.callsite.CallSiteArray.defaultCall(CallSiteArray.java:40)
at org.codehaus.groovy.runtime.callsite.AbstractCallSite.call(AbstractCallSite.java:117)
at org.codehaus.groovy.runtime.callsite.AbstractCallSite.call(AbstractCallSite.java:121)
at PersonTest.testAllPropertiesSetShouldNotThrow(PersonTest.groovy:30)
at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:39)
at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:25)
at com.intellij.rt.execution.junit.JUnitStarter.main(JUnitStarter.java:40)
at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:39)
at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:25)
at com.intellij.rt.execution.application.AppMain.main(AppMain.java:90)
```

Surely, Person Java class does not have validate() method, even if Groovy compiler assumed differently.
So you might ask yourself, what is the purpose of such a weak compilation?
Well, now comes the best part:

```java
void setUp() {
 Person.metaClass.validate = {->
     delegate.properties.each {property, value ->
         if (value == null)
             throw new java.lang.IllegalStateException("Property $property is null")
     }
 }
}
```

What I’ve done here is I injected method called validate() to meta class of Person Java class at runtime.
Since now, every instance of Person class is capable of handling validate() method even though this method has not been known during compilation.
Quick test case execution and...
success, not only the method is known, but it works as expected.

I won’t discuss details of validate() implementation, simply try to rewrite it in Java, you’ll see the difference.
But it is not the point!
I created brand new method and applied it to arbitrary Java class (of course, if Person was Groovy class, it would work as well).
This is absolutely impossible in static Java.
And if I add that by implementing methodMissing() object could handle ANY nonexistent method call...

You might ask yourself once again, what is the purpose of such a dangerous and unpredictable toy?
Well, I am about to obtain "[The Definitive Guide to Grails](http://www.amazon.com/Definitive-Grails-Second-Experts-Development/dp/1590599950)"\*, which also explains GORM framework.
If you would like to make Person class persistent, Groovy ORM will automatically inject save() method to Person class, so you could write:

```java
new Person(name: "John Smith").save()
```

No DAO, no session, na EntityManager.
But you could also write:

```java
def list = Person.findByNameLikeAndSalaryGreaterThan("John%", 1000)
```

Where is the implementation of this not-so-simple method?
You don’t have to implement it, Groovy will!
It will discover that such a method does not exist in Person class, parse the name and create proper SQL with AND and LIKE operators on Person table, issue SQL and map to a list of Person instances.
If this is not magic, go back to your Hibernate, as I find such features absolutely exciting and innovative.

I am just playing with Groovy, but I found this language to have many unexpectedly interesting parts.
It is not a replacement of Java, but a great tool to combine and interact with its older brother.

\* many thanks to my [employer](http://www.javart.com.pl) for sponsoring aforementioned books
