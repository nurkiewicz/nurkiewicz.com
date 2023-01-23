---
category: podcast
title: "#30: Linear Regression: simple, yet powerful machine learning"
redirect_from:
  - /30
tags: linear-regression machine-learning kaggle supervised-learning
description: >
    Linear regression is one of the simplest machine learning algorithms.
    But also quite useful.
    It takes a bunch of existing, known observations and tries to predict how new observations will look like.
    Think about forecasting or finding trends.
    It says "_linear_" because the algorithm essentially finds a straight line that most closely follows the observations.
    OK, let's take a concrete example.
    Imagine you are selling your apartment.
    What is the right price for it?
    Well, you compare it to similar apartments in your neighborhood.
    If someone sells the exact same flat across the street, your price should be very similar.
    If another flat is sold, but 10% larger, expect its price to be 10% higher as well.
    Yet another flat is half the size of yours.
    So expect its price to be just 50% of your estimated asking price.
    Sound reasonable?
---

{% include player.html spotify_id="7CtIsqE5g04QO0VYdw82ar" youtube_id="6TalLh9CM9w" %}

{{ page.description }}



As a matter of fact, this train of thought is quite obvious.
The biggest factor in real estate pricing is its area.
For example, let's say one square foot in New York costs around $1000.
The total price is clearly linear: more square feet, higher price.
How did I know it's $1000?
Well, I looked at a few hundred offers in New York and drew them on a chart.
Size on the X axis, price on the Y axis.
X is known as an independent variable, Y as a dependent variable.
Now if you imagine that chart, each point represents one apartment.
I can now draw a straight line that tries to be as close to every point as possible.
Of course points aren't completely aligned.
Some apartments are large but old and stinky.
Others are small, but very comfy.
The former will be cheaper per square feet and below the line.
The latter - more expensive and above it.
But in general the linear relationship is clear.
Even better, the slope of this line is the price per square foot!
The steeper it is, the faster the prices grow with the growing size.

OK, this is quite naive.
The area is not everything.
Another contributing factor is the location.
Price on Manhattan can be twice as high as in Brooklyn.
Our straight line doesn't take that into account, leading to large errors.
So now, our X axis is actually a 2-dimensional plane!
We have two independent variables: square footage and location.
Let's put aside how to quantify location as a number.
I'm sure you can come up with something.
Drawing a straight line is no longer that simple.
Our chart is 3-dimensional, with price being the third dimension.
In reality there are many, many more features that contribute to the final price:

* Number of bedrooms and bathrooms
* Which floor
* Parking space availability
* How many years since the last renovation
* etc.

Suddenly our X variable has tens of features.
Some of them contribute greatly to the price, others have only minimal effect.
A good real estate agent knows these coefficients by heart.
The cost per square foot, how much extra she should charge for a parking lot, and so on.
Some coefficients are negative.
For example, the further we are to the nearest subway station, the lower the price.

OK, how can linear regression help?
You start with writing down all apartments in a giant table.
One apartment per row.
Each feature is one column
Their respective prices are in a column as well.
An algorithm will come up with the most suitable coefficients.
Having enough data, the computer will discover which features contribute the most to the price.
And which ones are negligible.
It's still a straight line, but in an n-dimensional space.
Hard to visualize.

It's called supervised learning.
Given enough training data we can reliably predict new observations.
Other examples include predicting tree's age by its height.
Or unknown car's top speed knowing its engine's power and total mass.

If you are interested in how linear regression finds the coefficients, check out the show notes.
You'll find articles about so-called _gradient descent_.
That's it, thanks for listening, bye!



# More materials

* [Linear regression](https://en.wikipedia.org/wiki/Linear_regression) on Wikipedia
* [Linear regression and gradient descent for absolute beginners](https://towardsdatascience.com/linear-regression-and-gradient-descent-for-absolute-beginners-eef9574eadb0)
* [Linear Regression for Predicting Real Estate Price](https://deshiwa.medium.com/linear-regression-for-predicting-real-estate-price-712ccf746965)
* [Real estate.csv](https://www.kaggle.com/quantbruce/real-estate-price-prediction) dataset on kaggle
* [Gradient descent](https://en.wikipedia.org/wiki/Gradient_descent)
* [Anscombe's quartet](https://en.wikipedia.org/wiki/Anscombe%27s_quartet) - when linear regression is lying


