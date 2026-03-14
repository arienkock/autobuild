import { simulate } from '../montecarlo/simulate.js'
import { Model } from '../montecarlo/model.js'
import { Normal, Uniform, Triangular, Constant } from '../montecarlo/variables.js'
import { summary } from '../montecarlo/stats.js'
import { StatsPanel, Histogram } from './components.js'

const defaultModel = new Model([
  new Normal(50, 10),
  new Uniform(0, 30),
  new Triangular(5, 15, 25),
  new Constant(10),
])

function runSimulation(model, iterations) {
  const results = simulate(model, iterations)
  const s = summary(results)

  const output = document.getElementById('output')
  output.innerHTML = ''

  const chart = Histogram(results, s)
  output.appendChild(chart)
  output.appendChild(StatsPanel(s))
}

document.getElementById('run-btn').addEventListener('click', () => {
  const iterations = parseInt(document.getElementById('iterations').value, 10)
  runSimulation(defaultModel, iterations)
})
