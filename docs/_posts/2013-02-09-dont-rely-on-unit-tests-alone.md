---
layout: post
title: Don't rely on unit tests alone
date: '2013-02-09T23:40:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- testing
- mockito
- tdd
- junit
modified_time: '2013-02-17T16:31:41.022+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1240043741638782311
blogger_orig_url: https://www.nurkiewicz.com/2013/02/dont-rely-on-unit-tests-alone.html
image:
  path: /assets/img/dont-rely-on-unit-tests-alone/hero.jpg
  alt: "Rådhusbrygga"
---

When you are building a complex system, barely testing components in isolation is not enough.
It's crucial, but not enough.
Imagine a car factory that manufactures and imports highest quality parts, but after assembling the vehicle never starts the engine.
If your test case suite consists barely of unit tests, you can never be sure that the system as a whole works.
Let's give a contrived example:

```java
public class UserDao {

    public List<User> findRecentUsers() {
        try {
            return //run some query
        } catch(EmptyResultDataAccessException ignored) {
            return null;
        }
    }

    //...
}
```

I hope you already spotted an anti-pattern in the `catch` block (and I don't mean ignoring the exception, it seems to be expected).
Being a good citizen we decide to fix the implementation by [returning an empty collection instead of `null`](http://www.javapractices.com/topic/TopicAction.do?Id=59):

```java
public class UserDao {

    public List<User> findRecentUsers() {
        try {
            return //run some query
        } catch(EmptyResultDataAccessException ignored) {
            return Collections.emptyList();
        }
    }

    //...
}
```

The fix is so simple that we almost forget about running unit tests, but just in case we execute them and find the first test case to fail:

```java
public class UserDaoTest {

    private UserDao userDao;

    @Before
    public void setUp() throws Exception {
        userDao = new UserDao();
    }

    @Test
    public void shouldReturnNullWhenNoRecentUsers() throws Exception {
        //given

        //when
        final List<User> result = userDao.findRecentUsers();

        //then
        assertThat(result).isNull();
    }

    @Test
    public void shouldReturnOneRecentUser() throws Exception {
        //given
        final User lastUser = new User();
        userDao.storeLoginEvent(lastUser);

        //when
        final List<User> result = userDao.findRecentUsers();

        //then
        assertThat(result).containsExactly(lastUser);
    }

    @Test
    public void shouldReturnTwoRecentUsers() throws Exception {
        //given
        final User lastUser = new User();
        final User oneButLastUser = new User();
        userDao.storeLoginEvent(oneButLastUser);
        userDao.storeLoginEvent(lastUser);

        //when
        final List<User> result = userDao.findRecentUsers();

        //then
        assertThat(result).containsExactly(lastUser, oneButLastUser);
    }

}
```

Apparently not only the code was broken (by returning `null` instead of `null`-like empty collection), but there was a test verifying this bogus behaviour.
I'm pretty sure the test was written after the implementation and it had to somehow deal with reality.
No one would ever write a test like that without prior knowledge of the implementation peculiarities.
So we fix the test and cheerfully wait for green CI build - which eventually comes.

Days later our application breaks with `NullPointerException` on production.
It breaks in a place that is unit-tested thoroughly:

```java
public class StatService {

    private final UserDao userDao;

    public StatService(UserDao userDao) {
        this.userDao = userDao;
    }

    public void welcomeMostRecentUser() {
        final List<User> recentUsers = userDao.findRecentUsers();
        if (recentUsers != null) {
            welcome(recentUsers.get(0));
        }
    }

    private void welcome(User user) {
        //...
    }
}
```

We are surprised because this class is fully covered by unit tests (verification step omitted for clarity):

```java
@RunWith(MockitoJUnitRunner.class)
public class WelcomeServiceTest {

    @Mock
    private UserDao userDaoMock;
    private WelcomeService welcomeService;

    @Before
    public void setup() {
        welcomeService = new WelcomeService(userDaoMock);
    }

    @Test
    public void shouldNotSendWelcomeMessageIfNoRecentUsers() throws Exception {
        //given
        given(userDaoMock.findRecentUsers()).willReturn(null);

        //when
        welcomeService.welcomeMostRecentUser();

        //then
        //verify no message sent
    }

    @Test
    public void shouldSendWelcomeMessageToMostRecentUser() throws Exception {
        //given
        given(userDaoMock.findRecentUsers()).willReturn(asList(new User()));

        //when
        welcomeService.welcomeMostRecentUser();

        //then
        //verify user welcomed
    }

    //...

}
```

You see where the problem lies?
We changed the contract of `UserDao` class while it "looks" the same on the surface.
By fixing broken tests we assumed it still works.
However `WelcomeService` was still relying on the old behaviour of `UserDao`, which was either returning `null` or a list with at least one element.
This behaviour was recorded using mocking framework, so that we were able to unit test `WelcomeService` in separation.

In other words we failed to make sure these two components are still working with each other, we barely tested them alone.
Back to our car metaphor - all the pieces still fit together (same contract), but one of them is not behaving internally the same as before.
So, what really went wrong?
There are at least *four* problems here, and if any of them was mitigated, none of this would have ever happened.

First of all the author of `UserDao` failed to recognize that returning a `null` while an empty list seems much more intuitive.
It begs the question: is there a significant difference between `null` and empty collection?
If yes, maybe you are trying to "encode" too much information in a single return value?
If no, why make life of your API consumers harder?
Iterating over empty collection doesn't require any extra effort; iterating over collection that might be `null` needs one extra condition.

Author of `WelcomeService` failed as well by assuming `null` means an empty collection.
He should work around the ugly API rather than relying on it.
In this case he could have used [`CollectionUtils.isNotEmpty()`](http://commons.apache.org/collections/apidocs/org/apache/commons/collections/CollectionUtils.html#isNotEmpty(java.util.Collection)) and be a little bit more defensive:

```java
if (CollectionUtils.isNotEmpty(recentUsers)) {
```

For more comprehensive solution, he could also consider [decorating](http://en.wikipedia.org/wiki/Decorator_pattern) `UserDao` and replacing `null` with empty collection.
Or even using AOP to fix such APIs globally in whole application.
And BTW this applies to `String`s as well.
In 99% of the cases there is no "business" difference between `null`, empty string and a string with few white spaces.
Use [`StringUtils.isBlank()`](http://commons.apache.org/lang/api/org/apache/commons/lang3/StringUtils.html#isBlank(java.lang.CharSequence)) or similar by default, unless you really want to distinguish between them.

Finally the person "fixing" `UserDao` failed to see the big picture.
Barely fixing unit tests is not enough.
When you are changing the behaviour of a class without changing the API (this is especially important for dynamic languages), chances are you will miss places where this API was used, loosing the context.

But the biggest failure was the **lack of component/system tests**.
If we simply had a test case exercising both `WelcomeService` *and* `UserDao` running together, this bug would've been discovered.
It's not enough to have 100% code coverage.
You test every piece of the jigsaw puzzle but never look at the finished picture.
Have at least few larger, smoke tests.
Otherwise you no longer have this awesome confidence that when tests are green, code is good to go.
