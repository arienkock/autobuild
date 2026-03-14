---
id: "002"
title: Extend for NPV
extensibility_scenario: |
  Adding new models in the future should not require ANY changes to the core simulation logic. New variable types and distributions will be added in the future.
---
Implement a model for calculacting net present value. It takes cashflows, discount rates, and the initial investment amount. The result of the individual model calculations should be a timeline that shows the value evolving over the years, so the break-even point can be visually identified.

The user should be able to choose the model. In the case of the NPV model, the result should be visualized as a an area chart showing the "cone of uncertainty" which gets wider as time goes. In the chart the user should see the 50th percentile, and the +/- 1 and 2 sigma areas all together in one chart.