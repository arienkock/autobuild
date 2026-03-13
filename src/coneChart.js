/**
 * Renders a "cone of uncertainty" area chart for a timeline summary.
 * Shows 50th percentile line and ±1σ / ±2σ bands in one chart.
 *
 * @typedef {{ yearCount: number, median: number[], minus2Sigma: number[], minus1Sigma: number[], plus1Sigma: number[], plus2Sigma: number[] }} TimelineSummary
 */

const PADDING = { top: 12, right: 12, bottom: 28, left: 48 };
const MEDIAN_STROKE = '#1a1a1a';
const BAND_2SIGMA_FILL = 'rgba(100, 140, 200, 0.25)';
const BAND_1SIGMA_FILL = 'rgba(100, 140, 200, 0.4)';
const ZERO_STROKE = 'rgba(0,0,0,0.2)';

/**
 * @param {TimelineSummary} summary
 * @param {{ width: number, height: number }} size
 * @returns {SVGSVGElement}
 */
export function renderConeChart(summary, size = { width: 600, height: 320 }) {
  const { width, height } = size;
  const { yearCount, median, minus2Sigma, minus1Sigma, plus1Sigma, plus2Sigma } = summary;
  const innerWidth = width - PADDING.left - PADDING.right;
  const innerHeight = height - PADDING.top - PADDING.bottom;

  const allValues = [
    ...minus2Sigma,
    ...plus2Sigma,
    ...median,
  ].filter((v) => Number.isFinite(v));
  const yMin = allValues.length ? Math.min(0, ...allValues) : 0;
  const yMax = allValues.length ? Math.max(0, ...allValues) : 1;
  const yRange = yMax - yMin || 1;
  const yScale = (v) => PADDING.top + innerHeight - ((v - yMin) / yRange) * innerHeight;
  const xScale = (t) => PADDING.left + (t / Math.max(1, yearCount)) * innerWidth;

  const path = (points) =>
    points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${xScale(p.x)} ${yScale(p.y)}`).join(' ') + ' Z';

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('width', String(width));
  svg.setAttribute('height', String(height));
  svg.setAttribute('class', 'cone-chart');

  // Zero line
  const y0 = yScale(0);
  const lineZero = document.createElementNS('http://www.w3.org/2000/svg', 'line');
  lineZero.setAttribute('x1', String(PADDING.left));
  lineZero.setAttribute('y1', String(y0));
  lineZero.setAttribute('x2', String(width - PADDING.right));
  lineZero.setAttribute('y2', String(y0));
  lineZero.setAttribute('stroke', ZERO_STROKE);
  lineZero.setAttribute('stroke-dasharray', '4,4');
  lineZero.setAttribute('stroke-width', '1');
  svg.appendChild(lineZero);

  const n = yearCount;
  const band2Points = [
    ...minus2Sigma.map((y, i) => ({ x: i, y })),
    ...[...plus2Sigma].reverse().map((y, i) => ({ x: n - 1 - i, y })),
  ];
  const band1Points = [
    ...minus1Sigma.map((y, i) => ({ x: i, y })),
    ...[...plus1Sigma].reverse().map((y, i) => ({ x: n - 1 - i, y })),
  ];

  const path2 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path2.setAttribute('d', path(band2Points));
  path2.setAttribute('fill', BAND_2SIGMA_FILL);
  path2.setAttribute('stroke', 'none');
  svg.appendChild(path2);

  const path1 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path1.setAttribute('d', path(band1Points));
  path1.setAttribute('fill', BAND_1SIGMA_FILL);
  path1.setAttribute('stroke', 'none');
  svg.appendChild(path1);

  const medianPath = median
    .map((y, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(y)}`)
    .join(' ');
  const lineMedian = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  lineMedian.setAttribute('d', medianPath);
  lineMedian.setAttribute('fill', 'none');
  lineMedian.setAttribute('stroke', MEDIAN_STROKE);
  lineMedian.setAttribute('stroke-width', '2');
  lineMedian.setAttribute('stroke-linecap', 'round');
  lineMedian.setAttribute('stroke-linejoin', 'round');
  svg.appendChild(lineMedian);

  // X axis labels (years)
  for (let t = 0; t <= yearCount; t += Math.max(1, Math.floor(yearCount / 10))) {
    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', String(xScale(t)));
    text.setAttribute('y', String(height - 4));
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('font-size', '10');
    text.setAttribute('fill', '#555');
    text.textContent = String(t);
    svg.appendChild(text);
  }

  return svg;
}
