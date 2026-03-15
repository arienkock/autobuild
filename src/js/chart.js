/**
 * Renders an area chart for NPV timeline stats: 50th percentile line and ±1σ, ±2σ bands (cone of uncertainty).
 * @param {HTMLElement} container
 * @param {{ years: number[], median: number[], band1Lower: number[], band1Upper: number[], band2Lower: number[], band2Upper: number[] }} timelineStats
 * @param {{ width?: number, height?: number, padding?: number }} options
 */
export function renderNpvConeChart(container, timelineStats, options = {}) {
  const { width = 600, height = 320, padding = 40 } = options;
  const innerWidth = width - 2 * padding;
  const innerHeight = height - 2 * padding;

  const { years, median, band1Lower, band1Upper, band2Lower, band2Upper } = timelineStats;
  if (years.length === 0) {
    container.innerHTML = "<p class=\"chart-empty\">No data to display.</p>";
    return;
  }

  const allY = [
    ...band2Lower,
    ...band2Upper,
    ...band1Lower,
    ...band1Upper,
    ...median,
    0,
  ];
  const yMin = Math.min(...allY);
  const yMax = Math.max(...allY);
  const yPadding = (yMax - yMin) * 0.05 || 1;
  const yDomain = [yMin - yPadding, yMax + yPadding];
  const xDomain = [years[0], years[years.length - 1]];

  const xScale = (x) =>
    padding + ((x - xDomain[0]) / (xDomain[1] - xDomain[0])) * innerWidth;
  const yScale = (y) =>
    padding + innerHeight - ((y - yDomain[0]) / (yDomain[1] - yDomain[0])) * innerHeight;

  const path = (points) =>
    points
      .map((p, i) => `${i === 0 ? "M" : "L"} ${xScale(p.x)} ${yScale(p.y)}`)
      .join(" ");

  const band2LowerPoints = years.map((x, i) => ({ x, y: band2Lower[i] }));
  const band2UpperPointsReversed = years
    .map((x, i) => ({ x, y: band2Upper[i] }))
    .reverse();
  const band2Path =
    path(band2LowerPoints) +
    " " +
    path(band2UpperPointsReversed).replace(/^M\s*/, "L ") +
    " Z";

  const band1LowerPoints = years.map((x, i) => ({ x, y: band1Lower[i] }));
  const band1UpperPointsReversed = years
    .map((x, i) => ({ x, y: band1Upper[i] }))
    .reverse();
  const band1Path =
    path(band1LowerPoints) +
    " " +
    path(band1UpperPointsReversed).replace(/^M\s*/, "L ") +
    " Z";

  const medianPath = path(years.map((x, i) => ({ x, y: median[i] })));
  const zeroY = yScale(0);
  const zeroPath =
    zeroY >= padding && zeroY <= padding + innerHeight
      ? `M ${xScale(xDomain[0])} ${zeroY} L ${xScale(xDomain[1])} ${zeroY}`
      : "";

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("class", "npv-cone-chart");
  svg.setAttribute("aria-label", "NPV cone of uncertainty over time");

  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  const clip = document.createElementNS("http://www.w3.org/2000/svg", "clipPath");
  clip.setAttribute("id", "chart-clip");
  const clipRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  clipRect.setAttribute("x", padding);
  clipRect.setAttribute("y", padding);
  clipRect.setAttribute("width", innerWidth);
  clipRect.setAttribute("height", innerHeight);
  clip.appendChild(clipRect);
  defs.appendChild(clip);
  svg.appendChild(defs);

  const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
  g.setAttribute("clip-path", "url(#chart-clip)");

  const band2El = document.createElementNS("http://www.w3.org/2000/svg", "path");
  band2El.setAttribute("d", band2Path);
  band2El.setAttribute("class", "cone-band cone-band-2");
  band2El.setAttribute("fill-opacity", "0.25");
  g.appendChild(band2El);

  const band1El = document.createElementNS("http://www.w3.org/2000/svg", "path");
  band1El.setAttribute("d", band1Path);
  band1El.setAttribute("class", "cone-band cone-band-1");
  band1El.setAttribute("fill-opacity", "0.4");
  g.appendChild(band1El);

  if (zeroPath) {
    const zeroEl = document.createElementNS("http://www.w3.org/2000/svg", "path");
    zeroEl.setAttribute("d", zeroPath);
    zeroEl.setAttribute("class", "cone-zero");
    zeroEl.setAttribute("fill", "none");
    zeroEl.setAttribute("stroke-dasharray", "4 4");
    g.appendChild(zeroEl);
  }

  const medianEl = document.createElementNS("http://www.w3.org/2000/svg", "path");
  medianEl.setAttribute("d", medianPath);
  medianEl.setAttribute("class", "cone-median");
  medianEl.setAttribute("fill", "none");
  medianEl.setAttribute("stroke-width", "2");
  g.appendChild(medianEl);

  svg.appendChild(g);

  const xAxis = document.createElementNS("http://www.w3.org/2000/svg", "g");
  xAxis.setAttribute("class", "axis axis-x");
  [xDomain[0], xDomain[1]].forEach((x, i) => {
    const tick = document.createElementNS("http://www.w3.org/2000/svg", "line");
    tick.setAttribute("x1", xScale(x));
    tick.setAttribute("x2", xScale(x));
    tick.setAttribute("y1", padding + innerHeight);
    tick.setAttribute("y2", height);
    xAxis.appendChild(tick);
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", xScale(x));
    label.setAttribute("y", height - 6);
    label.setAttribute("text-anchor", i === 0 ? "start" : "end");
    label.setAttribute("class", "axis-label");
    label.textContent = `Year ${x}`;
    xAxis.appendChild(label);
  });
  svg.appendChild(xAxis);

  container.innerHTML = "";
  container.appendChild(svg);
}
