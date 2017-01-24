layout: post
title:  "Diophantine Equations and Enumeration"
date:   2016-02-25 13:29:51 -0500
categories: math


## Motivation

About a couple weeks ago, I watched a [certain numberphile video](https://www.youtube.com/watch?v=wymmCdLdPvM) about the number 33.

The problem interested me for its own sake, I wanted to perhaps implement the algorithm they were trying to use to solve for 33. I know that there's no way I can get close to their level of optimization, but it would be a neat thing to work out.

I decomposed the problem into 3 sections, and then decided I would use lisp over python, as tail recursion sounded like it was going to be a useful tool.

## Enumeration

A set has the property of enumeration if there exists a function that will return every element in the set once and only once.

For example, an enumeration of the natural numbers is (0,) 1, 2, 3, 4... an enumeration of the integers is similar, you just alternate the inclusion of the negative number: 0, 1, -1, 2, -2, 3, -3.

It turns out that most number systems have this property, including fractions ([resulting in some rather surprising conclusions](https://www.youtube.com/watch?v=Lfw96n0m1js)).

In the context of this problem, we only need to enumerate through the integers. But we need to go through them three times, and list out all the possible combinations of these numbers. It's quite simple to do with just one or two integer sets, the first is a straightforward formula, and the second is Cantor's Pairing Function. If I had the facility to I would perhaps draw something to help you understand, but I'll let [wikipedia handle this one](https://en.wikipedia.org/wiki/Countable_set#Formal_overview_without_details).

However, that function applied to the context of our problem introduces severe redundancies. Since addition is commutative, order of the numbers in our set does not matter. In 2 dimensions, we halve the time it takes to iterate through all the pairings (since cartesian pairings distinguish aXb from bXa, and sets don't care). It's quite easy to ignore duplicates and come up with something in Scheme that will iterate this.


``` scheme
;; this is a lisp implementation of the cantor pairing function
;; ignoring repeats. (2,0)
(define setsOf2
	(lambda (initialIndex)
		index = initialIndex
		(lambda (signal)
```
Edit 1/23/17: This post terminates here. You can see how I actually implemented it on [github](https://github.com/alphor/diophantine-33/blob/14772bb5f65824ac97fe8e321ece09a98cf00ea3/diophantine-3d.scm#L74)
gen-increment-3-pivot-list is actually cantor's pairing function applied to 3-space but it only enumerates sets, that is, (3 2 1) is enumerated, but any permutation of it (ie (2 3 1), (1 2 3)... etc) is not.