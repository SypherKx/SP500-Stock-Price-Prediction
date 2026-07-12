// ===== STATE =====
let priceChart = null;
let backtestChart = null;
let currentTicker = "AAPL";
let currentPeriod = "1y";
let autocompleteTimeout = null;
let isLoading = false;

// Loading messages rotation
const LOADING_STEPS = [
    { title: "Connecting to Market...", msg: "Reaching out to Yahoo Finance servers for ticker data." },
    { title: "Fetching Stock Prices...", msg: "Retrieving historical open, high, low, close, and volume." },
    { title: "Building Features...", msg: "Generating rolling ratios and trend vectors across horizons." },
    { title: "Initializing Model...", msg: "Setting up RandomForestClassifier in the backend." },
    { title: "Training Decision Trees...", msg: "Bootstrapping trees on historical S&P 500 data." },
    { title: "Running Backtest...", msg: "Evaluating model step-by-step since 1990 — no data leakage." },
    { title: "Calculating Metrics...", msg: "Comparing model precision vs buy-and-hold baseline." },
    { title: "Generating Forecast...", msg: "Analyzing today's signals to predict tomorrow's direction." }
];
let loaderInterval = null;
let loaderStep = 0;

// ===== INIT =====
document.addEventListener("DOMContentLoaded", () => {
    initThemeToggle();
    initSearch();
    initTimeframeSelectors();
    initSliders();
    initForm();
    initQuickChips();
    initScrollReveal();
});

// ===== THEME TOGGLE (DEPRECATED FOR REVOLUT REDESIGN) =====
function initThemeToggle() {
    // High-contrast full-bleed band rhythm has fixed light/dark bands.
    // We execute chart theme styling immediately.
    updateChartThemes();
}

function applyTheme(theme) {
    updateChartThemes();
}

// ===== SCROLL REVEAL =====
function initScrollReveal() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("active");
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll(".reveal").forEach(el => {
        observer.observe(el);
    });
}

// ===== SEARCH & AUTOCOMPLETE =====
function initSearch() {
    const input = document.getElementById("ticker-input");
    const btn = document.getElementById("search-btn");
    const dropdown = document.getElementById("autocomplete-dropdown");

    // Typing — debounced autocomplete
    input.addEventListener("input", (e) => {
        clearTimeout(autocompleteTimeout);
        const val = e.target.value.trim();
        if (val.length < 1) {
            closeDropdown();
            return;
        }
        autocompleteTimeout = setTimeout(() => fetchSuggestions(val), 200);
    });

    // Enter key
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            const val = input.value.trim();
            if (val) triggerSearch(val);
        }
        if (e.key === "Escape") closeDropdown();
    });

    // Search button
    btn.addEventListener("click", () => {
        const val = input.value.trim();
        if (val) triggerSearch(val);
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", (e) => {
        if (!e.target.closest("#search-container")) closeDropdown();
    });
}

async function fetchSuggestions(query) {
    try {
        const res = await fetch(`/api/search-suggest?q=${encodeURIComponent(query)}`);
        if (!res.ok) return;
        const data = await res.json();
        renderDropdown(data.suggestions);
    } catch (e) {
        closeDropdown();
    }
}

function renderDropdown(suggestions) {
    const dropdown = document.getElementById("autocomplete-dropdown");
    dropdown.innerHTML = "";

    if (!suggestions || suggestions.length === 0) {
        dropdown.innerHTML = `<div class="ac-empty"><i class="fa-solid fa-circle-info"></i> No S&P 500 matches found</div>`;
        dropdown.classList.add("open");
        return;
    }

    suggestions.forEach(s => {
        const item = document.createElement("div");
        item.className = "ac-item";
        item.innerHTML = `
            <div class="ac-symbol mono">${s.symbol}</div>
            <div class="ac-name">${s.name}</div>
        `;
        item.addEventListener("click", () => {
            document.getElementById("ticker-input").value = s.symbol;
            closeDropdown();
            triggerSearch(s.symbol);
        });
        dropdown.appendChild(item);
    });

    dropdown.classList.add("open");
}

function closeDropdown() {
    const dropdown = document.getElementById("autocomplete-dropdown");
    dropdown.classList.remove("open");
    dropdown.innerHTML = "";
}

function triggerSearch(query) {
    closeDropdown();
    currentTicker = query.toUpperCase();
    document.getElementById("ticker-input").value = query.toUpperCase();
    runFullPipeline();
}

