export function StatsPanel(s) {
  const el = document.createElement('div')
  el.className = 'stats-panel'

  const fmt = v => v.toFixed(3)

  const rows = [
    ['Mean', fmt(s.mean)],
    ['Median', fmt(s.median)],
    ['Std Dev', fmt(s.stddev)],
    ['\u00b11\u03c3', `${fmt(s.range1[0])} \u2013 ${fmt(s.range1[1])}`],
    ['\u00b12\u03c3', `${fmt(s.range2[0])} \u2013 ${fmt(s.range2[1])}`],
  ]

  el.innerHTML = rows
    .map(([label, value]) => `<div class="stat-row"><span class="stat-label">${label}</span><span class="stat-value">${value}</span></div>`)
    .join('')

  return el
}

export function Histogram(values, summary, { bins = 40, width = 600, height = 200 } = {}) {
  const min = Math.min(...values)
  const max = Math.max(...values)
  const binWidth = (max - min) / bins

  const counts = new Array(bins).fill(0)
  for (const v of values) {
    const i = Math.min(Math.floor((v - min) / binWidth), bins - 1)
    counts[i]++
  }

  const maxCount = Math.max(...counts)
  const pad = { top: 10, right: 10, bottom: 20, left: 10 }
  const innerW = width - pad.left - pad.right
  const innerH = height - pad.top - pad.bottom
  const barW = innerW / bins

  const toX = v => pad.left + ((v - min) / (max - min)) * innerW
  const toH = c => (c / maxCount) * innerH

  const bars = counts
    .map((c, i) => {
      const x = pad.left + i * barW
      const h = toH(c)
      return `<rect x="${x}" y="${pad.top + innerH - h}" width="${barW - 1}" height="${h}" class="bar"/>`
    })
    .join('')

  const marker = (v, cls) => {
    const x = toX(v)
    return `<line x1="${x}" y1="${pad.top}" x2="${x}" y2="${pad.top + innerH}" class="${cls}"/>`
  }

  const band = (lo, hi, cls) => {
    const x1 = toX(lo)
    const x2 = toX(hi)
    return `<rect x="${x1}" y="${pad.top}" width="${x2 - x1}" height="${innerH}" class="${cls}"/>`
  }

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`)
  svg.setAttribute('width', '100%')
  svg.className = 'histogram'
  svg.innerHTML = `
    ${band(summary.range2[0], summary.range2[1], 'band band-2')}
    ${band(summary.range1[0], summary.range1[1], 'band band-1')}
    ${bars}
    ${marker(summary.mean, 'marker mean-line')}
    ${marker(summary.median, 'marker median-line')}
  `

  return svg
}
