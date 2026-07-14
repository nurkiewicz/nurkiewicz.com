---
layout: post
title: su and sudo in Spring Security applications
date: '2013-06-30T12:09:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- logging
- spring
- spring security
modified_time: '2013-07-15T23:54:16.462+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5411421604732621564
blogger_orig_url: https://www.nurkiewicz.com/2013/06/su-and-sudo-in-spring-security.html
image:
  path: /assets/img/su-and-sudo-in-spring-security/hero.jpg
  alt: "Kolsåstoppen"
---

Long time ago I worked on a project that had a quite powerful feature.
There were two roles: user and supervisor.
Supervisor could change any document in the system in any way while users were much more limited to workflow constraints.
When a normal user had some issue with the document currently being edited and stored in HTTP session, supervisor could step in, switch to special *supervisor* mode and bypass all constrains.
Total freedom.
Same computer, same keyboard, same HTTP session.
Only special flag that supervisor could set by entering secret password.
Once the supervisor was done, he or she could clear that flag and enable usual constraints again.

This feature worked well but it was poorly implemented.
Availability of every single input field was dependent on that *supervisor mode* flag.
Business methods were polluted in dozens of places with `isSupervisorMode()` check.
And remember that if supervisor simply logged in using normal credentials, this mode was sort of implicit so security constraints were basically duplicated.

