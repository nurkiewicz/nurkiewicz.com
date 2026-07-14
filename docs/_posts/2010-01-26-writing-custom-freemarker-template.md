---
layout: post
title: Writing custom FreeMarker template loaders in Spring
date: '2010-01-26T23:24:00.003+01:00'
author: Tomasz Nurkiewicz
tags:
- freemarker
- spring
modified_time: '2010-01-26T23:42:29.277+01:00'
thumbnail: /assets/img/writing-custom-freemarker-template/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1639671970752023219
blogger_orig_url: https://www.nurkiewicz.com/2010/01/writing-custom-freemarker-template.html
---

...or "Thou shalt not hard-code any output messages in Java code".

Code is for program, algorithm, behavior, action.
Code in any programming language is intended to express the data flow, not the data itself!
But many programmers are forgetting about this rule, putting lots of data, both input and output, in source code.
While hard-coding input data instead of loading it from some external resource is easy to spot, hard-coded parts of the output data are even more common.
Typical examples are:

- Localized messages shown to the user.
  If you have a class with (...public static final...)
  strings containing different messages sent to the user, you might be proud of having all UI-specific labels in one place.
  Wrong!
  Changing messages require recompilation, as well as adding new translations (another classes?)
  Also all this strings are constantly present in the memory (PermGen space), being referenced by the class.
- Contents of exception messages.
  This is part of a bigger problem of error handling: pass exception to the user interface and display original error message or create some sophisticated exception-translation mechanism?
  But if your user interface is not in English, would you throw an exception with localized message?
- Printing HTML directly from a Servlet.
  Never do this!
  If you are unlucky and working directly with servlets, at least use request attributes and redirect from servlet to JSP.
  Using string concatenation and producing markup in Java code looks terrible and is very inefficient.
