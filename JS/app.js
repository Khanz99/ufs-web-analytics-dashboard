function buildNoCacheUrl(path) {
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}t=${Date.now()}`;
}

async function fetchJson(path) {
  const response = await fetch(buildNoCacheUrl(path), {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// Load Overview Data
async function loadOverview() {
  try {
    const data = await fetchJson("data/overview.json");

    document.getElementById("users").textContent = Number(data.users || 0).toLocaleString();
    document.getElementById("page-views").textContent = Number(data.page_views || 0).toLocaleString();
    document.getElementById("avg-engagement-time").textContent = data.avg_engagement_time || "00:00:00";
   const activeUsers = Number(data.users || 0);
   const newUsers = Number(data.new_users || 0);
   const returningUsers = Math.max(activeUsers - newUsers, 0);

   const newUsersPercent = activeUsers > 0
   ? ((newUsers / activeUsers) * 100).toFixed(1)
   : "0.0";

   const returningUsersPercent = activeUsers > 0
   ? ((returningUsers / activeUsers) * 100).toFixed(1)
   : "0.0";

  document.getElementById("new-users-percent").textContent = `${newUsersPercent}%`;
  document.getElementById("returning-users-percent").textContent = `${returningUsersPercent}%`;
    document.getElementById("report-period").textContent = `Reporting period: ${data.report_period || "Unavailable"}`;
  } catch (error) {
    console.error("Failed to load overview data:", error);
  }
}

// Load Top Pages
async function loadTopPages() {
  try {
    const data = await fetchJson("data/top_pages.json");

    const list = document.getElementById("top-pages-list");
    list.innerHTML = "";

    if (!Array.isArray(data) || data.length === 0) {
      list.innerHTML = "<li>No top pages available</li>";
      return;
    }

    data.forEach(item => {
      const li = document.createElement("li");
      li.innerHTML = `
        ${item.page}
        (<span class="metric">${Number(item.visits || 0).toLocaleString()} visits</span>)
      `;
      list.appendChild(li);
    });
  } catch (error) {
    console.error("Failed to load top pages:", error);
  }
}

// Load Top Web Stories
async function loadWebStories() {
  try {
    const data = await fetchJson("data/top_web_stories.json");

    const list = document.getElementById("top-web-stories-list");
    list.innerHTML = "";

    if (!Array.isArray(data) || data.length === 0) {
      list.innerHTML = "<li>No web stories available</li>";
      return;
    }

    data.forEach(item => {
      const li = document.createElement("li");
      li.innerHTML = `
        ${item.title}
        (<span class="metric">${Number(item.page_views || 0).toLocaleString()} views</span>)
      `;
      list.appendChild(li);
    });
  } catch (error) {
    console.error("Failed to load web stories:", error);
  }
}

// Load Google Trends from SerpApi
async function loadTrends() {
  try {
    const data = await fetchJson("data/google_trends.json");

    renderGoogleTrendRows("trends-topics-body", data.related_topics || [], "topic");
    renderGoogleTrendRows("trends-queries-body", data.related_queries || [], "query");

  } catch (error) {
    console.error("Failed to load SerpApi Trends data:", error);
  }
}

function renderGoogleTrendRows(bodyId, items, type) {
  const body = document.getElementById(bodyId);
  if (!body) return;

  body.innerHTML = "";

  if (!Array.isArray(items) || items.length === 0) {
    body.innerHTML = `<tr><td colspan="4">No data available</td></tr>`;
    return;
  }

  items.slice(0, 5).forEach((item, index) => {
    const label =
      type === "topic" && item.type
        ? `${item.title} - ${item.type}`
        : item.title;

    const value = Number(item.value || 0);

    body.innerHTML += `
      <tr class="trend-row">
        <td class="trend-rank">${index + 1}</td>
        <td class="trend-label">${label}</td>
        <td class="trend-score">${value}</td>
        <td class="trend-bar-cell">
          <div class="trend-bar-bg">
            <div class="trend-bar-fill" style="width:${value}%"></div>
          </div>
        </td>
      </tr>
    `;
  });
}

// Load Search Console
async function loadSearchConsoleQueries() {
  try {
    const data = await fetchJson("data/search_console.json");
    const body = document.getElementById("search-console-queries-body");

    if (!body) return;
    body.innerHTML = "";

    if (Array.isArray(data.queries) && data.queries.length > 0) {
      data.queries.forEach((item, index) => {
        const row = `<tr><td>${index + 1}</td><td>${item.query} (<span class="metric">${Number(item.clicks || 0).toLocaleString()} clicks</span>)</td></tr>`;
        body.innerHTML += row;
      });
    } else {
      body.innerHTML = `<tr><td colspan="2">No Search Console queries available</td></tr>`;
    }
  } catch (error) {
    console.error("Failed to load Search Console data:", error);
  }
}

// Load Traffic Chart
async function loadTrafficChart() {
  try {
    const data = await fetchJson("data/daily_traffic.json");

    if (!Array.isArray(data) || !data.length) return;

    const labels = data.map(item => item.date);
    const values = data.map(item => Number(item.active_users) || 0);

    const canvas = document.getElementById("dailyTrafficChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    if (window.dailyTrafficChartInstance) {
      window.dailyTrafficChartInstance.destroy();
    }

    window.dailyTrafficChartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "Active Users",
          data: values,
          backgroundColor: "#0F204B",
          borderColor: "#0F204B",
          borderWidth: 1,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false
      }
    });

  } catch (error) {
    console.error("Error loading traffic chart:", error);
  }
}

// Load Device Chart
async function loadDeviceChart() {
  try {
    const data = await fetchJson("data/device_breakdown.json");

    const filteredData = Array.isArray(data)
      ? data.filter(item => {
          const device = (item.device || "").toLowerCase().trim();
          return device !== "smart tv";
        })
      : [];

    const labels = filteredData.map(item => item.device);
    const values = filteredData.map(item => Number(item.percentage) || 0);

    const canvas = document.getElementById("deviceChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    if (window.deviceChartInstance) {
      window.deviceChartInstance.destroy();
    }

    window.deviceChartInstance = new Chart(ctx, {
      type: "pie",
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: ["#0F204B", "#A71930", "#A7A8AA", "#8B8D8E"],
          borderColor: "#ffffff",
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false
      }
    });

  } catch (error) {
    console.error("Device chart failed:", error);
  }
}

async function loadCombinedTrends() {
  try {
    const data = await fetchJson("data/google_trends.json");

    const topics = data.related_topics || [];
    const queries = data.related_queries || [];
    const body = document.getElementById("combined-trends-body");

    if (!body) return;

    body.innerHTML = "";

    for (let i = 0; i < 5; i++) {
      const topic = topics[i];
      const query = queries[i];

      const topicText = topic ? `${topic.title} – ${topic.type}` : "-";
      const queryText = query ? query.title : "-";

      body.innerHTML += `
        <tr>
          <td>${topicText}</td>
          <td>${queryText}</td>
        </tr>
      `;
    }
  } catch (error) {
    console.error("Failed to load combined trends:", error);
  }
}

async function initDashboard() {
  await Promise.all([
    loadOverview(),
    loadTopPages(),
    loadWebStories(),
    loadCombinedTrends(),
    loadSearchConsoleQueries(),
    loadTrafficChart(),
    loadDeviceChart()
  ]);
}

document.addEventListener("DOMContentLoaded", () => {
  initDashboard();

  const refreshButton = document.querySelector(".refresh-btn");

  if (refreshButton) {
    refreshButton.addEventListener("click", async () => {
      try {
        refreshButton.disabled = true;
        refreshButton.textContent = "Refreshing...";

        const response = await fetch("/refresh-data", {
          method: "POST"
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
          throw new Error(result.error || result.message || "Refresh failed");
        }

        refreshButton.textContent = "Updated";

        setTimeout(() => {
          window.location.reload();
        }, 1000);

      } catch (error) {
        console.error("Refresh failed:", error);
        alert("Refresh failed. Check PowerShell for details.");

        refreshButton.disabled = false;
        refreshButton.textContent = "Refresh Data";
      }
    });
  }
});
// Refresh Data button - runs the Python/Flask refresh endpoint
const refreshButton = document.querySelector(".refresh-btn");

if (refreshButton) {
  refreshButton.addEventListener("click", async () => {
    try {
      refreshButton.disabled = true;
      refreshButton.textContent = "Refreshing...";

      const response = await fetch("/refresh-data", {
        method: "POST"
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || result.message || "Refresh failed");
      }

      refreshButton.textContent = "Updated";

      setTimeout(() => {
        window.location.reload();
      }, 1000);

    } catch (error) {
      console.error("Refresh failed:", error);
      alert("Refresh failed. Check PowerShell for details.");

      refreshButton.disabled = false;
      refreshButton.textContent = "Refresh Data";
    }
  });
}