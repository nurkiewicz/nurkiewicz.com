---
layout: post
title: Property-based testing with ScalaCheck - custom generators
date: '2014-09-19T11:33:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- testing
- ScalaCheck
- scala
modified_time: '2014-09-19T11:33:02.494+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2199646930772740089
blogger_orig_url: https://www.nurkiewicz.com/2014/09/property-based-testing-with-scalacheck.html
---

In the [previous article](http://www.nurkiewicz.com/2014/09/property-based-testing-with-spock.html) we examined how [Spock](http://code.google.com/p/spock/) can be used to implement property-based testing.
One of the "*hello, world*" examples of property-based testing is making sure absolute value of arbitrary integer is always non-negative.
We did that one as well.
However our test didn't discover very important edge case.
See for yourself, this time with [ScalaCheck](http://scalacheck.org/) and [ScalaTest](http://www.scalatest.org/):

```scala
import org.scalatest.FunSuite
import org.scalatest.prop.Checkers

class AbsSuite extends FunSuite with Checkers {

    test("absolute value should not be negative") {
        check((somInt: Int) => {
            somInt.abs >= 0
        })
    }
}
```

...or with a different syntax:

```scala
import org.scalatest.FunSuite
import org.scalatest.matchers.ShouldMatchers
import org.scalatest.prop.{GeneratorDrivenPropertyChecks, Checkers}

class AbsSuite extends FunSuite with GeneratorDrivenPropertyChecks with ShouldMatchers{

    test("absolute value should not be negative") {
        forAll((someInt: Int) => {
            someInt.abs should be >= 0
        })
    }
}
```

The results are surprising:

```scala
GeneratorDrivenPropertyCheckFailedException was thrown during property evaluation.
 (AbsSuite.scala:7)
  Falsified after 8 successful property evaluations.
  Location: (AbsSuite.scala:7)
  Occurred when passed generated values (
    arg0 = -2147483648
  )
```

ScalaCheck tells us that our property is not met for input = `-2147483648`.
What's so special about this number?
`int`s aren't symmetric, `Integer.MIN_VALUE` = `-2147483648` while `Integer.MAX_VALUE` = `2147483647`.
It's not possible to represent `2147483648` in `Int`:

```scala
scala> (-2147483647).abs
res0: Int = 2147483647

scala> (-2147483648).abs
res0: Int = -2147483648
```

------------------------------------------------------------------------

You got a taste of ScalaCheck combined with ScalaTest.
ScalaCheck is much more advanced compared to our Groovy solution because it supports:

- parallelism - running examples in multiple threads
- custom data generators - type safe and composable, resolved at compile time
- shrinking - finding smallest input that exhibits erroneous behaviour
- predictability - can re-run tests with the same examples later in case of rarely occurring bugs

To test drive ScalaCheck we will work on a simple bank abstraction:

```scala
case class AccountNo(num: BigInt) extends AnyVal

case class Account(accNo: AccountNo, balance: BigDecimal) {
    def withBalancePlus(amount: BigDecimal): Account =
        this.copy(balance = this.balance + amount)

    def withBalanceMinus(amount: BigDecimal) = withBalancePlus(-amount)

}

class Bank(accounts: Map[AccountNo, Account]) {

    def this(newAccounts: TraversableOnce[Account]) {
        this(newAccounts.map(acc => (acc.accNo, acc)).toMap)
    }

    def transfer(from: AccountNo, to: AccountNo, amount: BigDecimal): Bank = {
        val modifiedFrom = accounts(from).withBalanceMinus(amount)
        val modifiedTo = accounts(to).withBalancePlus(amount)
        val newAccounts = accounts
            .updated(from, modifiedFrom)
            .updated(to, modifiedTo)
        new Bank(newAccounts)
    }

    def totalMoney = accounts.values.map(_.balance).sum

}
```

To stay with the spirit of functional programming, our `Bank` implementation is immutable (`accounts` is of `scala.collection.immutable.Map` type), as well as `Account` and `AccountNo`.
Every time we call `Bank.transfer()`, new instance of `Bank` is created, almost exactly the same, but with `from` and `to` accounts modified.
This greatly simplifies coding in multi-threaded environment.
Code is quite simple: take `amount` of money from one account and put it on another.
Assume we have few example based tests and we are confident this code works.
But to be extra safe we are going to build property based test.
What is the property that will be satisfied, no matter how many transfers we perform?
The most important one is that the total money in the bank should remain the same, no matter how many intra-bank transfers are executed.
After all, we don't want money to disappear or appear from nowhere.

Our test should prove that *any* bank, with *any* number of *arbitrary* transfers has the same total amount of money before and after executing transfers.
We start with simple:

```scala
class BankSuite extends FunSuite with Checkers {

    test("Total money should not change after arbitrary number of intra-bank transfers") {
        check((bank: Bank, transfers: List[Transfer]) => {
            val bankAfterTransfers = transfers.foldLeft(bank) { (curBank, transfer) =>
                curBank.transfer(transfer.from, transfer.to, transfer.amount)
            }
            bank.totalMoney == bankAfterTransfers.totalMoney
        })
    }
}

case class Transfer(from: AccountNo, to: AccountNo, amount: BigDecimal) 
```

What we are saying is: for any `bank` and any `List` of `transfers`, `totalMoney` before and after should remain the same.
We must `foldLeft()` because `Bank` is immutable and every transfer must be applied on a `Bank` instance returned from a previous one.
ScalaCheck can generate random `Int`s (as we saw in `AbsSuite`) and other primitives, strings, etc. - and collections of these.
But ScalaCheck has no idea how to create random `Bank` or `Transfer`:

```scala
Error:(34, 8) could not find implicit value for parameter a1: org.scalacheck.Arbitrary[com.nurkiewicz.banking.Bank]
        check((bank: Bank, transfers: List[Transfer]) => {
             ^
```

What the compiler is telling us is that it can't find a type class [`org.scalacheck.Arbitrary[T]`](http://www.scalacheck.org/files/scalacheck_2.11-1.11.5-api/#org.scalacheck.Arbitrary) type-parameterized with `Bank`.
There are instances of this type class for primitives or collections, but obviously not for our `Bank`.
There are actually two abstractions we need to provide: `Gen` implementation and `Arbitrary` type class wrapping it.
Let's go through it step by step.
`accountNoGen` generates random `AccountNo` with values ranging from `100000` and `999999`.
`Gen` is like a stateless stream of data, it produces possibly infinite number of random values.
You might wonder, why not just use `Math.rand()`?
We can, but this way ScalaCheck can instrument all generated random data and e.g. allow replying it later, when the same random seed is used.

```scala
val accountNoGen: Gen[AccountNo] =
    Gen.choose(100000, 999999).map(n => AccountNo(BigInt(n)))
```

`moneyGen` generates arbitrary positive amount of money (up to cent precision).
Having these we can compose `accountGen` by taking arbitrary account number and balance:

```scala
val moneyGen = for {
    value <- Gen.chooseNum(0, 100000000)
    valueDecimal = BigDecimal.valueOf(value)
} yield valueDecimal / 100

val accountGen: Gen[Account] = for {
    accNo <- accountNoGen
    balance <- moneyGen
} yield Account(accNo, balance)
```

We are now ready to generate random `Bank`.
It takes an arbitrary number (`Gen.containerOf[List, Account]`) of arbitrary accounts (`accountGen`), but we don't want to generate empty banks or banks with too many accounts:

```scala
implicit val arbitraryBank = Arbitrary(
    for {
        accounts <- Gen.containerOf[List, Account](accountGen)
        if !accounts.isEmpty
        if accounts.size < 10000
    } yield new Bank(accounts)
)
```

The last piece is a random `Transfer`.
This part is actually more complex.
In order to generate arbitrary transfer we need two random accounts from a bank.
But we don't know accounts yet, since bank with accounts was generated randomly.
Thus our generator must be parameterized with a bank that was earlier randomized.
The difference between `accountNoGen` and `accountNoInBankGen` is that the latter picks an existing account number from a given bank, rather than an arbitrary, random number.
In `arbitraryTransfer` we don't have to pass `bank` explicitly because it is marked as `implicit`:

```scala
def accountNoInBankGen(implicit bank: Bank): Gen[AccountNo] = {
    val accNums = bank.accountNumbers.toSeq
    for {
        accNum <- Gen.chooseNum(0, accNums.size - 1)
    } yield accNums(accNum)
}

implicit def arbitraryTransfer(implicit bank: Bank) = Arbitrary {
    for {
        fromAcc <- accountNoInBankGen
        toAcc <- accountNoInBankGen
        amount <- moneyGen
    } yield Transfer(fromAcc, toAcc, amount)
}
```

Unfortunately `check((bank: Bank, transfers: List[Transfer])` won't work.
`Bank` and `List[Transfer]` are generated "at the same time", so there is no way to pass generated `bank` to `transfers` generator.
We have to go deeper, using different ScalaCheck syntax (`forAll`), abusing it slightly:

```scala
test("Total money should not change after arbitrary number of intra-bank transfers") {
    forAll((bank: Bank) => {
        implicit val anyBank = bank
        forAll((transfers: List[Transfer]) => {
            val bankAfterTransfers = transfers.foldLeft(bank) { (curBank, transfer) =>
                curBank.transfer(transfer.from, transfer.to, transfer.amount)
            }
            bank.totalMoney should equal (bankAfterTransfers.totalMoney)
        })
    })
}
```

In outer `forAll()` clause we generate arbitrary `Bank`.
We have to make it `implicit` and then in inner `forAll` we ask for random `transfers`.
This was a lot of work!
But hey, we found a bug, did you spot it?

```scala
GeneratorDrivenPropertyCheckFailedException was thrown during property evaluation.
  Message: TestFailedException was thrown during property evaluation.
  Message: 467626.69 did not equal 1352118.86
  Location: (BankChecks.scala:53)
  Occurred when passed generated values (
    arg0 = List(Transfer(AccountNo(664482),AccountNo(664482),884492.17)) // 1 shrink
  )
  Location: (GeneratorDrivenPropertyChecks.scala:837)
  Occurred when passed generated values (
    arg0 = Bank[Account(AccountNo(664482),467626.69)]
  )
```

Money doesn't add up!
Looking carefully we see that the test failed with just one account and one transfer.
By repeating the test we can easily find the pattern: single transfer with the same source and target account (`664482` this time)!
Scroll back to our implementation and try to figure out why (remember about immutability):

```scala
def transfer(from: AccountNo, to: AccountNo, amount: BigDecimal): Bank = {
    val modifiedFrom = accounts(from).withBalanceMinus(amount)
    val modifiedTo = accounts(to).withBalancePlus(amount)
    val newAccounts = accounts
        .updated(from, modifiedFrom)
        .updated(to, modifiedTo)
    new Bank(newAccounts)
}
```

If `from == to`, changes to `modifiedFrom` are overwritten by changes in `modifiedTo`.
Amazingly, if `Account` was mutable, this bug would not occur (!)
Let's first go from red to green:

```scala
def transfer(from: AccountNo, to: AccountNo, amount: BigDecimal): Bank = {
    val modifiedFrom = accounts(from).withBalanceMinus(amount)
    val accountsMinusAmount = accounts.updated(from, modifiedFrom)
    val modifiedTo = accountsMinusAmount(to).withBalancePlus(amount)
    val accountsPlusAmount = accountsMinusAmount.updated(to, modifiedTo)
    new Bank(accountsPlusAmount)
}
```

Be sure you understand why the two code snippets are fundamentally different.
Hint: compare `accounts(to)` and `accountsMinusAmount(to)`.
OK, it works, but I see way too many identifiers and noise, let's go more functional:

```scala
def transfer(from: AccountNo, to: AccountNo, amount: BigDecimal): Bank = {
    this.
        update(from)(_.withBalanceMinus(amount)).
        update(to)  (_.withBalancePlus(amount))
}

private def update(accNo: AccountNo)(transformation: Account => Account): Bank = {
    val account = accounts(accNo)
    val modified = transformation(account)
    val updatedAccounts = accounts.updated(accNo, modified)
    new Bank(updatedAccounts)
}
```

Private `Bank.update()` modifies one account by applying a custom function on top of it.
We call this higher-order function twice, once to modify `from` account, later to modify `to` - but this second application works on top of already modified `Bank` instance.

One thing we haven't covered is shrinking (noticed `// 1 shrink` comment in test failure message?)
ScalaCheck produces random, sometimes really large input, for example very long list of random transactions.
Imagine just one transaction in hundreds causes error.
If ScalaCheck finds such a list and reports it, discovering which particular transfer caused bug can be a challenge on its own.
Thus ScalaCheck, using various heuristics, tries to shrink generated input in order to find the smallest one, still exhibiting erroneous behaviour.
In our case it's a matter of selectively removing transfers from an input list ("*shrinking*" it), until we find the smallest subset still exposing a bug.
This time-saving process is called "*shrinking*".
More importantly we can customize it, for example telling the framework how to shrink `Bank` to a smaller, still problematic instance.

------------------------------------------------------------------------

As you can see property based testing can be useful.
It doesn't replace example based testing.
Moreover, every time you find a bug using ScalaCheck, you should start with writing an example test that fails (and fails *all the time*, not *from time to time*).
Remember that property based tests are randomized so they will not always find all bugs - and even worse, sometimes they will find bugs much later.
Such tests are valuable, but they will never replace ordinary, predictable tests.