- Producing other types of content (reports, XML, e-mail) similar to the servlet way mentioned above: by using string concatenations, typically in loops with many conditions.
- Complicated SQL queries and even whole procedures.
  If the SQL query is parameterized (almost always), programmers tend to produce the query using string concatenation, also making their application vulnerable to [SQL injection](http://en.wikipedia.org/wiki/SQL_injection).
  In this scenario use named parameters or [iBATIS](http://ibatis.apache.org).

To make our case study code a bit better we are going to implement e-mail sending functionality example without hard-coding e-mail contents in Java sources.
Actually, contents are going to be stored in the database as a [FreeMarker](http://freemarker.org) templates, giving users flexibility of FreeMarker markup and ability to change the form of e-mail in any time (by issuing database update).

Unfortunately (and as expected) FreeMarker has only few built-in mechanisms for loading templates (e.g.
directly from the file system).
But, also as expected, this mechanism can be easily (?)
extended.
The question mark is not here because of the complexity of this process, but very poor design of FreeMarker template loading API (see discussion at the end of this article).

In order to make FreeMarker read templates from any source, one must implement [TemplateLoader](http://freemarker.org/docs/api/freemarker/cache/TemplateLoader.html) interface.
Before we take a look at it, another abstraction must be taken into account: [TemplateCache](http://freemarker.org/docs/api/freemarker/cache/TemplateCache.html).
It seems like loading and compiling templates takes significant amount of time for FreeMarker, so it lazy-loads and caches templates.
Of course if the template has changed, FreeMarker must be able to discover it and invalidate the cache.
Now we are finally ready to take a look at TemplateLoader interface and understand how it works, do we?

```java
public interface TemplateLoader {
   public Object findTemplateSource(String name) throws IOException;
   public long getLastModified(Object templateSource);
   public Reader getReader(Object templateSource, String encoding) throws IOException;
   public void closeTemplateSource(Object templateSource) throws IOException;
}
```

Is it obvious to you what all the methods do?
And why getLastModified() does not declare IOException like other methods?

findTemplateSource() returns some object (name suggests it is template source).
All other methods are taking templateSource as an argument.
I had to study few built-in implementations to finally discover how it works.
When implementing custom template loader, findTemplateSource() should return something that denotes source of a specific template given by name.
This something (literally any Object instance) is then used by FreeMarker as a key in its cache, where value is the template itself ([Template](http://freemarker.sourceforge.net/docs/api/freemarker/template/Template.html) instance).
If the value denoted by this key is not found, FreeMarker asks TemplateLoader again to read template contents via getReader().
If template is already found in cache, FreeMarker will just check whether the template has not been modified in the meantime (using getLastModified()) and re-read template if necessary.

Enough of the theory.
We are going to store our e-mail templates in the following JPA entities:

```java
@Cache(usage = CacheConcurrencyStrategy.NONSTRICT_READ_WRITE)
public class EmailTemplate {

   private String name;
   private String content;
   private Calendar lastModified = Calendar.getInstance();

   public void updateLastModified() {
       setLastModified(Calendar.getInstance());
   }

}
```

Getters/setters, as always, omitted – if only I used Groovy, I would never have to write this clause again.

I don't like JPA annotations, if you know how to avoid Hibernates' @Cache and use other source of configuration, please let me know.
So piece of the orm.xml looks like this:

```xml
<entity class="com.blogspot.nurkiewicz.email.EmailTemplate">
   <pre-persist method-name="updateLastModified"/>
   <pre-update method-name="updateLastModified"/>
   <attributes>
       <id name="name"/>
       <basic name="content">
           <column length="10000"/>
           <lob/>
       </basic>
       <basic name="lastModified">
           <temporal>TIMESTAMP</temporal>
       </basic>
   </attributes>
</entity>
```

I use pre-persist and pre-update hooks to automatically update lastModified field.
This is very convenient and one of the very few use cases for these methods – they don't have access to the EntityManager, so, sadly, no audit/trigger functionality can be achieved in plain JPA.

Having entity object representing single e-mail template, all that has left is implementing simple template loader:

```java
@Repository
public class EmailDatabaseTemplateLoader implements TemplateLoader {

   @PersistenceContext
   private EntityManager em;

   public Object findTemplateSource(String name) throws IOException {
       return em.find(EmailTemplate.class, name);
   }

   public long getLastModified(Object templateSource) {
       final EmailTemplate emailTemplate = (EmailTemplate) templateSource;
       em.refresh(emailTemplate);
       return emailTemplate.getLastModified().getTimeInMillis();
   }

   public Reader getReader(Object templateSource, String encoding) throws IOException {
       return new StringReader(((EmailTemplate) templateSource).getContent());
   }

   public void closeTemplateSource(Object templateSource) throws IOException {
   }
}
```

To wire everything up, we must tell Spring to use our template loader, which happens to be a Spring bean with Repository stereotype.
Luckily, Spring has support for FreeMarker.
As you can see even the whole stack of loaders can be configured – if first loader does not find the template, second is asked.
Single loader is fine for us:

```xml
<bean id="freemarkerConfiguration" class="org.springframework.ui.freemarker.FreeMarkerConfigurationFactoryBean">
   <property name="preTemplateLoaders">
       <list>
           <ref bean="databaseTemplateLoader"/>
       </list>
   </property>
</bean>
<bean name="databaseTemplateLoader" class="com.blogspot.nurkiewicz.email.EmailDatabaseTemplateLoader"/>
```

That's all, now we can simply inject [Configuration](http://freemarker.sourceforge.net/docs/api/freemarker/template/Configuration.html) instance into any Spring bean, load some template and process it using given model.
Spring provides handy utility class for that:

```java
String email = FreeMarkerTemplateUtils.processTemplateIntoString(freemarkerCfg.getTemplate("FULL_EMAIL"), emailModel)
```

Well, everything is working, but the purpose of this article was not to help you with developing custom template loader for FreeMarker (although I hope it helped).
My goal was to show you some epic code smell introduced by FreeMarker developers designing TemplateLoader contract.

TemplateLoader might return any object it likes.
The FreeMarker framework does not know anything about the true nature of this object (whether it is File, URL, or your JPA entity instance).
So in order to extract some information from the template source, FreeMarker passes this returned object back to the loader and basically says: "OK, you have returned this previously.
Could you please tell me what is the last modification time of this".
And then: "Nice, so could you please load the template using this somehow".
Wouldn't it be better to call this returned object itself instead of asking third actor (TemplateLoader)?
The object should be able to performs tasks that correspond to its state and make decisions on its own.

This might be considered as a violation of a [Tell, Don't Ask](http://pragprog.com/articles/tell-dont-ask) principle.
Clearly the FreeMarker developers wanted to avoid another abstraction (template source) and simply used Object instead to create an illusion of flexibility.
This is how it should be done:

[![](/assets/img/writing-custom-freemarker-template/1.png)](/assets/img/writing-custom-freemarker-template/1.png)

or even better (can you see the difference?
Why it's better?):

[![](/assets/img/writing-custom-freemarker-template/2.png)](/assets/img/writing-custom-freemarker-template/2.png)

Whenever you see plain Object in the source code, you are almost always missing some abstraction.
Whenever instanceof operator is used (God forbids!), probably polymorphism should have been introduced.
Don't be afraid of refactoring and do not hesitate to use interfaces.
Otherwise you will end up with "map programming" - where each method takes a map and returns a map and every map can nest other maps.
Surely, the flexibility is unbelievable, no classes, no interfaces...
and nobody who would ever be able to maintain such "flexible" code.