// ===== QUICK CHIPS =====
function initQuickChips() {
    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const ticker = chip.dataset.ticker;
            document.getElementById("ticker-input").value = ticker;
            triggerSearch(ticker);
        });
    });
}

// ===== TIMEFRAME BUTTONS =====
function initTimeframeSelectors() {
    document.querySelectorAll(".tf-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".tf-btn").forEach(b => b.classList.remove("active"));
            e.target.classList.add("active");
            currentPeriod = e.target.dataset.period;
            fetchAndRenderPriceChart();
        });
    });
}

// ===== SLIDERS =====
function initSliders() {
    [
        { id: "n-estimators", valId: "n-estimators-val", fmt: v => v },
        { id: "min-split", valId: "min-split-val", fmt: v => v },
        { id: "conf-threshold", valId: "conf-threshold-val", fmt: v => parseFloat(v).toFixed(2) }
    ].forEach(({ id, valId, fmt }) => {
        const el = document.getElementById(id);
        const val = document.getElementById(valId);
        el.addEventListener("input", () => { val.textContent = fmt(el.value); });
    });
}

// ===== FORM =====
function initForm() {
    document.getElementById("config-form").addEventListener("submit", (e) => {
        e.preventDefault();
        runFullPipeline();
    });
}

// ===== LOADER =====
function updateTimelinePills(step) {
    // Clear active class from all pills
    document.querySelectorAll(".loader-timeline .timeline-item").forEach(el => {
        el.classList.remove("active");
    });
    
    let activeId = "";
    if (step === 0 || step === 1) {
        activeId = "tl-step-thinking";
    } else if (step === 2) {
        activeId = "tl-step-grep";
    } else if (step === 3) {
        activeId = "tl-step-read";
    } else if (step === 4 || step === 5 || step === 6) {
        activeId = "tl-step-edit";
    } else if (step === 7) {
        activeId = "tl-step-done";
    }
    
    const activeEl = document.getElementById(activeId);
    if (activeEl) {
        activeEl.classList.add("active");
    }
}

function showLoader(ticker) {
    isLoading = true;
    const overlay = document.getElementById("loader-overlay");
    const title = document.getElementById("loader-title");
    const msg = document.getElementById("loader-message");
    const progress = document.getElementById("loader-progress");
    const tickerLabel = document.getElementById("loader-ticker-label");

    overlay.classList.remove("hidden");
    loaderStep = 0;
    title.textContent = LOADING_STEPS[0].title;
    msg.textContent = LOADING_STEPS[0].msg;
    progress.style.width = "5%";
    tickerLabel.textContent = ticker;
    updateTimelinePills(0);

    loaderInterval = setInterval(() => {
        loaderStep = (loaderStep + 1) % LOADING_STEPS.length;
        title.textContent = LOADING_STEPS[loaderStep].title;
        msg.textContent = LOADING_STEPS[loaderStep].msg;
        const pct = Math.min(90, Math.round((loaderStep / (LOADING_STEPS.length - 1)) * 88) + 5);
        progress.style.width = `${pct}%`;
        updateTimelinePills(loaderStep);
    }, 1600);
}

function hideLoader() {
    clearInterval(loaderInterval);
    updateTimelinePills(7);
    const overlay = document.getElementById("loader-overlay");
    const progress = document.getElementById("loader-progress");
    progress.style.width = "100%";
    setTimeout(() => overlay.classList.add("hidden"), 400);
    isLoading = false;
}

// ===== ERROR TOAST =====
function showError(msg) {
    const toast = document.getElementById("error-toast");
    document.getElementById("error-toast-msg").textContent = msg;
    toast.classList.remove("hidden");
    setTimeout(() => toast.classList.add("hidden"), 6000);
}

// ===== MAIN PIPELINE =====
async function runFullPipeline() {
    if (isLoading) return;
    showLoader(currentTicker);

    try {
        // Show results section
        const resultsSection = document.getElementById("results-section");
        resultsSection.classList.remove("hidden");

        // Run all fetches concurrently
        const [infoResult, priceResult, predResult] = await Promise.allSettled([
            fetchStockInfo(),
            fetchAndRenderPriceChart(),
            retrainAndForecast()
        ]);

        // Handle errors per request
        if (infoResult.status === "rejected") {
            console.error("Stock info failed:", infoResult.reason);
        }
        if (priceResult.status === "rejected") {
            console.error("Price chart failed:", priceResult.reason);
        }
        if (predResult.status === "rejected") {
            const err = predResult.reason;
            // Check if it's an S&P 500 rejection
            if (err.message && err.message.includes("not an S&P 500")) {
                showError(`❌ ${err.message}`);
            } else {
                showError(`Prediction failed: ${err.message || "Unknown error"}`);
            }
        }

        // Scroll to results smoothly
        setTimeout(() => {
            document.getElementById("results-section").scrollIntoView({ behavior: "smooth", block: "start" });
        }, 200);

        // Re-trigger scroll reveal animations
        setTimeout(() => {
            document.querySelectorAll(".reveal").forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.top < window.innerHeight) {
                    el.classList.add("active");
                }
            });
        }, 600);

    } catch (e) {
        console.error("Pipeline error:", e);
        showError("Something went wrong. Please try again.");
    } finally {
        hideLoader();
    }
}

