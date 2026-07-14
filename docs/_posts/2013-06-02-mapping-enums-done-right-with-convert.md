---
layout: post
title: Mapping enums done right with @Convert in JPA 2.1
date: '2013-06-02T23:00:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- eclipselink
- jpa
- spring
modified_time: '2013-06-02T23:00:42.617+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-6873036090398150824
blogger_orig_url: https://www.nurkiewicz.com/2013/06/mapping-enums-done-right-with-convert.html
image:
  path: /assets/img/mapping-enums-done-right-with-convert/hero.jpg
  alt: "Torshovdalen"
---

If you ever worked with Java enums in JPA you are definitely aware of their limitations and traps.
Using `enum` as a property of your `@Entity` is often very good choice, however JPA prior to 2.1 didn’t handle them very well.
It gave you 2+1 choices:

1.  `@Enumerated(EnumType.ORDINAL)` (default) will map `enum` values using [`Enum.ordinal()`](http://docs.oracle.com/javase/7/docs/api/java/lang/Enum.html#ordinal()).
    Basically first enumerated value will be mapped to `0` in database column, second to `1`, etc. This is very compact and works great to the point when you want to modify your enum.
    Removing or adding value in the middle or rearranging them will totally break existing records.
    Ouch!
    To make matters worse, unit and integration tests often work on clean database, so they won’t catch discrepancy in old data.
2.  `@Enumerated(EnumType.STRING)` is much safer because it stores string representation of `enum`.
    You can now safely add new values and move them around.
    However renaming `enum` in Java code will still break existing records in DB.
    Even more important, such representation is very verbose, unnecessarily consuming database resources.
3.  You can also use raw representation (e.g.
    single `char` or `int`) and map it manually back and forth in `@PostLoad`/`@PrePersist`/`@PreUpdate` events.
    Most flexible and safe from database perspective, but quite ugly.

Luckily [Java Persistence API 2.1](https://java.net/projects/jpa-spec/) ([JSR-388](http://jcp.org/en/jsr/detail?id=338)) released few days ago provides standardized mechanism of [pluggable data converters](http://en.wikibooks.org/wiki/Java_Persistence/Basic_Attributes#Converters_.28JPA_2.1.29).
Such API was present for ages in proprietary forms and it’s not really rocket science, but having it as part of JPA is a big improvement.
To my knowledge [Eclipselink](http://www.eclipse.org/eclipselink/) is the only JPA 2.1 implementation available to date, so we will use it to experiment a bit.

We will start from [sample Spring application](https://github.com/nurkiewicz/books) developed as part of [“*Poor man’s CRUD: jqGrid, REST, AJAX, and Spring MVC in one house*”](http://nurkiewicz.blogspot.no/2011/07/poor-mans-crud-jqgrid-rest-ajax-and.html) article.
That version had no persistence, so we will add thin DAO layer on top of Spring Data JPA backed by Eclipselink.
Only entity so far is `Book`:

```java
@Entity
public class Book {

    @Id
    @GeneratedValue(strategy = IDENTITY)
    private Integer id;

    //...

    private Cover cover;

    //...
}
```

Where `Cover` is an `enum`:

```java
public enum Cover {

    PAPERBACK, HARDCOVER, DUST_JACKET

}
```

Neither `ORDINAL` nor `STRING` is a good choice here.
The former because rearranging first three values in any way will break loading of existing records.
The latter is too verbose.
Here is where custom converters in JPA come into play:

```java
import javax.persistence.AttributeConverter;
import javax.persistence.Converter;

@Converter
public class CoverConverter implements AttributeConverter<Cover, String> {

    @Override
    public String convertToDatabaseColumn(Cover attribute) {
        switch (attribute) {
            case DUST_JACKET:
                return "D";
            case HARDCOVER:
                return "H";
            case PAPERBACK:
                return "P";
            default:
                throw new IllegalArgumentException("Unknown" + attribute);
        }
    }

    @Override
    public Cover convertToEntityAttribute(String dbData) {
        switch (dbData) {
            case "D":
                return DUST_JACKET;
            case "H":
                return HARDCOVER;
            case "P":
                return PAPERBACK;
            default:
                throw new IllegalArgumentException("Unknown" + dbData);
        }
    }
}
```

OK, I won’t insult you, my dear reader, explaining this.
Converting enum to whatever will be stored in relational database and vice-versa.
Theoretically JPA provider should apply converters automatically if they are declared with:

```java
@Converter(autoApply = true)
```

It didn’t work for me.
Moreover declaring them explicitly instead of `@Enumerated` in `@Entity` class didn’t work as well:

```java
import javax.persistence.Convert;

//...

@Convert(converter = CoverConverter.class)
private Cover cover;
```

Resulting in exception:

```java
Exception Description: The converter class [com.blogspot.nurkiewicz.CoverConverter] 
specified on the mapping attribute [cover] from the class [com.blogspot.nurkiewicz.Book] was not found. 
Please ensure the converter class name is correct and exists with the persistence unit definition.
```

Bug or feature, I had to mention converter in `orm.xml`:

```xml
<?xml version="1.0"?>
<entity-mappings xmlns="http://www.eclipse.org/eclipselink/xsds/persistence/orm" version="2.1">
    <converter class="com.blogspot.nurkiewicz.CoverConverter"/>
</entity-mappings>
```

And it flies!
I have a freedom of modifying my `Cover` enum (adding, rearranging, renaming) without affecting existing records.

One tip I would like to share with you is related to maintainability.
Every time you have a piece of code mapping from or to `enum`, make sure it’s tested properly.
And I don’t mean testing every possible existing value manually.
I am more after a test making sure that new `enum` values are reflected in mapping code.
Hint: code below will fail (by throwing `IllegalArgumentException`) if you add new `enum` value but forget to add mapping code *from* it:

```java
for (Cover cover : Cover.values()) {
    new CoverConverter().convertToDatabaseColumn(cover);
}
```

------------------------------------------------------------------------

Custom converters in JPA 2.1 are much more useful than what we saw.
If you combine JPA with Scala, you can use `@Converter` to map database columns directly to [`scala.math.BigDecimal`](http://www.scala-lang.org/api/current/index.html#scala.math.BigDecimal), [`scala.Option`](http://www.scala-lang.org/api/current/index.html#scala.Option) or small case class.
In Java there will finally be a portable way of mapping [Joda time](http://joda-time.sourceforge.net/).
Last but not least, if you like (very) strongly typed domain, you may wish to have `PhoneNumber` class (with `isInternational()`, `getCountryCode()` and custom validation logic) instead of `String` or `long`.
This small addition in JPA 2.1 will surely improve domain objects quality significantly.

If you wish to play a bit with this feature, sample Spring web application is [available on GitHub](https://github.com/nurkiewicz/books).
