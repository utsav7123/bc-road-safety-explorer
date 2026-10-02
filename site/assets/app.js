"use strict";

const nf = new Intl.NumberFormat("en-CA");
const pf = new Intl.NumberFormat("en-CA", { maximumFractionDigits: 1 });

function lineChart(canvas, labels, datasets) {
  return new Chart(canvas, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          labels: {
            color: "#343434",
            boxWidth: 20,
            usePointStyle: false
          }
        }
      },
      scales: {
        x: {
          ticks: { color: "#666666" },
          grid: { color: "rgba(0,0,0,.06)" }
        },
        y: {
          ticks: { color: "#666666" },
          grid: { color: "rgba(0,0,0,.08)" }
        }
      }
    }
  });
}

function createMap(points) {
  const map = L.map("map", { scrollWheelZoom: false }).setView([53.2, -124.3], 5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  points.forEach(point => {
    const radius = 8 + Math.sqrt(Math.max(point.fatalities, 1)) * 0.65;
    L.circleMarker([point.lat, point.lon], {
      radius,
      color: "#ffffff",
      weight: 2,
      fillColor: "#f36c21",
      fillOpacity: 0.82
    }).addTo(map).bindPopup(
      "<strong>" + point.region + "</strong><br>" +
      point.year +
      "<br>Fatalities: " + nf.format(point.fatalities) +
      "<br>Serious injuries: " + nf.format(point.serious_injuries)
    );
  });
}

function setupYearSelector(data, chart) {
  const series = data.annual.fatalities_region;
  const slider = document.getElementById("year-slider");
  const readout = document.getElementById("year-readout");
  const value = document.getElementById("timeline-value");

  slider.min = 0;
  slider.max = series.length - 1;
  slider.value = series.length - 1;

  function update(index) {
    const row = series[index];
    readout.textContent = row.year;
    value.textContent = nf.format(row.value);
    chart.data.datasets[0].pointRadius = series.map((_, i) => i === index ? 6 : 2);
    chart.update("none");
  }

  slider.addEventListener("input", () => update(Number(slider.value)));
  update(Number(slider.value));
}

async function init() {
  const status = document.getElementById("status");

  try {
    const response = await fetch("./data/dashboard.json", { cache: "no-store" });
    if (!response.ok) throw new Error("Dashboard data unavailable");
    const data = await response.json();

    data.kpis.forEach((kpi, index) => {
      const card = document.querySelector('[data-kpi="' + index + '"]');
      card.querySelector(".kpi-label").textContent = kpi.label;
      card.querySelector(".kpi-value").textContent = nf.format(kpi.value);

      const change = kpi.five_year_change;
      card.querySelector(".kpi-meta").textContent =
        kpi.year +
        (change === null ? "" : " · " + (change >= 0 ? "+" : "") + pf.format(change) + "% vs 5 years earlier");
    });

    const trend = data.annual.fatalities_region;
    const trendChart = lineChart(
      document.getElementById("trend-chart"),
      trend.map(d => d.year),
      [{
        label: "Fatalities",
        data: trend.map(d => d.value),
        borderColor: "#f36c21",
        backgroundColor: "rgba(243,108,33,.10)",
        borderWidth: 3,
        fill: true,
        tension: 0.18,
        pointRadius: 2,
        pointHoverRadius: 5
      }]
    );

    const users = data.road_users.items.slice(0, 8);
    new Chart(document.getElementById("road-user-chart"), {
      type: "bar",
      data: {
        labels: users.map(d => d.category),
        datasets: [{
          label: "Fatalities",
          data: users.map(d => d.value),
          backgroundColor: "#f36c21"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: { legend: { display: false } },
        scales: {
          x: {
            ticks: { color: "#666666" },
            grid: { display: false }
          },
          y: {
            ticks: { color: "#666666" },
            grid: { color: "rgba(0,0,0,.08)" }
          }
        }
      }
    });

    const recent = trend.slice(-10);
    const projection = data.forecast;
    const forecastLabels = [...recent.map(d => d.year), ...projection.map(d => d.year)];
    const observedValues = [...recent.map(d => d.value), ...Array(projection.length).fill(null)];
    const projectedValues = [
      ...Array(Math.max(recent.length - 1, 0)).fill(null),
      recent.at(-1).value,
      ...projection.map(d => d.value)
    ];

    lineChart(
      document.getElementById("forecast-chart"),
      forecastLabels,
      [
        {
          label: "Observed",
          data: observedValues,
          borderColor: "#343434",
          backgroundColor: "rgba(52,52,52,.04)",
          borderWidth: 2.5,
          fill: false,
          tension: 0.18,
          pointRadius: 2,
          pointHoverRadius: 5
        },
        {
          label: "Baseline projection",
          data: projectedValues,
          borderColor: "#f36c21",
          backgroundColor: "transparent",
          borderWidth: 3,
          borderDash: [7, 6],
          fill: false,
          tension: 0.18,
          pointRadius: 3,
          pointHoverRadius: 5
        }
      ]
    );

    createMap(data.region_points);
    setupYearSelector(data, trendChart);

    const vulnerable = document.getElementById("vulnerable-list");
    vulnerable.innerHTML = data.vulnerable_road_users.map(item =>
      "<div class='card'><div class='kpi-label'>" + item.category + "</div>" +
      "<div class='kpi-value'>" + nf.format(item.value) + "</div>" +
      "<div class='kpi-meta'>Fatalities in " + data.road_users.year + "</div></div>"
    ).join("");

    status.textContent =
      "Public RoadSafetyBC aggregate data loaded. Latest year available in the current source set: " +
      data.latest_year_seen + ".";
  } catch (error) {
    status.textContent =
      "Dashboard data is unavailable. Check the latest deployment or data pipeline run.";
  }
}

init();