Another interesting use case arises when our application is highly customizable with plenty of security roles.
Sooner or later you will face anomaly (OK, *bug*) that you simply can’t reproduce having different privileges.
Being able to log in as that particular user and look around might be a big win.
Of course you don’t know the passwords of your users ([*don’t you?*](http://en.wikipedia.org/wiki/Cryptographic_hash_function#Password_verification)).
UNIX-like systems found solution to this problem: [`su`](http://en.wikipedia.org/wiki/Su_(Unix)) (*switch user*) and [`sudo`](http://en.wikipedia.org/wiki/Sudo) commands.
Surprisingly [Spring Security](http://static.springsource.org/spring-security/site/index.html) ships with built-in [`SwitchUserFilter`](http://static.springsource.org/spring-security/site/docs/current/apidocs/org/springframework/security/web/authentication/switchuser/SwitchUserFilter.html) that in principle mimics `su` in web applications.
Let’s give it a try!

All you need is declaring custom filter:

```xml
<bean id="switchUserProcessingFilter"
       class="org.springframework.security.web.authentication.switchuser.SwitchUserFilter">
    <property name="userDetailsService" ref="userDetailsService"/>
    <property name="targetUrl" value="/"/>
</b:bean>
```

and pointing to it in `<http>` configuration:

```xml
<http auto-config="true" use-expressions="true">
    <custom-filter position="SWITCH_USER_FILTER" ref="switchUserProcessingFilter" />
    <intercept-url pattern="/j_spring_security_switch_user" access="hasRole('ROLE_SUPERVISOR')"/>
    ...
```

That’s it!
Notice that I secure `/j_spring_security_switch_user` URL pattern.
You guessed it, that’s how you log in as a different user, thus we want this resource to be well protected.
By default `j_username` parameter name is used.
After applying changes above to your web application and logging in with a user having `ROLE_SUPERVISOR` one can simply browse to:

```text
/j_spring_security_switch_user?j_username=bob
```

And automagically you become logged in as `bob` - assuming there exists such a user.
No password required here.
When you are done impersonating him, browsing to `/j_spring_security_exit_user` will restore your previous credentials.
Of course all these URLs are configurable.
`SwitchUserFilter` is not documented in [*Reference Documentation*](http://static.springsource.org/spring-security/site/docs/current/reference/springsecurity.html) but it is a very useful tool when used with caution.

Indeed *with great power…*.
Giving even most trusted user ability to log in as any other arbitrary user sounds quite risky.
Imagine such a feature on Facebook, impossible!
([well…](http://therumpus.net/2010/01/conversations-about-the-internet-5-anonymous-facebook-employee/?all=1)) Thus tracking and auditing becomes a major requirement.

What I typically do in the first place is adding a small servlet filter right after Spring Security filter that adds user name to [MDC](http://logback.qos.ch/manual/mdc.html):

```java
import org.slf4j.MDC;

public class UserNameFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) throws IOException, ServletException {
        final Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        final String userName = authentication.getName();
        final String realName = findSwitchedUser(authentication);
        final String fullName = userName + (realName != null ? " (" + realName + ")" : "");

        MDC.put("user", fullName);
        try {
            chain.doFilter(request, response);
        } finally {
            MDC.remove("user");
        }
    }

    private String findSwitchedUser(Authentication authentication) {
        for (GrantedAuthority auth : authentication.getAuthorities()) {
            if (auth instanceof SwitchUserGrantedAuthority) {
                return ((SwitchUserGrantedAuthority)auth).getSource().getName();
            }
        }
        return null;
    }

    //...
}
```

Just remember to add it to `web.xml` **after** Spring Security.
At this point you can reference `"user"` key e.g. in `logback.xml`:

```xml
<pattern>%d{HH:mm:ss.SSS} | %-5level | %X{user} | %thread | %logger{1} | %m%n%rEx</pattern>
```

See the `%X{user}` snippet?
Every time logged in user does something in the system that triggers log statement, you will see that users’ name:

```text
21:56:55.074 | DEBUG | alice | http-bio-8080-exec-9 | ...
//...
21:56:57.314 | DEBUG | bob (alice) | http-bio-8080-exec-3 | ...
```

The second log statement is interesting.
If you look at `findSwitchedUser()` call above it becomes obvious that `alice`, being a supervisor, switched to user `bob` and now browses on behalf of him.

Sometimes you need even stronger auditing system.
Luckily Spring framework has built-in event infrastructure and we can take advantage of [`AuthenticationSwitchUserEvent`](http://static.springsource.org/spring-security/site/docs/current/apidocs/org/springframework/security/web/authentication/switchuser/AuthenticationSwitchUserEvent.html) sent both when someone switches user and exits this mode:

```java
@Service
public class SwitchUserListener 
       implements ApplicationListener<AuthenticationSwitchUserEvent> {

    private static final Logger log = LoggerFactory.getLogger(SwitchUserListener.class);

    @Override
    public void onApplicationEvent(AuthenticationSwitchUserEvent event) {
        log.info("User switch from {} to {}",
                event.getAuthentication().getName(),
                event.getTargetUser().getUsername());
    }
}
```

Of course you can replace simple logging with any business logic you desire, e.g. storing such event in database or sending an e-mail to security officer.

------------------------------------------------------------------------

So we know how to log in as a different user for a period of time and then exit such mode.
But what if we need “`sudo`”, that is making just one HTTP request on behalf of some other user?
Of course we can switch to that user, run that request and then exit.
But that seems too heavyweight and cumbersome.
Such a requirement may pop up when client program accesses our API and wants to see data as another user (think about testing complex ACLs).

Adding custom HTTP header to denote such a special impersonating request sounds reasonable.
It works only for the duration of one request, assuming the client is already authenticating, e.g. using JSESSIONID cookie.
Unfortunately this is not supported by Spring Security, but easy to implement on top of `SwitchUserFilter`:

```java
public class SwitchUserOnceFilter extends SwitchUserFilter {

    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain) throws IOException, ServletException {
        HttpServletRequest request = (HttpServletRequest) req;

        final String switchUserHeader = request.getHeader("X-Switch-User-Once");
        if (switchUserHeader != null) {
            trySwitchingUserForThisRequest(chain, request, res, switchUserHeader);
        } else {
            super.doFilter(req, res, chain);
        }
    }

    private void trySwitchingUserForThisRequest(FilterChain chain, HttpServletRequest request, ServletResponse response, String switchUserHeader) throws IOException, ServletException {
        try {
            proceedWithSwitchedUser(chain, request, response, switchUserHeader);
        } catch (AuthenticationException e) {
            throw Throwables.propagate(e);
        }
    }

    private void proceedWithSwitchedUser(FilterChain chain, HttpServletRequest request, ServletResponse response, String switchUserHeader) throws IOException, ServletException {
        final Authentication targetUser = attemptSwitchUser(new SwitchUserRequest(request, switchUserHeader));
        SecurityContextHolder.getContext().setAuthentication(targetUser);

        try {
            chain.doFilter(request, response);
        } finally {
            final Authentication originalUser = attemptExitUser(request);
            SecurityContextHolder.getContext().setAuthentication(originalUser);
        }

    }

}
```

The only difference from original `SwitchUserFilter` is that if `"X-Switch-User-Once"` is present, we switch credentials to user denoted by the value of this header - however only for the duration of one HTTP request.
`SwitchUserFilter` assumes user name to switch to is under `j_username` parameter so I had to cheat a bit with `SwitchUserRequest` wrapper:

```java
private class SwitchUserRequest extends HttpServletRequestWrapper {

    private final String switchUserHeader;

    public SwitchUserRequest(HttpServletRequest request, String switchUserHeader) {
        super(request);
        this.switchUserHeader = switchUserHeader;
    }

    @Override
    public String getParameter(String name) {
        switch (name) {
            case SPRING_SECURITY_SWITCH_USERNAME_KEY:
                return switchUserHeader;
            default:
                return super.getParameter(name);
        }
    }
}
```

And our custom “`sudo`” is in place!
You can test it e.g. using `curl`:

```text
$ curl localhost:8080/books/rest/book \
    -H "X-Switch-User-Once: bob" \
    -b "JSESSIONID=..."
```

Of course without `JSESSIONID` cookie the system would not let us in.
We have to be logged in first and have special privileges to access `sudo` functionality.

Switching user is a handy and quite powerful tool.
If you want to try it in practice, check out [working example on GitHub](https://github.com/nurkiewicz/books).