// ===== FETCH STOCK INFO =====
async function fetchStockInfo() {
    const res = await fetch(`/api/stock-info?ticker=${encodeURIComponent(currentTicker)}`);
    if (!res.ok) throw new Error("Failed to fetch stock info");
    const data = await res.json();

    // Symbol & name
    document.getElementById("stock-symbol-badge").textContent = data.symbol;
    document.getElementById("stock-full-name").textContent = data.name;

    // Data source badge
    const badge = document.getElementById("data-source-badge");
    const dot = badge.querySelector(".ds-dot");
    const label = document.getElementById("ds-label");
    if (data.data_source === "live") {
        dot.className = "ds-dot live";
        label.textContent = "Live Data";
        badge.className = "data-source-badge live";
    } else {
        dot.className = "ds-dot sim";
        label.textContent = "Simulation Mode";
        badge.className = "data-source-badge sim";
    }

    // Price & change
    const currency = data.currency || "USD";
    const symbol = currency === "USD" ? "$" : "";
    const priceStr = `${symbol}${data.current_price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById("live-price").textContent = priceStr;

    const changeEl = document.getElementById("live-change");
    const sign = data.change >= 0 ? "+" : "";
    changeEl.textContent = `${sign}${data.change.toFixed(2)} (${sign}${data.pct_change.toFixed(2)}%)`;
    changeEl.className = `stat-change ${data.change >= 0 ? "up" : "down"}`;

    // OHLCV
    document.getElementById("stock-open").textContent = `${symbol}${data.open.toLocaleString("en-US", { minimumFractionDigits: 2 })}`;
    document.getElementById("stock-high").textContent = `${symbol}${data.high.toLocaleString("en-US", { minimumFractionDigits: 2 })}`;
    document.getElementById("stock-low").textContent = `${symbol}${data.low.toLocaleString("en-US", { minimumFractionDigits: 2 })}`;
    document.getElementById("stock-volume").textContent = data.volume.toLocaleString("en-US");

    // 52-week range
    if (data.week52_low !== undefined && data.week52_high !== undefined) {
        const low52 = data.week52_low;
        const high52 = data.week52_high;
        const current = data.current_price;
        const pct = Math.min(100, Math.max(0, ((current - low52) / (high52 - low52)) * 100));

        document.getElementById("week52-low").textContent = `${symbol}${low52.toFixed(2)}`;
        document.getElementById("week52-high").textContent = `${symbol}${high52.toFixed(2)}`;
        document.getElementById("week52-bar").style.width = `${pct}%`;
    }
}

// ===== FETCH & RENDER PRICE CHART =====
async function fetchAndRenderPriceChart() {
    const res = await fetch(`/api/stock-data?ticker=${encodeURIComponent(currentTicker)}&period=${currentPeriod}`);
    if (!res.ok) throw new Error("Failed to fetch price data");
    const data = await res.json();

    // Update chart note
    const note = document.getElementById("chart-data-note");
    if (data.data_source === "simulation") {
        note.textContent = "⚠️ Simulation data (Yahoo Finance unavailable)";
        note.className = "panel-sub sim-note";
    } else {
        note.textContent = "Real-time data from Yahoo Finance";
        note.className = "panel-sub";
    }

    renderPriceChart(data.prices);
}

function renderPriceChart(prices) {
    const ctx = document.getElementById("priceChart").getContext("2d");

    const labels = prices.map(p => p.date);
    const closes = prices.map(p => p.close);

    if (priceChart) priceChart.destroy();

    const gradient = ctx.createLinearGradient(0, 0, 0, 400);

    // Determine if overall trend is up or down
    const trendUp = closes.length > 1 && closes[closes.length - 1] >= closes[0];
    const lineColor = trendUp ? "#00a87e" : "#e23b4a"; // Teal vs Danger
    gradient.addColorStop(0, trendUp ? "rgba(0, 168, 126, 0.08)" : "rgba(226, 59, 74, 0.08)");
    gradient.addColorStop(1, "rgba(0,0,0,0)");

    const gridColor = "rgba(255, 255, 255, 0.12)";
    const tickColor = "rgba(255, 255, 255, 0.72)";

    priceChart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Close Price",
                data: closes,
                borderColor: lineColor,
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 5,
                pointHoverBackgroundColor: lineColor,
                pointHoverBorderColor: "#fff",
                pointHoverBorderWidth: 2,
                fill: true,
                backgroundColor: gradient,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#16181a",
                    titleColor: "rgba(255, 255, 255, 0.72)",
                    bodyColor: "#ffffff",
                    borderColor: "rgba(255, 255, 255, 0.12)",
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: ctx => ` $${ctx.parsed.y.toLocaleString("en-US", { minimumFractionDigits: 2 })}`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: gridColor },
                    ticks: { color: tickColor, maxTicksLimit: 8, font: { family: "Inter", size: 11 } }
                },
                y: {
                    grid: { color: gridColor },
                    ticks: {
                        color: tickColor,
                        font: { family: "JetBrains Mono", size: 11 },
                        callback: v => `$${v.toLocaleString("en-US", { minimumFractionDigits: 0 })}`
                    }
                }
            }
        }
    });
}

// ===== RETRAIN & FORECAST =====
async function retrainAndForecast() {
    const payload = {
        ticker: currentTicker,
        n_estimators: parseInt(document.getElementById("n-estimators").value),
        min_samples_split: parseInt(document.getElementById("min-split").value),
        confidence_threshold: parseFloat(document.getElementById("conf-threshold").value),
        horizons: document.getElementById("rolling-horizons").value.split(",").map(x => parseInt(x.trim())).filter(x => !isNaN(x)),
        use_rolling_predictors: document.getElementById("use-rolling").checked
    };

    const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Prediction API failed");
    }

    const data = await res.json();
    updateForecastCard(data);
    updateAccuracyCard(data);
    renderReasonsPanel(data.reasons || []);
    updateBacktestMetrics(data.metrics);
    renderBacktestChart(data.backtest_history, payload.confidence_threshold);
}

// ===== FORECAST CARD =====
function updateForecastCard(data) {
    const f = data.forecast;
    const prob = f.probability;
    const threshold = f.confidence_threshold;
    const lowerBound = 1.0 - threshold;

    let state = "neutral"; // "bullish", "neutral", "bearish"
    if (prob >= threshold) {
        state = "bullish";
    } else if (prob <= lowerBound) {
        state = "bearish";
    }

    document.getElementById("as-of-date").textContent = f.as_of_date;
    document.getElementById("lbl-threshold-stat").textContent = `${Math.round(threshold * 100)}%`;

    const dirEl = document.getElementById("pred-direction");
    const badge = document.getElementById("signal-badge");
    const arrow = document.getElementById("direction-arrow");
    const box = document.getElementById("forecast-direction-box");

    if (state === "bullish") {
        dirEl.textContent = "BULLISH";
        dirEl.className = "direction-main bullish";
        badge.textContent = "BUY SIGNAL";
        badge.className = "forecast-badge bull";
        arrow.innerHTML = '<i class="fa-solid fa-arrow-trend-up"></i>';
        arrow.className = "direction-arrow up";
        box.className = "forecast-direction bull";
    } else if (state === "bearish") {
        dirEl.textContent = "BEARISH";
        dirEl.className = "direction-main bearish";
        badge.textContent = "SELL / AVOID";
        badge.className = "forecast-badge bear";
        arrow.innerHTML = '<i class="fa-solid fa-arrow-trend-down"></i>';
        arrow.className = "direction-arrow down";
        box.className = "forecast-direction bear";
    } else {
        dirEl.textContent = "NEUTRAL";
        dirEl.className = "direction-main neutral";
        badge.textContent = "HOLD / WAIT";
        badge.className = "forecast-badge neutral";
        arrow.innerHTML = '<i class="fa-solid fa-arrow-right"></i>';
        arrow.className = "direction-arrow neutral";
        box.className = "forecast-direction neutral";
    }

    // Gauge
    const pct = Math.round(prob * 100);
    document.getElementById("gauge-percentage").textContent = `${pct}%`;
    const circumference = 2 * Math.PI * 50; // r=50
    const offset = circumference - (circumference * prob);
    const gaugeFg = document.getElementById("gauge-fg");
    gaugeFg.style.strokeDasharray = circumference;
    gaugeFg.style.strokeDashoffset = offset;

    if (prob >= threshold) {
        gaugeFg.style.stroke = "#00a87e"; // Accent Teal
    } else if (prob <= lowerBound) {
        gaugeFg.style.stroke = "#e23b4a"; // Accent Danger
    } else {
        gaugeFg.style.stroke = "#b09000"; // Accent Yellow
    }
}

// ===== ACCURACY CARD =====
function updateAccuracyCard(data) {
    const m = data.metrics;
    const precPct = (m.precision * 100).toFixed(1);
    const basePct = (m.baseline_precision * 100).toFixed(1);

    document.getElementById("metric-precision").textContent = `${precPct}%`;
    document.getElementById("metric-baseline").textContent = `${basePct}%`;

    // Bar fill
    document.getElementById("acc-bar-fill").style.width = `${precPct}%`;
    // Baseline marker position
    document.getElementById("acc-baseline-marker").style.left = `${basePct}%`;

    const diff = m.precision - m.baseline_precision;
    const sign = diff >= 0 ? "+" : "";
    const diffEl = document.getElementById("precision-comparison");
    diffEl.textContent = `${sign}${(diff * 100).toFixed(1)}% vs buy & hold`;
    diffEl.className = `acc-diff ${diff >= 0 ? "positive" : "negative"}`;
}

// ===== REASONS PANEL =====
function renderReasonsPanel(reasons) {
    const grid = document.getElementById("reasons-grid");
    grid.innerHTML = "";

    if (!reasons || reasons.length === 0) {
        grid.innerHTML = `<p class="no-reasons">No reasoning data available for this prediction.</p>`;
        return;
    }

    const signalConfig = {
        "bullish": { cls: "bull", icon: "fa-arrow-trend-up", label: "Bullish Signal" },
        "neutral-bullish": { cls: "neutral-bull", icon: "fa-minus", label: "Mild Bullish" },
        "neutral-bearish": { cls: "neutral-bear", icon: "fa-minus", label: "Mild Bearish" },
        "bearish": { cls: "bear", icon: "fa-arrow-trend-down", label: "Bearish Signal" }
    };

    reasons.forEach((r, i) => {
        const cfg = signalConfig[r.signal] || signalConfig["neutral-bullish"];
        const card = document.createElement("div");
        card.className = `reason-card ${cfg.cls}`;
        card.style.animationDelay = `${i * 0.08}s`;
        card.innerHTML = `
            <div class="reason-top">
                <div class="reason-icon-wrapper">
                    <div class="reason-icon ${cfg.cls}">
                        <i class="fa-solid ${cfg.icon}"></i>
                    </div>
                    <div class="reason-header-text">
                        <span class="reason-factor">${r.factor}</span>
                        <span class="reason-signal-label ${cfg.cls}">${cfg.label}</span>
                    </div>
                </div>
                <div class="reason-importance">
                    <span class="imp-value mono">${r.importance}%</span>
                    <span class="imp-label">importance</span>
                </div>
            </div>
            <div class="reason-body">
                <div class="reason-importance-bar">
                    <div class="imp-bar-fill ${cfg.cls}" style="width: ${Math.min(100, r.importance * 2)}%"></div>
                </div>
                <p class="reason-explanation">${r.explanation}</p>
                <div class="reason-value-row">
                    <span class="rv-label">Current Value</span>
                    <span class="rv-val mono">${r.current_value}</span>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

// ===== BACKTEST METRICS =====
function updateBacktestMetrics(m) {
    const precPct = (m.precision * 100).toFixed(1);
    const basePct = (m.baseline_precision * 100).toFixed(1);
    const diff = m.precision - m.baseline_precision;
    const sign = diff >= 0 ? "+" : "";

    document.getElementById("bt-precision").textContent = `${precPct}%`;
    document.getElementById("bt-baseline").textContent = `${basePct}%`;
    document.getElementById("bt-days").textContent = m.total_eval_days.toLocaleString();

    const diffEl = document.getElementById("bt-precision-diff");
    diffEl.textContent = `${sign}${(diff * 100).toFixed(1)}% vs baseline`;
    diffEl.className = `metric-diff ${diff >= 0 ? "positive" : "negative"}`;

    const total = m.bullish_predictions + m.bearish_predictions;
    const bullPct = total > 0 ? (m.bullish_predictions / total) * 100 : 50;
    const bearPct = total > 0 ? (m.bearish_predictions / total) * 100 : 50;

    document.getElementById("split-bullish-bar").style.width = `${bullPct}%`;
    document.getElementById("split-bearish-bar").style.width = `${bearPct}%`;
    document.getElementById("prediction-split-text").textContent =
        `Bullish: ${m.bullish_predictions} (${bullPct.toFixed(0)}%) | Bearish: ${m.bearish_predictions} (${bearPct.toFixed(0)}%)`;
}

// ===== BACKTEST CHART =====
function renderBacktestChart(history, threshold) {
    const ctx = document.getElementById("backtestChart").getContext("2d");

    if (backtestChart) backtestChart.destroy();

    const labels = history.map(h => h.date);
    const probs = history.map(h => h.probability * 100);
    const classifications = history.map(h => ({
        correct: h.predicted === h.actual,
        value: h.probability * 100,
        actual: h.actual
    }));

    const pointColors = classifications.map(c => {
        if (c.correct) {
            return "#00a87e"; // Teal
        } else {
            return "#e23b4a"; // Danger/Pink
        }
    });
    const pointRadii = classifications.map(c => c.correct ? 3 : 4);

    const gridColor = "rgba(255, 255, 255, 0.12)";
    const tickColor = "rgba(255, 255, 255, 0.72)";

    backtestChart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Prediction Probability %",
                data: probs,
                borderColor: "rgba(73, 79, 223, 0.4)", // Cobalt violet line color
                borderWidth: 1.5,
                pointBackgroundColor: pointColors,
                pointBorderColor: "transparent",
                pointRadius: pointRadii,
                pointHoverRadius: 7,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#16181a",
                    titleColor: "rgba(255, 255, 255, 0.72)",
                    bodyColor: "#ffffff",
                    borderColor: "rgba(255, 255, 255, 0.12)",
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: (context) => {
                            const idx = context.dataIndex;
                            const c = classifications[idx];
                            return [
                                `Probability: ${Math.round(c.value)}%`,
                                `Market: ${c.actual === 1 ? "▲ UP" : "▼ DOWN"}`,
                                `Result: ${c.correct ? "✓ HIT" : "✗ MISS"}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: gridColor },
                    ticks: { color: tickColor, maxTicksLimit: 10, font: { family: "Inter", size: 11 } }
                },
                y: {
                    min: 0, max: 100,
                    grid: { color: gridColor },
                    ticks: {
                        color: tickColor,
                        font: { family: "JetBrains Mono", size: 11 },
                        callback: v => `${v}%`
                    }
                }
            }
        }
    });

    setTimeout(updateChartThemes, 50);
}

// ===== CHART THEME UPDATE =====
function updateChartThemes() {
    const gridColor = "rgba(255, 255, 255, 0.12)";
    const tickColor = "rgba(255, 255, 255, 0.72)";
    const tooltipBg = "#16181a";
    const tooltipBorder = "rgba(255, 255, 255, 0.12)";
    const tooltipBody = "#ffffff";
    const tooltipTitle = "rgba(255, 255, 255, 0.72)";

    [priceChart, backtestChart].forEach(chart => {
        if (!chart) return;
        chart.options.scales.x.grid.color = gridColor;
        chart.options.scales.x.ticks.color = tickColor;
        chart.options.scales.y.grid.color = gridColor;
        chart.options.scales.y.ticks.color = tickColor;
        chart.options.plugins.tooltip.backgroundColor = tooltipBg;
        chart.options.plugins.tooltip.borderColor = tooltipBorder;
        chart.options.plugins.tooltip.bodyColor = tooltipBody;
        chart.options.plugins.tooltip.titleColor = tooltipTitle;
        chart.options.plugins.tooltip.borderWidth = 1;
        
        // Dynamic re-coloring of lines/points
        if (chart === priceChart && chart.data.datasets.length > 0) {
            const dataset = chart.data.datasets[0];
            const closes = dataset.data;
            const trendUp = closes.length > 1 && closes[closes.length - 1] >= closes[0];
            const lineColor = trendUp ? "#00a87e" : "#e23b4a";
            
            dataset.borderColor = lineColor;
            dataset.pointHoverBackgroundColor = lineColor;
            
            const ctx = document.getElementById("priceChart").getContext("2d");
            const gradient = ctx.createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, trendUp ? "rgba(0, 168, 126, 0.08)" : "rgba(226, 59, 74, 0.08)");
            gradient.addColorStop(1, "rgba(0,0,0,0)");
            dataset.backgroundColor = gradient;
        }

        chart.update();
    });
}
