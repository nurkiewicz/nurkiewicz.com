---
title: "Best place to commute from in Warsaw: public transit heatmap"
tags: Python, geospatial
layout: post
---

Location, location, location!
That's what the real estate agent will tell you when asked what's the most important factor when choosing the place to live.
When living in a modern, busy city like Warsaw you have two choices: travelling by car or by public transit.
I came up with the idea to automate finding the best place to live in Warsaw, transport-wise.
My plan is to estimate the time it takes to commute from every address in Warsaw to the city center.
I'm focusing on public transport and I'd like to find both hidden gems and transport black holes.
That is, places with great commute time despite the distance and the opposite - respectively.

## Assumptions

1. The city center is Metro Świętokrzyska, the place where the two existing metro lines cross.
2. I use Google Distance API to measure how long it takes to commute, as well as travel by car.
3. I assume Monday morning, 8 AM, as departure time

## Collecting the data

First, I need to figure out all the addresses in Warsaw.
Amazingly, the official data portal of Polish Governemnt provides just that: [in CSV, SHP and GML formats](https://dane.gov.pl/pl/dataset/469).
I chose the least poerful, but still massive CSV dataset.
It containts street name/address, latitude/longitude, etc.
120 thousand records.
SHP file has the exact shape of each lot, which is even better, but I didn't need that.

Having all the addresses, let's ask Google's API how long it takes from each and every one of them to the city center.
After a few hours and collecting about 10% of the records (I asked for both public transit and car travel time) I realized I exhausted the free plan of Distance API.
$14 I could cover from Patreon (which I don't have), ads (which I don't display) or somehow monetizing data from Google Analytics (which I don't emebed).
Well, I guess I have enough data.




The first step was figuring out what are the 
The first step was collecting raw data using Google's API.

