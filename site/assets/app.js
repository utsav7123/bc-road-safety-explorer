"use strict";

const nf = new Intl.NumberFormat("en-CA");
const pf = new Intl.NumberFormat("en-CA", { maximumFractionDigits: 1 });

function animateNumber(el, target) {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) { el.textContent = nf.format(target); return; }
  const start = performance.now();
  const duration = 900;
  function tick(now) {
    const p = Math.min(1, (now - start) / duration);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = nf.format(Math.round(target * eased));
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function makeChart(canvas, labels, values, label, accent, dashed=false) {
  return new Chart(canvas, {
    type: "line",
    data: { labels, datasets: [{
      label, data: values, borderColor: accent, backgroundColor: accent + "22",
      borderWidth: 3, fill: true, tension: .32, pointRadius: 2, pointHoverRadius: 6,
      borderDash: dashed ? [8, 7] : []
    }]},
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: { duration: 1100, easing: "easeOutQuart" },
      plugins: { legend: { labels: { color: "#44515d" } } },
      scales: {
        x: { ticks: { color: "#6d7b87" }, grid: { color: "rgba(24,35,45,.08)" } },
        y: { ticks: { color: "#6d7b87" }, grid: { color: "rgba(24,35,45,.08)" } }
      }
    }
  });
}

function setStoryObserver() {
  const steps = [...document.querySelectorAll(".story-step")];
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => entry.target.classList.toggle("active", entry.isIntersecting));
  }, { threshold: .55 });
  steps.forEach(step => observer.observe(step));
}

function createMap(points) {
  const map = L.map("map", { scrollWheelZoom: false }).setView([53.2, -124.3], 5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  points.forEach(point => {
    const radius = 9 + Math.sqrt(Math.max(point.fatalities, 1)) * .7;
    L.circleMarker([point.lat, point.lon], {
      radius, color: "#ffffff", weight: 1.5, fillColor: "#155d6b", fillOpacity: .65
    }).addTo(map).bindPopup(
      "<strong>" + point.region + "</strong><br>" +
      point.year + "<br>Fatalities: " + nf.format(point.fatalities) +
      "<br>Serious injuries: " + nf.format(point.serious_injuries)
    );
  });
}

function timeline(data, chart) {
  const series = data.annual.fatalities_region;
  const slider = document.getElementById("year-slider");
  const readout = document.getElementById("year-readout");
  const play = document.getElementById("play-years");
  slider.min = 0;
  slider.max = series.length - 1;
  slider.value = series.length - 1;

  function update(index) {
    const row = series[index];
    readout.textContent = row.year;
    document.getElementById("timeline-value").textContent = nf.format(row.value);
    chart.data.datasets[0].pointRadius = series.map((_, i) => i === index ? 7 : 2);
    chart.update("none");
  }
  slider.addEventListener("input", () => update(Number(slider.value)));
  update(Number(slider.value));

  let timer = null;
  play.addEventListener("click", () => {
    if (timer) { clearInterval(timer); timer = null; play.textContent = "▶"; return; }
    play.textContent = "Ⅱ";
    timer = setInterval(() => {
      let next = Number(slider.value) + 1;
      if (next > Number(slider.max)) next = 0;
      slider.value = next;
      update(next);
    }, 700);
  });
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
      animateNumber(card.querySelector(".kpi-value"), kpi.value);
      const change = kpi.five_year_change;
      card.querySelector(".kpi-meta").textContent =
        kpi.year + (change === null ? "" : " · " + (change >= 0 ? "+" : "") + pf.format(change) + "% vs 5 years earlier");
    });

    const trend = data.annual.fatalities_region;
    const trendChart = makeChart(
      document.getElementById("trend-chart"),
      trend.map(d => d.year), trend.map(d => d.value),
      "Fatalities", "#155d6b"
    );

    const users = data.road_users.items.slice(0, 8);
    new Chart(document.getElementById("road-user-chart"), {
      type: "bar",
      data: {
        labels: users.map(d => d.category),
        datasets: [{ label: "Fatalities", data: users.map(d => d.value), backgroundColor: "#a66b17" }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        animation: { duration: 1000 },
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#6d7b87" }, grid: { display: false } },
          y: { ticks: { color: "#6d7b87" }, grid: { color: "rgba(24,35,45,.08)" } }
        }
      }
    });

    const f = data.forecast;
    makeChart(
      document.getElementById("forecast-chart"),
      [...trend.slice(-10).map(d => d.year), ...f.map(d => d.year)],
      [...trend.slice(-10).map(d => d.value), ...Array(f.length).fill(null)],
      "Observed", "#155d6b"
    );
    new Chart(document.getElementById("forecast-overlay"), {
      type: "line",
      data: {
        labels: [...trend.slice(-10).map(d => d.year), ...f.map(d => d.year)],
        datasets: [{
          label: "Baseline projection",
          data: [...Array(trend.slice(-10).length - 1).fill(null), trend.at(-1).value, ...f.map(d => d.value)],
          borderColor: "#a66b17", borderDash: [8,7], borderWidth: 3, pointRadius: 3, tension: .25
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        animation: { duration: 1200 },
        plugins: { legend: { labels: { color: "#44515d" } } },
        scales: {
          x: { display: false }, y: { display: false }
        }
      }
    });

    createMap(data.region_points);
    timeline(data, trendChart);

    const vuln = document.getElementById("vulnerable-list");
    vuln.innerHTML = data.vulnerable_road_users.map(item =>
      "<div class='card'><div class='kpi-label'>" + item.category + "</div><div class='kpi-value'>" +
      nf.format(item.value) + "</div><div class='kpi-meta'>Fatalities in " + data.road_users.year + "</div></div>"
    ).join("");

    status.textContent = "Loaded public RoadSafetyBC aggregate data. Latest year found: " + data.latest_year_seen + ".";
  } catch (error) {
    status.textContent = "Dashboard data has not been built yet. Run the Python pipeline or check the latest GitHub Actions build.";
  }
  setStoryObserver();
}

init();
