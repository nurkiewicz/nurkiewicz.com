---
layout: post
title: Clojure for Machine Learning book review
date: '2014-06-29T23:30:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- machine learning
- clojure
- review
- books
modified_time: '2014-06-29T23:30:04.568+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5553846777268222056
blogger_orig_url: https://www.nurkiewicz.com/2014/06/clojure-for-machine-learning-book-review.html
image: /assets/img/clojure-for-machine-learning-book-review/hero.jpg
---

A [Clojure for Machine Learning](http://www.packtpub.com/clojure-for-machine-learning/book), together with [Clojure Data Analysis Cookbook](http://www.amazon.com/gp/product/B00BECVV9C/ref=as_li_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B00BECVV9C&linkCode=as2&tag=javaandneighb-20&linkId=GWN6ALWAIPVBYQ6H), are two compelling books for people interested in data mining and reasoning.
It is also worth mentioning that the amount of publications not dedicated to Clojure itself but how to effectively use it in real world problems is growing.
Therefore Clojure for Machine Learning is not a suitable book for newcomers to the language.
It will probably not be a good starting point for people completely new to machine learning as well.
However basic Clojure knowledge and rough understanding of core concepts in machine learning will be enough to enjoy this book.

Book goes through pretty much all standard machine learning topics, including: linear regression, various classification algorithms, clustering, artificial neural networks and support vector machines.
Author also briefly covers large scale machine learning on top off Hadoop and Map Reduce.
Too bad other more modern BigData solutions were not represented.
This book starts with a brief introduction to matrices and linear algebra.
Not being an expert in the field I spotted few embarrassing mistakes.
E.g. "*For matrix A of size m x n and B of size p x q \[...\]
if n = p, the product of A and B is a new matrix of size n x q*" – in this notation the size of A times B is m x q, not n x q.
Few pages later formula for calculating inversion of 2x2 matrix is broken (incorrectly transposed).
For a book filled with math I would expect reviewers or proof readers to double checks easily available formulas.

Please keep in mind that [*Clojure for Machine Learning*](http://www.amazon.com/gp/product/1783284358/ref=as_li_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=1783284358&linkCode=as2&tag=javaandneighb-20&linkId=AP7VRAS7XZYCUXRG) is not a best choice to learn Clojure, it expects you to know basic constructs.
Moreover Clojure code was not always perfectly idiomatic.
Using `+ 1` rather than `inc` function, nesting of functions instead of composing or threading (`->` macro) them, abuse of atoms to introduce mutability or using `reduce` instead of conceptually simpler `apply +` to add up vector of numbers.
In one place we see sorting just to take first element – where simply taking minimum would be enough, cutting running time from O(nlogn) to O(n).
However author does a good job explaining the code and in general it is quite pleasant to read.
Many examples are written on top of [`ml-clj`](http://antoniogarrote.github.io/clj-ml/) library, sometimes spiced with [Incanter](http://incanter.org/) for visualization.
But when the algorithm is not very complex, author implements it from scratch in plain Clojure.
I found that really enjoyable.

I was reading an e-book on a dated Kindle Keyboard.
The experience was rather good, however math formulas were stored in bitmap format and not scaled properly, thus when inlined in text they were much bigger than ordinary font, resulting in lots of empty space between lines.
This is just cosmetics, maybe related to my device.
Also one or two times the book references colours on pictures, which doesn’t work well on a black and white e-book reader.

Despite few issues, I found this book rather complete and moderately easy to read, taking subject into account.
If you want to discover machine learning and have no prior Clojure knowledge, start from learning Clojure first.
But if you happen to use Clojure already and need to improve your understanding or find good reference, definitely check out *Clojure for machine learning*.
You can tell an author is an expert in the field and different aspects are explained well.
You will not find many complete recipes, but a solid foundation instead.

Disclaimer: I received a free copy of this book from [Packt Publishing](http://www.packtpub.com/) and was asked for a review.
