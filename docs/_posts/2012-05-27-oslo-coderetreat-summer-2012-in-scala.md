---
layout: post
title: Oslo coderetreat summer 2012 - in Scala
date: '2012-05-27T23:58:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- testing
- scala
- coderetreat
- tdd
modified_time: '2012-05-28T15:10:10.614+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-7083859418549730440
blogger_orig_url: https://www.nurkiewicz.com/2012/05/oslo-coderetreat-summer-2012-in-scala.html
---

Few days ago I had a pleasure to attend [Coderetreat summer 2012](http://www.meetup.com/OsloCodingDojo/events/63387912/) in Oslo, carried out by [Johannes Brodwall](http://johannesbrodwall.com/).
It was a great experience, I had an opportunity to do some pair programming with six different people and learnt quite a lot about both programming and productivity.
You can find some more thoughts about the event on [Anders Nordby's article](http://andersnordby.wordpress.com/2012/05/21/coderetreat-summer-2012/) (+ C# implementation of the problem we were solving throughout the day).

So what was the problem?
Suspiciously simple: develop a function taking an arbitrary character and printing a diamond-shape like this:

```scala
test("should generate A diamond") {
  diamond('A') should equal (List(
    "A"
  ))
}

test("should generate D diamond") {
  diamond('D') should equal (List(
    "   A   ",
    "  B B  ",
    " C   C ",
    "D     D",
    " C   C ",
    "  B B  ",
    "   A   "
  ))
}
```

The first approach all of us tried was a terrible mixture of `for` loops, counting spaces (nasty off-by-one "error generators" like `- 1`, `+ 1`, `* 2 - 1` all over the place and plenty of special cases.
With every subsequent iteration we were discovering (often with a help from the coderetreat host) how this problem can be solved in various different ways.
I would like to share my thoughts about how we managed to squeeze the code in 3 times less lines, while increasing the readability.

*\[I encourage you to stop right now and try implementing this simple program yourself in the language of choice.
I programmed in Java, Groovy, C#, Scala - and passively paired with a person doing it in Clojure\]*

...

The first advice given to us was to exploit the symmetry.
If you look closely the desired diamond shape has two axes of symmetry - horizontal and vertical.
What about simply drawing one quarter only and then mirroring it along two axes?
We first need a helper function to perform mirroring.
If we are lucky enough it should work on both sequences of strings (each string representing one line) and a single string, treated as a sequence of characters.
Here are some test cases (we practiced TDD a lot):

```scala
test("should mirror array") {
  mirror("abcd") should equal ("abcdcba")
  mirror(List("abc", "def")) should equal (List("abc", "def", "abc"))
  mirror(List("abc", "def", "ghi")) should equal (List("abc", "def", "ghi", "def", "abc"))
}

test("should do nothing when input has only one element") {
  mirror("a") should equal ("a")
  mirror(List("abc")) should equal (List("abc"))
}
```

My first naïve implementation was not sufficient:

```scala
def mirror[T](seq: Seq[T]): Seq[T] =
  seq ++ seq.reverse.tail
```

It was semantically correct and accepted both `Seq[String]` and `String` alone (treated as `Seq[Char]`).
But that was the problem - the result of `mirror("abcd")` was a `Vector[Char]` rather than a `String`.
The method was semantically correct but I wasn't capable of forcing it to return strongly typed string.
So I asked about [Method taking Seq\[T\] to return String rather than Seq\[Char\]](http://stackoverflow.com/questions/10689161) and minutes later got a terrifying answer:

```scala
def mirror[CC, A, That](seq: CC)(implicit asSeq: CC => Seq[A], cbf: CanBuildFrom[CC, A, That]): That = {
  val b = cbf(seq)
  b ++= seq ++ seq.reverse.tail
  b.result()
}
```

You know what?
It works!
If I call `mirror(List("abc", "def"))` I get `List[String]` in return.
But if I call `mirror("abc")` the type of the method is `String`.
Type safe, brilliant and frightening...

Having the `mirror()` function in place we need a second one to actually draw the diamond quarter.
This function can be described with the following test cases:

```scala
test("should print first quarter for 'A'") {
  quarter('A') should equal (List(
    "A"
  ))
}

test("should print first quarter for 'D'") {
  quarter('D') should equal (List(
    "   A",
    "  B ",
    " C  ",
    "D   "
  ))
}
```

The `quarter` is not the cleanest implementation, but wait for the second approach!

```scala
def quarter(c: Char) = {
  val alphabetPos = c - 'A'
  (0 to alphabetPos) map { row =>
    val curChar = ('A' + row).toChar
    (" " * (alphabetPos - row)) + curChar + (" " * row)
  }
}
```

This approach takes advantage of handy `"A" * 3 == "AAA"` construct in Scala.
Having `quarter` and `mirror` methods do you know how to construct the `diamond()` method?
It is beautifully simply:

```scala
def diamond(c: Char) =
  mirror(quarter(c)) map {mirror(_)}
```

We first generate one qurter (north-west) and mirror it to generate south-west piece.
Then we mirror each and every line to generate eastern copies.
That's it!
BTW wondering why I didn't simply wrote `mirror(quarter(c)) map mirror`?
See [this](http://stackoverflow.com/questions/10774284).

The second approach suggested to us was even more intriguing.
When looking at the diamond shape we can clearly see it can be defined in terms of geometry.
By iterating over all possible points and examining whether they belong to the desired shape we end up with extremely compact implementation:

```scala
def diamond2(c: Char) {
  val radius = c - 'A'

  (-radius to radius) foreach {y =>
    (-radius to radius) foreach {x =>
      if (x.abs + y.abs == radius) {
        print(('A' + x.abs).toChar)
      } else {
        print(" ")
      }
    }
    println()
  }
}
```

The condition inside the loop is crucial - it defines whether a given point should be empty or contain a character.
And since it is so simple, why not extract it and allow the client code to define any condition?

```scala
def diamond(c: Char, predicate: (Int, Int, Int) => Boolean) {
  val radius = c - 'A'

  (-radius to radius) foreach {y =>
    (-radius to radius) foreach {x =>
      if (predicate(x, y, radius)) {
        print(('A' + x.abs).toChar)
      } else {
        print(" ")
      }
    }
    println()
  }
}
```

We can now draw ellipses and other shapes in no time by simply passing different `predicate` functions:

```scala
diamond('P', (x, y, radius) => x.abs + y.abs == radius)
diamond('P', (x, y, radius) => math.sqrt(x * x + y * y - radius * radius) < 6)
diamond('P', (x, y, radius) => x.abs == y.abs)

               A               
              B B              
             C   C             
            D     D            
           E       E           
          F         F          
         G           G         
        H             H        
       I               I       
      J                 J      
     K                   K     
    L                     L    
   M                       M   
  N                         N  
 O                           O 
P                             P
 O                           O 
  N                         N  
   M                       M   
    L                     L    
     K                   K     
      J                 J      
       I               I       
        H             H        
         G           G         
          F         F          
           E       E           
            D     D            
             C   C             
              B B              
               A               

          FEDCBABCDEF          
       IHG           GHI       
      JI               IJ      
     KJ                 JK     
    L                     L    
   M                       M   
  NM                       MN  
 ON                         NO 
 O                           O 
 O                           O 
P                             P
P                             P
P                             P
P                             P
P                             P
P                             P
P                             P
P                             P
P                             P
P                             P
P                             P
 O                           O 
 O                           O 
 ON                         NO 
  NM                       MN  
   M                       M   
    L                     L    
     KJ                 JK     
      JI               IJ      
       IHG           GHI       
          FEDCBABCDEF          

P                             P
 O                           O 
  N                         N  
   M                       M   
    L                     L    
     K                   K     
      J                 J      
       I               I       
        H             H        
         G           G         
          F         F          
           E       E           
            D     D            
             C   C             
              B B              
               A               
              B B              
             C   C             
            D     D            
           E       E           
          F         F          
         G           G         
        H             H        
       I               I       
      J                 J      
     K                   K     
    L                     L    
   M                       M   
  N                         N  
 O                           O 
P                             P
```

I think the most important lesson for me was to fully understand the problem and explore as many different approaches as possible.
As long as we were focused on console, spaces and lines, the implementations were very clumsy and complicated.
Once we discovered what the problem really was, understood the problem domain, it became much easier to implement.
And the full minified implementation (in Scala) [fits one Twitter message!](https://twitter.com/tnurkiewicz/status/206862519309058048)
(127 chars).

```scala

def d(c:Char){val r=c-65;-r to r foreach{y=>(-r to r)foreach{x=>print((if(x.abs+y.abs==r)65+x.abs else 32).toChar)};println()}}
```
