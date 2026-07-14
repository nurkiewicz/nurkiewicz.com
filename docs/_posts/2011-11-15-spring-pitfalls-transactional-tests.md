---
layout: post
title: 'Spring pitfalls: transactional tests considered harmful'
date: '2011-11-15T22:27:00.001+01:00'
author: Tomasz Nurkiewicz
tags:
- testing
- transactions
- jpa
- scala
- hibernate
- spring
- h2
modified_time: '2011-11-17T19:31:29.910+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4456248775897338627
blogger_orig_url: https://www.nurkiewicz.com/2011/11/spring-pitfalls-transactional-tests.html
---

One of the Spring killer-features is an in-container [integration testing](http://static.springsource.org/spring/docs/current/spring-framework-reference/html/testing.html).
While EJB lacked this functionality for many years (Java EE 6 finally [addresses](http://www.adam-bien.com/roller/abien/entry/embedding_ejb_3_1_container)this, however I haven't, *ekhem*, tested it), Spring from the very beginning allowed you to test the full stack, starting from web tier, through services all the way down to the database.

Database is the problematic part.
First you need to use in-memory self-contained database like [H2](http://www.h2database.com/)to decouple your tests from an external database.
Spring helps with this to a great degree, especially now with profiles and [embedded database support](http://static.springsource.org/spring/docs/current/spring-framework-reference/html/jdbc.html#jdbc-embedded-database-support).
The second problem is more subtle.
While typical Spring application is almost completely stateless (for better or worse), database is inherently stateful.
This complicates integration testing since the very first principle of writing tests is that they should be independent on each other and repeatable.
If one test writes something to the database, another test may fail; also the same test may fail on subsequent call due to database changes.

Obviously Spring [handles this problem](http://static.springsource.org/spring/docs/current/spring-framework-reference/html/testing.html#testcontext-tx) as well with a very neat trick: prior to running every test Spring starts a new transaction.
The whole test (including its setup and tear down) runs within the same transaction which is...
rolled back at the end.
This means all the changes made during the test are visible in the database just like if they were persisted.
However rollback after every test wipes out all the changes and the next test works on a clean and fresh database.
Brilliant!

Unfortunately this is not yet another article about Spring integration testing advantages.
I think I have written hundreds if not thousands of such tests and I truly appreciate the transparent support Spring framework gives.
But I also came across numerous quirks and inconsistencies introduces by this comfortable feature.
To make matters worse, very often so-called transactional tests are actually **hiding errors**convincing the developer that the software works, while it fails after deployment!
Here is a non-exhaustive but eye-opening collection of issues:

```java

@Test
public void shouldThrowLazyInitializationExceptionWhenFetchingLazyOneToManyRelationship() throws Exception {
  //given
  final Book someBook = findAnyExistingBook();

  //when
  try {
    someBook.reviews().size();
    fail();
  } catch(LazyInitializationException e) {
    //then
  }
}
```

This is a known issue with Hibernate and spring integration testing.
Bookis a database entity with one-to-many, lazy by default, relationship to Reviews.
findAnyExistingBook() simply reads a test book from a transactional service.
Now a bit of theory: as long as an entity is bound to a session (EntityManager if using JPA), it can lazily and transparently load relationships.
In our case it means: as long as it is within a scope of a transaction.
The moment an entity leaves a transaction, it becomes detached.
At this lifecycle stage an entity is no longer attached to a session/EntityManager (which has been committed and closed already) and any approach to fetch lazy properties throws the dreadful LazyInitializationException.
This behaviour is actually standardized in JPA (except the exception class itself, which is vendor specific).

In our case we are callling .reviews() (Scala-style “getter”, we will translate our test case to ScalaTest soon as well) and expecting to see the Hibernate exception.
However the exception is not thrown and the application keeps going.
That's because the whole test is running within a transaction and the Book entity never gets out of transactional scope.
Lazy loading *always*works in Spring integration tests.

[](http://draft.blogger.com/blogger.g?blogID=6753769565491687768)To be fair, we will never see tests like this in real life (unless you are testing to make sure that a given collection is lazy – unlikely).
In real life we are testing business logic which just works in tests.
However after deploying we start experiencing LazyInitializationException.
But we tested it!
Not only Spring integration testing support **hid the problem**, but it also encourages the developer to throw in [OpenSessionInViewFilter](http://static.springsource.org/spring/docs/current/javadoc-api/org/springframework/orm/hibernate3/support/OpenSessionInViewFilter.html)or [OpenEntityManagerInViewFilter](http://static.springsource.org/spring/docs/current/javadoc-api/org/springframework/orm/jpa/support/OpenEntityManagerInViewFilter.html).
In other words: our test not only didn't discover a bug in our code, but it also significantly worsen our overall architecture and performance.
Not what I would expect.

My typical workflow these days while implementing some end-to-end feature is to write back-end tests, implement the back-end including REST API and when everything runs smoothly deploy it and proceed with the GUI.
The latter is written using AJAX/JavaScript completely so I only need to deploy once and replace cheap client-side files often.
At this stage I don't want to go back to the server to fix undiscovered bugs.

Suppressing LazyInitializationException is among the most known problems with Spring integration testing.
But this is just a tip of an iceberg.
Here is a bit more complex example (it uses JPA again, but this problems manifests itself with plain JDBC and any other persistence technology as well):

```java

@Test
public void externalThreadShouldSeeChangesMadeInMainThread() throws Exception {
  //given
  final Book someBook = findAnyExistingBook();
  someBook.setAuthor("Bruce Wayne");
  bookService.save(someBook);

  //when
  final Future<Book> future = executorService.submit(new Callable<Book>() {
    @Override
    public Book call() throws Exception {
      return bookService.findBy(someBook.id()).get();
    }
  });

  //then
  assertThat(future.get().getAuthor()).isEqualTo("Bruce Wayne");
}
```

In the first step we are loading some book from the database and modifying the author, saving an entity afterwards.
Then we load the same entity by id in another thread.
The entity is already saved so it is guaranteed that the thread should see the changes.
This is not the case however, which is proved by the failing assertion in the last step.
What happened?

We have just observed “I” in [ACID](http://en.wikipedia.org/wiki/ACID)transaction properties.
Changes made by the test thread are not visible to other threads/connections until the transaction is committed.
But we know the test transaction commits!
This small showcase demonstrates how hard it is to write multi-threaded integration tests with transactional support.
I learnt the hard way few weeks ago when I wanted to integration-test [Quartz](http://www.quartz-scheduler.org/)scheduler with [JDBCJobStore](http://www.quartz-scheduler.org/documentation/quartz-2.1.x/tutorials/tutorial-lesson-09)enabled.
No matter how hard I tried the jobs were never fired.
It turned out that I was scheduling a job in Spring-managed test within the scope of a Spring transaction.
Because the transaction was never committed, the external scheduler and worker threads couldn't see the new job record in the database.
And how many hours have you spent debugging such issues?

Talking about debugging, the same problem pop up when trouble-shooting database-related test failures.
I can add this simple H2 web console (browse to localhost:8082) bean to my test configuration:

```scala

@Bean(initMethod = "start", destroyMethod = "stop")
def h2WebServer() = Server.createWebServer("-webDaemon", "-webAllowOthers")
```

But I will never see changes made by my test while stepping through it.
I cannot run the query manually to find out why it returns wrong results.
Also I cannot modify the data on-the-fly to have a faster turn-around while trouble-shooting.
My database lives in a different dimension.

Please read the next test carefully, it's not long:

```java

@Test
public void shouldNotSaveAndLoadChangesMadeToNotManagedEntity() throws Exception {
  //given
  final Book unManagedBook = findAnyExistingBook();
  unManagedBook.setAuthor("Clark Kent");

  //when
  final Book loadedBook = bookService.findBy(unManagedBook.id()).get();

  //then
  assertThat(loadedBook.getAuthor()).isNotEqualTo("Clark Kent");
}
```

We are loading a book and modifying an author **without**explicitly persisting it.
Then we are loading it again from the database and making sure that the change was **not**persisted.
Guess what, somehow we have updated the object!

If you are experienced JPA/Hibernate user you know exactly how could that happen.
Remember when I was describing attached/detached entities above?
When an entity is still attached to the underlying EntityManager/session it has other powers as well.
JPA provider is obligated to track the changes made to such entities and automatically propagate them to the database when entity becomes detached (so-called *dirty checking*).

This means that an idiomatic way to work with JPA entities modifications is to load an object from a database, perform necessary changes using setters and...
that's it.
When the entity becomes detached, JPA will discover it was modified and issue an UPDATE for you.
No merge()/update() needed, cute object abstraction.
This works as long as an entity is managed.
Changes made to detached entity are silently ignored because JPA provider knows nothing about such entities.
Now the best part – you almost never know if your entity is attached or not because transaction management is transparent and almost invisible.
This means that it is way too easy to only modify POJO instance in-memory while still believing that changes are persistent and vice-versa!

Can we test it?
Of course, we just did – and failed.
In our test above transaction spans across the whole test method, so every entity is managed.
Also due to Hibernate L1 cache we get the exact same book instance back, even though no database update has been yet issued.
This is another case where transactional tests are hiding problems rather than revealing them (see LazyInitializationExceptionexample).
Changes are propagated to the database as expected in the test, but silently ignored after deployment...

BTW did I mention that all tests so far are passing once you get rid of @Transactional annotation over test case class?
Have a look, sources as always are [available](https://github.com/nurkiewicz/spring-pitfalls/tree/transactional-tests).

[](http://draft.blogger.com/blogger.g?blogID=6753769565491687768)This one is exciting.
I have a transactional deleteAndThrow(book) business method that deletes given book and throws OppsException.
Here is my test that passes, proving the code is correct:

```java

@Test
public void shouldDeleteEntityAndThrowAnException() throws Exception {
  //given
  final Book someBook = findAnyExistingBook();

  try {
    //when
    bookService.deleteAndThrow(someBook);
    fail();
  } catch (OppsException e) {
    //then
    final Option<Book> deletedBook = bookService.findBy(someBook.id());
    assertThat(deletedBook.isEmpty()).isTrue();
  }

}
```

[](http://draft.blogger.com/blogger.g?blogID=6753769565491687768)The Scala's [Option\<Book\>](http://www.scala-lang.org/api/current/scala/Option.html)is returned (have you noticed how nicely Java code interacts with services and and entities written in Scala?)
instead of null.
deletedBook.isEmpty() yielding true means that no result was found.
So it seems like our code is correct: the entity was deleted and the exception thrown.
Yes, you are correct, it fails silently after deployment again!
This time Hibernate L1 cache knows that this particular instance of book was deleted so it returns null even before flushing changes to the database.
However OppsException thrown from the services rolls back the transaction, discarding DELETE!
But the test passes, only because Spring manages this tiny extra transaction and the assertion happens within that transaction.
Milliseconds later transaction rolls back, resurrecting deleted entity.

Obviously the solution was to add noRollbackFor attribute for OppsException(this is an actual bug I found in my code after dropping transactional tests in favour to other solution which is yet to be explained).
But this is not the point.
The point is – **can you really afford to write and maintain tests that are generating false-positives, convincing you that your application is working whereas it's not?**

Oh, and did I mention that transacational tests are actually leaking here and there and won't prevent you from modifying the test database?
The second test fails, can you see why?

```java

@Test
public void shouldStoreReviewInSecondThread() throws Exception {
  final Book someBook = findAnyExistingBook();

  executorService.submit(new Callable<Review>() {
    @Override
    public Review call() throws Exception {
      return reviewDao.save(new Review("Unicorn", "Excellent!!!1!", someBook));
    }
  }).get();
}

@Test
public void shouldNotSeeReviewStoredInPreviousTest() throws Exception {
  //given

  //when
  final Iterable<Review> reviews = reviewDao.findAll();

  //then
  assertThat(reviews).isEmpty();
}
```

Once again threading gets into the way.
It gets even more interesting when you try to clean up after external transaction in background thread that obviously was committed.
The natural place would be to delete created Review in @After method.
But @After is executed within the same test transaction, so the clean up will be...
rolled back.

Of course I am not here to complain and grumble about my favourite application stack weaknesses.
I am here to give solutions and hints.
Our goal is to get rid of transactional tests altogether and only depend on application transactions.
This will help us to avoid all the aforementioned problems.
Obviously we cannot drop test independence and repeatability features.
Each test has to work on the same database to be reliable.
First, we will translate JUnit test to ScalaTest.
In order to have Spring dependency-injection support we need this tiny trait:

```scala

trait SpringRule extends Suite with BeforeAndAfterAll { this: AbstractSuite =>

  override protected def beforeAll() {
    new TestContextManager(this.getClass).prepareTestInstance(this)
    super.beforeAll();
  }

}
```

Now it's about time to reveal my idea (if you are impatient, full [source code is here](https://github.com/nurkiewicz/spring-pitfalls/tree/non-transactional-tests)).
It's far from being ingenious or unique, but I think it deserves some attention.
Instead of running everything in one huge transaction and rolling it back, just let the tested code to start and commit transactions wherever and whenever it needs and has configured.
This means that the data **is**actually written to the database and persistence works exactly the same as it would after the deployment.
Where's the catch?
We must somehow clean up the mess after each test...

Turns out it's not that complicated.
Just take a dump of a clean database and import it after each test!
The dump contains all the tables, constraints and records present right after the deployment and application start-up but before the first test run.
It's like taking a backup and restoring from it!
Look how simple it is with H2:

```scala

trait DbResetRule extends Suite with BeforeAndAfterEach with BeforeAndAfterAll { this: SpringRule =>

  @Resource val dataSource: DataSource = null

  val dbScriptFile = File.createTempFile(classOf[DbResetRule].getSimpleName + "-", ".sql")

  override protected def beforeAll() {
    new JdbcTemplate(dataSource).execute("SCRIPT NOPASSWORDS DROP TO '" + dbScriptFile.getPath + "'")
    dbScriptFile.deleteOnExit()
    super.beforeAll()
  }

  override protected def afterEach() {
    super.afterEach()
    new JdbcTemplate(dataSource).execute("RUNSCRIPT FROM '" + dbScriptFile.getPath + "'")

  }

}

trait DbResetSpringRule extends DbResetRule with SpringRule
```

The SQL dump (see H2 [SCRIPT](http://www.h2database.com/html/grammar.html#script)command) is taken once and exported to temporary file.
Then the SQL script file is executed after each test.
Believe it or not, that's it!
Our test is no longer transactional (so all Hibernate and multi-threading corner-cases are discovered and tested) while we didn't sacrifice the ease of transactional-tests setup (no extra clean up needed).
Also I can finally look at the database contents while debugging!
Here is one of the previous tests in action:

```scala

@RunWith(classOf[JUnitRunner])
@ContextConfiguration(classes = Array[Class[_]](classOf[SpringConfiguration]))
class BookServiceTest extends FunSuite with ShouldMatchers with BeforeAndAfterAll with DbResetSpringRule {

  @Resource
  val bookService: BookService = null

  private def findAnyExistingBook() = bookService.listBooks(new PageRequest(0, 1)).getContent.head

  test("should delete entity and throw an exception") {
    val someBook = findAnyExistingBook()

    intercept[OppsException] {
      bookService.deleteAndThrow(someBook)
    }

    bookService findBy someBook.id should be (None)
  }
}
```

Keep in mind that this is not a library/utility, but an idea.
For your project you might choose slightly different approach and tools, but the general idea still applies: let your code run in the exact same environment as after deployment and clean up the mess from backup afterwards.
You can achieve the exact same results with JUnit, [HSQLDB](http://hsqldb.org/) or whatever you prefer.
Of course you can add some clever optimizations as well – mark or discover tests that are not modifying the database, choose faster dump, import approaches, etc.

To be honest, there are some downsides as well, here are a few from top of my head:

- *Performance*.
  While it is not obvious that this approach is significantly slower than rolling back transactions all the time (some databases are particularly slow at rollbacks), it is safe to assume so.
  Of course in-memory databases might have some unexpected performance characteristics, but be prepared for a slowdown.
  However I haven't observed huge difference (maybe around 10%) per 100 tests in a small project.
- *Concurrency*.
  You can no longer run tests concurrently.
  Changes made by one thread (test) are visible by others, making test execution unpredictable.
  This becomes even more painful with regards to aforementioned performance problems.

That would be it.
If you are interested give this approach a chance.
It may take some time to adopt your existing test base, but discovering even one hidden bug is worth it, don't you think?
And also be aware of other [spring pitfalls](http://nurkiewicz.com/2011/10/spring-pitfalls-proxying.html).
