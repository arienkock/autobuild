---
id: "001"
title: Create a monte carlo simulation algorithm
extensibility_scenario: |
  Adding multiple models that calculate different things, from finance to project management.
---
Add the core logic for a monte carlo simulation algorithm to the project.
The number of iterations should be a parameter.
A model (the thing actually calculating the result) should be a parameter.
The model includes a set of variables that each can be 'sampled'.
Variables can be distributions (e.g. normal, uniform, triangular, pareto, etc.).
But variables can also be constants, or arbitrary values.
For this task, it is sufficient to implement a model that simply adds up the values of the randomized variables.
All the results of the simulation should be returned allowing them to be analyzed.
In this task I want you to show the mean, median, and +/- 1 and 2 standard deviations around the mean.
Stack: plain HTML and DOM usage (vanilla JS). 
Create reusable components, functions and classes.
There should be some tests that run directly when executing `npm run test`.
No documentation or comments. Just the code.
