/**
 * Renders an area chart (cone of uncertainty) for NPV timeline summary.
 * Shows ±2σ band, ±1σ band, and 50th percentile line in one chart.
 */

const PADDING = { top: 20, right: 20, bottom: 36, left: 52 };
const DEFAULT_WIDTH = 640;
const DEFAULT_HEIGHT = 320;

function scaleX(index, length, width) {
  const inner = width - PADDING.left - PADDING.right;
  return length <= 1 ? PADDING.left + inner / 2 : PADDING.left + (index / (length - 1)) * inner;
}

function scaleY(value, yMin, yMax, height) {
  const inner = height - PADDING.top - PADDING.bottom;
  const range = yMax - yMin || 1;
  return PADDING.top + inner * (1 - (value - yMin) / range);
}

function pathBand(xs, ysLow, ysHigh, yMin, yMax, width, height) {
  const points = [];
  for (let i = 0; i < xs.length; i++) {
    points.push(`${scaleX(i, xs.length, width)},${scaleY(ysHigh[i], yMin, yMax, height)}`);
  }
  for (let i = xs.length - 1; i >= 0; i--) {
    points.push(`${scaleX(i, xs.length, width)},${scaleY(ysLow[i], yMin, yMax, height)}`);
  }
  return `M ${points.join(" L ")} Z`;
}

function pathLine(xs, ys, yMin, yMax, width, height) {
  const points = xs.map((_, i) => `${scaleX(i, xs.length, width)},${scaleY(ys[i], yMin, yMax, height)}`);
  return `M ${points.join(" L ")}`;
}

function allValues(summary) {
  return [
    ...summary.minus2Sigma,
    ...summary.minus1Sigma,
    ...summary.median,
    ...summary.plus1Sigma,
    ...summary.plus2Sigma,
  ].filter((v) => Number.isFinite(v));
}

function renderConeChart(container, summary, options = {}) {
  const width = options.width ?? DEFAULT_WIDTH;
  const height = options.height ?? DEFAULT_HEIGHT;
  const values = allValues(summary);
  const yMin = Math.min(...values);
  const yMax = Math.max(...values);
  const yPadding = (yMax - yMin) * 0.05 || 1;
  const yMinS = yMin - yPadding;
  const yMaxS = yMax + yPadding;

  const years = summary.years;
  const innerWidth = width - PADDING.left - PADDING.right;
  const innerHeight = height - PADDING.top - PADDING.bottom;

  const xTicks = years.length <= 10 ? years : years.filter((_, i) => i % Math.ceil(years.length / 8) === 0);
  const yTickCount = 5;
  const yTicks = Array.from({ length: yTickCount + 1 }, (_, i) => yMinS + (yMaxS - yMinS) * (i / yTickCount));

  let svg = `
<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" class="cone-chart">
  <defs>
    <linearGradient id="band2" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#93c5fd" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#93c5fd" stop-opacity="0.1"/>
    </linearGradient>
    <linearGradient id="band1" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#60a5fa" stop-opacity="0.5"/>
      <stop offset="100%" stop-color="#60a5fa" stop-opacity="0.2"/>
    </linearGradient>
  </defs>
  <g class="chart-inner">
    <path d="${pathBand(years, summary.minus2Sigma, summary.plus2Sigma, yMinS, yMaxS, width, height)}" fill="url(#band2)" stroke="none"/>
    <path d="${pathBand(years, summary.minus1Sigma, summary.plus1Sigma, yMinS, yMaxS, width, height)}" fill="url(#band1)" stroke="none"/>
    <path d="${pathLine(years, summary.median, yMinS, yMaxS, width, height)}" fill="none" stroke="#1d4ed8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
  <g class="axis axis-x" fill="none" stroke="#64748b" stroke-width="1">
    <line x1="${PADDING.left}" y1="${height - PADDING.bottom}" x2="${width - PADDING.right}" y2="${height - PADDING.bottom}"/>
    ${xTicks.map((year) => {
      const x = scaleX(year, years.length, width);
      return `<line x1="${x}" y1="${height - PADDING.bottom}" x2="${x}" y2="${height - PADDING.bottom + 6}"/>`;
    }).join("")}
  </g>
  <g class="axis axis-y" fill="none" stroke="#64748b" stroke-width="1">
    <line x1="${PADDING.left}" y1="${PADDING.top}" x2="${PADDING.left}" y2="${height - PADDING.bottom}"/>
    ${yTicks.map((v) => {
      const y = scaleY(v, yMinS, yMaxS, height);
      return `<line x1="${PADDING.left}" y1="${y}" x2="${PADDING.left - 6}" y2="${y}"/>`;
    }).join("")}
  </g>
  <g class="labels axis-x-labels" text-anchor="middle" fill="#475569" font-size="11">
    ${xTicks.map((year) => {
      const x = scaleX(year, years.length, width);
      return `<text x="${x}" y="${height - 8}">${year}</text>`;
    }).join("")}
  </g>
  <g class="labels axis-y-labels" text-anchor="end" fill="#475569" font-size="11">
    ${yTicks.map((v) => {
      const y = scaleY(v, yMinS, yMaxS, height);
      const label = v >= 1000000 ? (v / 1e6).toFixed(1) + "M" : v >= 1000 ? (v / 1000).toFixed(1) + "k" : v.toFixed(0);
      return `<text x="${PADDING.left - 8}" y="${y + 4}">${label}</text>`;
    }).join("")}
  </g>
  <g class="legend" transform="translate(${width - PADDING.right - 120}, ${PADDING.top})">
    <rect x="0" y="0" width="12" height="12" fill="url(#band2)" stroke="#93c5fd"/>
    <text x="18" y="11" font-size="11" fill="#475569">±2σ</text>
    <rect x="0" y="18" width="12" height="12" fill="url(#band1)" stroke="#60a5fa"/>
    <text x="18" y="29" font-size="11" fill="#475569">±1σ</text>
    <line x1="0" y2="42" x2="12" y2="42" stroke="#1d4ed8" stroke-width="2"/>
    <text x="18" y="46" font-size="11" fill="#475569">50th %</text>
  </g>
</svg>`;

  container.innerHTML = svg;
}

export { renderConeChart, PADDING, DEFAULT_WIDTH, DEFAULT_HEIGHT };
