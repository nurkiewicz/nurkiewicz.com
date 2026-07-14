---
layout: post
title: 'Hades: DRY principle in JPA/Spring development'
date: '2010-07-06T23:11:00.006+02:00'
author: Tomasz Nurkiewicz
tags:
- jpa
- spring
- hades
modified_time: '2010-07-06T23:42:10.834+02:00'
thumbnail: /assets/img/hades-dry-principle-in-jpaspring/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4222227573134757128
blogger_orig_url: https://www.nurkiewicz.com/2010/07/hades-dry-principle-in-jpaspring.html
---

It's almost two weeks after great [Javarsovia 2010](http://javarsovia.pl) conference, but before I write few words about this event, let me mention about really clever library called [Hades](http://redmine.synyx.org/projects/hades).
I owe you this after my attendance in [GeeCON 2010](http://nurkiewicz.com/2010/05/impressions-after-geecon-2010.html), where I discovered this tool during its author talk.

DRY stands for [Don't Repeat Yourself](http://en.wikipedia.org/wiki/Don%27t_repeat_yourself) and if you were developing in JPA for a while you have violated this principal several times.
Take for example this piece of code:

[![](/assets/img/hades-dry-principle-in-jpaspring/1.png)](/assets/img/hades-dry-principle-in-jpaspring/1.png)

Although IntelliJ IDEA has a wonderful [support for JPA](http://www.jetbrains.com/idea/features/jpa_hibernate.html) (have you noticed this little popup suggesting me the proper named query parameter name since?), I still have to write the same boilerplate code over and over.
Basically for each entity object I need a DAO class and 90% of them look the same except they have different entity type.
Same CRUD, same paging and sorting logic, same unit tests, similar queries.
We are getting bored after writing fifth or tenth DAO like this, especially if we are lazy (which is good!)
So Hades provides nice abstraction, at least all your DAOs would follow same naming convention:

```java
public interface GenericDao<T, PK extends Serializable> {
    T save(final T entity);
    List<T> save(final List<T> entities);
    T saveAndFlush(final T entity);
    T readByPrimaryKey(final PK primaryKey);
    boolean exists(final PK primaryKey);
    List<T> readAll();
    List<T> readAll(final Sort sort);
    Page<T> readAll(final Pageable pageable);
    Long count();
    void delete(final T entity);
    void delete(final List<T> entities);
    void deleteAll();
    void flush();
}
```

Nice, but you probably came out with similar generic interface long time ago.
But Hades goes one step further and it automatically implements this interface for you… For any entity bean you provide!

```java
public interface MoneyTransferDao extends GenericDao<MoneyTransfer, Long> {}
```

But let's start from the beginning.
First get necessary dependencies:

```xml
<!-- Spring -->
<dependency>
    <groupId>org.springframework</groupId>
    <artifactId>spring-orm</artifactId>
    <version>3.0.3.RELEASE</version>
</dependency>
<dependency>
    <groupId>org.springframework</groupId>
    <artifactId>spring-test</artifactId>
    <version>3.0.3.RELEASE</version>
    <scope>test</scope>
</dependency>

<!-- Persistence -->
<dependency>
    <groupId>com.h2database</groupId>
    <artifactId>h2</artifactId>
    <version>1.1.119</version>
    <scope>runtime</scope>
</dependency>
<dependency>
    <groupId>commons-dbcp</groupId>
    <artifactId>commons-dbcp</artifactId>
    <version>1.4</version>
    <scope>runtime</scope>
</dependency>
<dependency>
    <groupId>org.hibernate.java-persistence</groupId>
    <artifactId>jpa-api</artifactId>
    <version>2.0-cr-1</version>
</dependency>
<dependency>
    <groupId>org.hibernate</groupId>
    <artifactId>hibernate-entitymanager</artifactId>
    <version>3.5.1-Final</version>
</dependency>
<dependency>
    <groupId>org.synyx.hades</groupId>
    <artifactId>org.synyx.hades</artifactId>
    <version>2.0.0.RC2</version>
    <exclusions>
        <exclusion>
            <groupId>org.springframework</groupId>
            <artifactId>org.springframework.orm</artifactId>
        </exclusion>
    </exclusions>
</dependency>

<!-- ... -->

<repository>
    <id>repo.synyx.de</id>
    <name>Synyx Maven2 Repository</name>
    <url>http://repo.synyx.org</url>
</repository>
```

All other dependencies necessary to run Spring-managed integration test with JPA 2.0 backed by Hibernate 3.5 will be downloaded transitively.
You also need logging dependencies, take a look [here](http://nurkiewicz.com/2010/05/clean-code-clean-logs-use-appropriate.html).

As an example we are going to use these two entities:

```java
public class MoneyTransfer implements Serializable {
    private long id;
    private Account from;
    private Account to;
    private BigDecimal amount;
    private Calendar date;

    //get/set

}
```

```java
public class Account implements Serializable {
    private int id;
    private String ownerName;

    //get/set

}
```

Personally, I find JPA annotations great for rapid prototyping, but awful in production code, especially when fine-tuning your mapping (database sequence names in Java annotations attributes?!?)
So here is my orm.xml excerpt:

```xml
<entity class="com.blogspot.nurkiewicz.hades.MoneyTransfer">
    <attributes>
        <id name="id">
            <generated-value/>
        </id>
        <basic name="date" optional="false">
            <temporal>DATE</temporal>
        </basic>
        <basic name="amount" optional="false">
            <column precision="20" scale="2"/>
        </basic>
        <many-to-one name="from" optional="false">
            <cascade>
                <cascade-all/>
            </cascade>
        </many-to-one>
        <many-to-one name="to" optional="false">
            <cascade>
                <cascade-all/>
            </cascade>
        </many-to-one>
    </attributes>
</entity>

<entity class="com.blogspot.nurkiewicz.hades.Account">
    <attributes>
        <id name="id">
            <generated-value/>
        </id>
        <basic name="ownerName" optional="false">
            <column length="120"/>
        </basic>
    </attributes>
</entity>
```

We all love XML, admit it!
And finally unit test itself:

```java
@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration
@Transactional
public class MoneyTransferDaoTest {

    @PersistenceContext
    private EntityManager em;

    @Resource
    private MoneyTransferDao dao;

    @Resource
    private AccountDao accountDao;

    @Test
    public void shouldReturnNothingWhenReadingNotExistingMoneyTransfer() throws Exception {
        //when
        final MoneyTransfer moneyTransfer = dao.readByPrimaryKey(17L);

        //then
        assertThat(moneyTransfer).isNull();
    }

    @Test
    public void shouldReturnExistingMoneyTransfer() throws Exception {
        //given
        final MoneyTransfer newTransfer = new MoneyTransfer();
        em.persist(newTransfer);

        //when
        final MoneyTransfer moneyTransfer = dao.readByPrimaryKey(newTransfer.getId());

        //then
        assertThat(moneyTransfer).isNotNull();
        assertThat(moneyTransfer.getId()).isEqualTo(newTransfer.getId());
    }

//...

}
```

Following Spring unit test naming convention, this test case will start Spring context located in MoneyTransferDaoTest-context.xml:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xmlns:context="http://www.springframework.org/schema/context"
       xmlns:tx="http://www.springframework.org/schema/tx" xmlns:hades="http://schemas.synyx.org/hades"
       xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd
            http://www.springframework.org/schema/context http://www.springframework.org/schema/context/spring-context.xsd
            http://www.springframework.org/schema/tx http://www.springframework.org/schema/tx/spring-tx-2.5.xsd http://schemas.synyx.org/hades http://schemas.synyx.org/hades/hades.xsd">

    <tx:annotation-driven transaction-manager="transactionManager"/>
    <context:annotation-config/>

    <bean class="org.springframework.orm.jpa.support.PersistenceAnnotationBeanPostProcessor"/>
    <bean class="org.springframework.dao.annotation.PersistenceExceptionTranslationPostProcessor"/>

    <bean id="dataSource" class="org.apache.commons.dbcp.BasicDataSource">
        <property name="driverClassName" value="org.h2.Driver"/>
        <property name="url" value="jdbc:h2:mem:moneytransfers;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE"/>
    </bean>

    <bean id="transactionManager" class="org.springframework.orm.jpa.JpaTransactionManager">
        <property name="entityManagerFactory" ref="entityManagerFactory"/>
    </bean>

    <bean id="entityManagerFactory" class="org.springframework.orm.jpa.LocalContainerEntityManagerFactoryBean">
        <property name="dataSource" ref="dataSource"/>
        <property name="jpaVendorAdapter" ref="jpaAdapter"/>
        <property name="jpaProperties">
            <props>
                <prop key="hibernate.format_sql">true</prop>
                <prop key="hibernate.ejb.naming_strategy">org.hibernate.cfg.DefaultComponentSafeNamingStrategy</prop>
                <prop key="hibernate.hbm2ddl.auto">update</prop>
            </props>
        </property>
    </bean>

    <bean id="jpaAdapter" class="org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter"/>

    <hades:dao-config base-package="com.blogspot.nurkiewicz.hades"/>

</beans>
```

Now run the test, it should pass.
That's right, we haven't written even single line of DAO code and still our MoneyTransferDao, injected in line 10, works perfectly!
The whole magic is hidden under line 39 of Spring context file.
hades:dao-config element discovers all interfaces extending org.synyx.hades.dao.GenericDao\<T, PK extends Serializable\> and dynamically implements them based on their generic types.
We automatically get methods like:

```java
public interface MoneyTransferDao extends GenericDao<MoneyTransfer, Long> {
    MoneyTransfer readByPrimaryKey(final Long primaryKey);
    Page<MoneyTransfer> readAll(final Pageable pageable);
 //...
}
```

Yep, Hades also provides built in support for paging and sorting – especially annoying when has to be implemented and tested manually for several entities.

OK, to be honest, there was no magic in what we have seen until now and you might have even written similar utilities for your internal usage.
Although GenericDao has some built in methods that cover, let's say, 50% of typical queries, what about the rest?
What if I would like to find all money transfers with amount greater than given value?

```java
public interface MoneyTransferDao extends GenericDao<MoneyTransfer, Long> {
    List<MoneyTransfer> findByAmountGreaterThan(BigDecimal amount);
}
```

Where to put the implementation of this custom DAO method?
Well, now the magic part begins – nowhere!
Similar to GORM, Hades will parse this method name and create the query for you.
All you have to do is to follow some naming convention.
No custom queries, no boilerplate code.
Hades will even set the parameter for you.
It's such a clever tool, that simply by adding argument of type Pageable Hades will include paging clauses (like TOP, LIMIT, OFFSET, etc.):

```java
public interface MoneyTransferDao extends GenericDao<MoneyTransfer, Long> {
    List<MoneyTransfer> findByDateGreaterThan(Calendar date, Pageable page);
 //...
}
```

```java
moneyTransferDao.findByDateGreaterThan(
        Calendar.getInstance(),
        new PageRequest(1, 20, new Sort(Order.ASCENDING, "amount")));
```

So, Hades can transparently implement basic CRUD operations with sorting/paging support.
It can also synthesize queries based only on interface method name and arguments.
But once you discover that this feature is very limited (for instance it does not support Not, Like, IsNull, In and other modifiers known from [GORM](http://www.grails.org/GORM), see issue [\#274](http://redmine.synyx.org/issues/274)), you'll eventually end up with a need for a custom JPA query like this:

```xml
<named-query name="MoneyTransfer.getAverageTransferAmountSince">
    <query>
        SELECT AVG(transfer.amount)
        FROM MoneyTransfer transfer
        WHERE transfer.date > ?1
    </query>
</named-query>
```

Now we add method in our DAO interface that will execute this query:

```java
public interface MoneyTransferDao extends GenericDao<MoneyTransfer, Long> {
    BigDecimal getAverageTransferAmountSince(Calendar since);
 //...
}
```

The implementation is trivial (see screenshot at the beginning of this article), so Hades implements this method for us as well.
Name of the method matches name of the named query (prefixed by the entity name), which is enough for Hades.
Few lines of code (repeated hundreds of times) are saved.

But what if you really want to implement custom DAO method, but still having all other methods implemented for you?
There are two reasons: do some validation and parameters transformation before the query is executed and post-process results after query execution.
The latter reason can be often eliminated using not very well known JPA query language feature.
Take for instance this query:

```text
SELECT transfer.amount, transfer.from.id, transfer.to.id
FROM MoneyTransfer transfer
```

It will return List\<Object\[\]\>, which isn't very object-orientish.
Instead, our DAO layer should do some transformation and return more user friendly object.
JPA can do this for you with this simple expression:

```text
SELECT NEW RawMoneyTransfer(transfer.amount, transfer.from.id, transfer.to.id)
FROM MoneyTransfer transfer
```

RawMoneyTransfer is any Java object (not necessarily JPA entity) with constructor matching given parameters being only requirement.
But once again, what if you really need custom DAO method?
For example JPA does not define any date expressions, so there is no straightforward way to define "30 days before today" when generating report for last month in JPA QL.
Unfortunately, Hades way of defining custom DAO methods is troublesome and a bit counterintuitive.
I will open an issue and try to introduce simpler (although harder in implementation) solution.
Meanwhile take a look at great Hades reference [documentation](http://redmine.synyx.org/projects/hades/wiki) for further details.

Hades also has support for entity auditing, but [Envers](http://www.jboss.org/envers), being part of Hibernate portfolio, is probably more mature solution.
As of version 2.0 it also has built in support to participate in Spring transactions.
As you have seen, Hades aims to increase your productivity by writing less code, less unit tests (comprehensive unit testing of Hades-generated methods isn't necessary) and promoting convention over configuration approach.
It still has some limitations but give it a try, I recently will.
