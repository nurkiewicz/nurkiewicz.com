---
layout: post
title: Invoking secured remote EJB in JBoss 5
date: '2009-08-03T23:59:00.003+02:00'
author: Tomasz Nurkiewicz
tags:
- ejb
- jboss
modified_time: '2009-08-04T00:17:06.625+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2907566374522626524
blogger_orig_url: https://www.nurkiewicz.com/2009/08/invoking-secured-remote-ejb-in-jboss-5.html
---

While preparing for SCBCD exam I encountered many difficulties in securing remote EJB 3 stateless session bean, and then calling such a component from remote standalone client.
I hope this short introduction will help you… avoiding this problem.
First, I simply put security annotations on my bean as follows:

```java
@Stateless
@RolesAllowed("ROLE_ADMIN")
@PermitAll
public class DateServiceBean implements DateServiceRemote {
 //...
}
```

Surprisingly such a bean can be easily deployed on JBoss 5.1.0 application server and all its methods are available.
Why surprise?
Because no ROLE_ADMIN was defined in JBoss nor the client was authorized.
As the role was not defined, server silently ignored the security annotation!
I learned my lesson – always verify security configuration, especially whether it actually secures anything…

Quick tour over JBoss documentation and I discovered @org.jboss.annotation.security.SecurityDomain annotation, which should mark all the beans using declarative as well as programmatic security, next to @RolesAllowed.
This does not look well – not only this annotation needs to be repeated in every session bean (and what happens if you forget?
– nothing, security is then ignored…), but it brings compile-time dependency on JBoss specific class!
Fortunately, good-old-XML can be used:

```xml
<jboss>
 <security-domain>dateserver</security-domain>
</jboss>
```

This short snippet in jboss.xml, which must be included in ejb-jar file, specifies the security domain name (dateserver) to be used by whole application.
The same name should be referenced in login-config.xml file, located in JBoss distribution (typically server/default/conf directory):

```xml
<application-policy name="dateserver">
  <authentication>
    <login-module code="org.jboss.security.auth.spi.UsersRolesLoginModule" flag="required">
      <module-option name="usersProperties">props/dateserver-users.properties</module-option>
      <module-option name="rolesProperties">props/dateserver-roles.properties</module-option>
    </login-module>
</authentication>
```

Just put this by the end of login-config.xml file and restart JBoss.
Does describing dateserver-users.properties and dateserver-roles.properties is necessary?
First consists of username=password items and second: username=role1, role2, role3 mappings.
Now we have successfully secured our remote EJBs, which quick test from Java SE client proves:

javax.ejb.EJBAccessException: Caller unauthorized
at org.jboss.ejb3.security.RoleBasedAuthorizationInterceptorv2.invoke(RoleBasedAuthorizationInterceptorv2.java:199)
at org.jboss.aop.joinpoint.MethodInvocation.invokeNext(MethodInvocation.java:102)
\[...\]
Needless to say, the journey begins here...
After few frustrating tries, I still couldn’t manage to log on application server and call secured method, using all varieties of standard lookup code:

```java
Hashtable<String, String> properties = new Hashtable<String, String>();
properties.put(Context.INITIAL_CONTEXT_FACTORY, "org.jboss.naming.NamingContextFactory");
properties.put(Context.PROVIDER_URL, "jnp://localhost:1099");
properties.put(Context.URL_PKG_PREFIXES, "org.jnp.interfaces");
properties.put(Context.SECURITY_PRINCIPAL, "user");
properties.put(Context.SECURITY_CREDENTIALS, "password");
Context context = new InitialContext(properties);
DateServiceRemote dateService = (DateServiceRemote) context.lookup("DateServiceBean/remote");
```

JBoss totally ignores authentication data provided to the InitialContext, repeatedly returning "Caller unauthorized".
Finally, I found out that this server since 5.0 version has its own, non-standard API for managing user authentication:

```java
SecurityClient securityClient = SecurityClientFactory.getSecurityClient();
try {
 securityClient.setSimple("username", "password");
 securityClient.login();
 //perform JNDI lookup and call business method as usual WITHOUT authentication
} finally {
   securityClient.logout();
}
```

This is totally awful!
– not only JBoss forces me to use container specific classes (org.jboss.security.client.SecurityClient), the API itself isn’t very well designed.
Please note, that although SecurityClient instance is created, it is never passed to the InitialContext or propagated by any other way.
This smells like nasty ThreadLocal and will behave unexpectedly if you forget to logout and reuse the thread (e.g.
when pooling in client).
JBoss finally catches up usernames and validates them against password, discovers user roles and applies security to EJBs.
But, IMHO, the price is very high.
I could stand JBoss client libraries on my CLASSPATH, I somehow avoided vendor specific annotations.
But all in all, some strange client class must be used.
What’s the point of this whole standardization, JSRs and tons of specifications, if even the simplest use case cannot be implemented without making my hands dirty?

P.S.: I'm starting to blog in English.
Comments are welcome, but please be gentle ;-).
