import maplibregl from 'maplibre-gl';
import * as d3 from 'd3';
import scrollama from 'scrollama';
import { PMTiles, Protocol } from 'pmtiles';

// Configuration
const CONFIG = {
    mapStyle: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
    dataUrl: './assets/counties_esda.geojson',
    tilesUrl: './assets/counties.pmtiles',
    initialView: {
        center: [-98.5795, 39.8283],
        zoom: 4,
        pitch: 0,
        bearing: 0
    },
    colors: {
        distress: ['#2166ac', '#4393c3', '#92c5de', '#d1e5f0', '#fddbc7', '#f4a582', '#d6604d', '#b2182b'],
        trump: ['#0571b0', '#92c5de', '#f7f7f7', '#f4a582', '#ca0020'],
        bivariate: {
            'HH': '#d62728',
            'HL': '#ff9896',
            'LH': '#9edae5',
            'LL': '#1f77b4',
            'Not Significant': '#7f7f7f'
        },
        hotspot: {
            'Hot Spot - 99% Conf': '#b30000',
            'Hot Spot - 95% Conf': '#e34a33',
            'Hot Spot - 90% Conf': '#fc8d59',
            'Not Significant': '#ffffcc',
            'Cold Spot - 90% Conf': '#91bfdb',
            'Cold Spot - 95% Conf': '#4575b4',
            'Cold Spot - 99% Conf': '#253494'
        }
    }
};

// State management
let map;
let countyData;
let currentStep = 'intro';
let scroller;

// Initialize the application
async function init() {
    await loadData();
    initMap();
    initScrollama();
    setupEventHandlers();
}

// Load data
async function loadData() {
    try {
        const response = await fetch(CONFIG.dataUrl);
        countyData = await response.json();
        console.log('Data loaded:', countyData.features.length, 'counties');
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

// Initialize map
function initMap() {
    // Add PMTiles protocol if using tiles
    // const protocol = new Protocol();
    // maplibregl.addProtocol('pmtiles', protocol);

    map = new maplibregl.Map({
        container: 'map',
        style: CONFIG.mapStyle,
        center: CONFIG.initialView.center,
        zoom: CONFIG.initialView.zoom,
        pitch: CONFIG.initialView.pitch,
        bearing: CONFIG.initialView.bearing
    });

    map.on('load', () => {
        addDataLayers();
        setupMapInteractions();
    });
}

// Add data layers to map
function addDataLayers() {
    // Add county data source
    map.addSource('counties', {
        type: 'geojson',
        data: countyData
    });

    // Add fill layer for counties
    map.addLayer({
        id: 'counties-fill',
        type: 'fill',
        source: 'counties',
        paint: {
            'fill-color': '#ffffff',
            'fill-opacity': 0.7
        }
    }, 'waterway-label');

    // Add outline layer
    map.addLayer({
        id: 'counties-outline',
        type: 'line',
        source: 'counties',
        paint: {
            'line-color': '#ffffff',
            'line-width': 0.5,
            'line-opacity': 0.3
        }
    }, 'waterway-label');

    // Add highlight layer for hover
    map.addLayer({
        id: 'counties-highlight',
        type: 'line',
        source: 'counties',
        paint: {
            'line-color': '#667eea',
            'line-width': 2,
            'line-opacity': 0
        }
    }, 'waterway-label');
}

// Setup map interactions
function setupMapInteractions() {
    // Hover effect
    map.on('mousemove', 'counties-fill', (e) => {
        if (e.features.length > 0) {
            map.getCanvas().style.cursor = 'pointer';

            // Highlight county
            map.setFilter('counties-highlight', ['==', 'fips', e.features[0].properties.fips]);
            map.setPaintProperty('counties-highlight', 'line-opacity', 1);
        }
    });

    map.on('mouseleave', 'counties-fill', () => {
        map.getCanvas().style.cursor = '';
        map.setPaintProperty('counties-highlight', 'line-opacity', 0);
    });

    // Click to show info card
    map.on('click', 'counties-fill', (e) => {
        if (e.features.length > 0) {
            showInfoCard(e.features[0].properties);
        }
    });
}

// Initialize Scrollama
function initScrollama() {
    scroller = scrollama();

    scroller
        .setup({
            step: '.step',
            offset: 0.5,
            progress: true
        })
        .onStepEnter(handleStepEnter)
        .onStepProgress(handleStepProgress)
        .onStepExit(handleStepExit);

    // Handle resize
    window.addEventListener('resize', scroller.resize);
}

// Handle step enter
function handleStepEnter(response) {
    const step = response.element.dataset.step;
    currentStep = step;

    // Update visualization based on step
    switch(step) {
        case 'intro':
            showIntro();
            break;
        case 'distress-map':
            showDistressMap();
            break;
        case 'trump-2016':
            showTrumpMap2016();
            break;
        case 'bivariate':
            showBivariateAnalysis();
            break;
        case 'overdose':
            showOverdoseMap();
            break;
        case 'hotspots':
            showHotspots();
            break;
        case 'model-results':
            showModelResults();
            break;
        case 'caveats':
            showCaveats();
            break;
    }
}

// Handle step progress
function handleStepProgress(response) {
    // Could use for animations during scroll
}

// Handle step exit
function handleStepExit(response) {
    // Clean up if needed
}

// Visualization functions for each step
function showIntro() {
    // Reset to initial view
    map.flyTo({
        center: CONFIG.initialView.center,
        zoom: CONFIG.initialView.zoom,
        pitch: 0,
        bearing: 0,
        duration: 2000
    });

    // Set neutral colors
    map.setPaintProperty('counties-fill', 'fill-color', '#444444');
    map.setPaintProperty('counties-fill', 'fill-opacity', 0.3);

    hideLegend();
    hideCharts();
}

function showDistressMap() {
    // Update map to show physical distress
    const colorScale = d3.scaleQuantile()
        .domain(countyData.features.map(d => d.properties.freq_phys_distress_pct))
        .range(CONFIG.colors.distress);

    map.setPaintProperty('counties-fill', 'fill-color', [
        'interpolate',
        ['linear'],
        ['get', 'freq_phys_distress_pct'],
        10, CONFIG.colors.distress[0],
        15, CONFIG.colors.distress[2],
        20, CONFIG.colors.distress[4],
        25, CONFIG.colors.distress[6],
        30, CONFIG.colors.distress[7]
    ]);
    map.setPaintProperty('counties-fill', 'fill-opacity', 0.8);

    showLegend('Frequent Physical Distress (%)', CONFIG.colors.distress, [10, 15, 20, 25, 30]);
}

function showTrumpMap2016() {
    // Update map to show Trump 2016 vote share
    map.setPaintProperty('counties-fill', 'fill-color', [
        'interpolate',
        ['linear'],
        ['get', 'trump_share_2016'],
        20, CONFIG.colors.trump[0],
        40, CONFIG.colors.trump[1],
        50, CONFIG.colors.trump[2],
        60, CONFIG.colors.trump[3],
        80, CONFIG.colors.trump[4]
    ]);
    map.setPaintProperty('counties-fill', 'fill-opacity', 0.8);

    showLegend('Trump Vote Share 2016 (%)', CONFIG.colors.trump, [20, 40, 50, 60, 80]);
}

function showBivariateAnalysis() {
    // Show bivariate LISA clusters
    const bivariateExpression = ['match', ['get', 'bv_cluster']];

    for (const [cluster, color] of Object.entries(CONFIG.colors.bivariate)) {
        bivariateExpression.push(cluster, color);
    }
    bivariateExpression.push('#cccccc'); // default

    map.setPaintProperty('counties-fill', 'fill-color', bivariateExpression);
    map.setPaintProperty('counties-fill', 'fill-opacity', 0.9);

    showBivariateLegend();
    showScatterPlot();
}

function showOverdoseMap() {
    // Update map to show overdose rates
    map.setPaintProperty('counties-fill', 'fill-color', [
        'interpolate',
        ['linear'],
        ['get', 'od_1316_rate'],
        0, '#fee5d9',
        10, '#fcbba1',
        20, '#fc9272',
        30, '#fb6a4a',
        40, '#de2d26',
        50, '#a50f15'
    ]);
    map.setPaintProperty('counties-fill', 'fill-opacity', 0.8);

    showLegend('Overdose Rate (per 100k)', ['#fee5d9', '#fc9272', '#fb6a4a', '#a50f15'], [0, 20, 40, 60]);
}

function showHotspots() {
    // Show hot spot analysis results
    const hotspotExpression = ['match', ['get', 'trump_share_2016_hotspot_conf']];

    for (const [category, color] of Object.entries(CONFIG.colors.hotspot)) {
        hotspotExpression.push(category, color);
    }
    hotspotExpression.push('#cccccc'); // default

    map.setPaintProperty('counties-fill', 'fill-color', hotspotExpression);
    map.setPaintProperty('counties-fill', 'fill-opacity', 0.9);

    showHotspotLegend();
}

function showModelResults() {
    // Show model results with charts
    showCharts();
    showCoefficientsChart();
}

function showCaveats() {
    // Fade map slightly to focus on text
    map.setPaintProperty('counties-fill', 'fill-opacity', 0.3);
    hideLegend();
    hideCharts();
}

// Legend functions
function showLegend(title, colors, breaks) {
    const legend = document.getElementById('legend');
    const content = document.getElementById('legend-content');

    content.innerHTML = '';

    colors.forEach((color, i) => {
        const item = document.createElement('div');
        item.className = 'legend-item';

        const colorBox = document.createElement('div');
        colorBox.className = 'legend-color';
        colorBox.style.backgroundColor = color;

        const label = document.createElement('span');
        if (breaks && breaks[i] !== undefined) {
            label.textContent = breaks[i] + (breaks[i + 1] ? '-' + breaks[i + 1] : '+');
        }

        item.appendChild(colorBox);
        item.appendChild(label);
        content.appendChild(item);
    });

    legend.style.display = 'block';
}

function showBivariateLegend() {
    const legend = document.getElementById('legend');
    const content = document.getElementById('legend-content');

    content.innerHTML = '';

    const categories = [
        { key: 'HH', label: 'High-High', color: CONFIG.colors.bivariate.HH },
        { key: 'LL', label: 'Low-Low', color: CONFIG.colors.bivariate.LL },
        { key: 'HL', label: 'High-Low', color: CONFIG.colors.bivariate.HL },
        { key: 'LH', label: 'Low-High', color: CONFIG.colors.bivariate.LH },
        { key: 'Not Significant', label: 'Not Significant', color: CONFIG.colors.bivariate['Not Significant'] }
    ];

    categories.forEach(cat => {
        const item = document.createElement('div');
        item.className = 'legend-item';

        const colorBox = document.createElement('div');
        colorBox.className = 'legend-color';
        colorBox.style.backgroundColor = cat.color;

        const label = document.createElement('span');
        label.textContent = cat.label;

        item.appendChild(colorBox);
        item.appendChild(label);
        content.appendChild(item);
    });

    legend.style.display = 'block';
}

function showHotspotLegend() {
    showLegend('Hot Spot Analysis',
        Object.values(CONFIG.colors.hotspot),
        Object.keys(CONFIG.colors.hotspot));
}

function hideLegend() {
    document.getElementById('legend').style.display = 'none';
}

// Chart functions
function showCharts() {
    document.getElementById('charts-overlay').style.display = 'block';
}

function hideCharts() {
    document.getElementById('charts-overlay').style.display = 'none';
}

function showScatterPlot() {
    // D3 scatter plot implementation
    const container = d3.select('#scatter-plot');
    container.html(''); // Clear previous

    // Implementation would go here
    // This is a placeholder
    container.append('div')
        .attr('class', 'chart-title')
        .text('Distress vs Trump Support');
}

function showCoefficientsChart() {
    // D3 coefficient plot implementation
    const container = d3.select('#bar-chart');
    container.html(''); // Clear previous

    // Implementation would go here
    // This is a placeholder
    container.append('div')
        .attr('class', 'chart-title')
        .text('Model Coefficients');
}

// Info card functions
function showInfoCard(properties) {
    const card = document.getElementById('info-card');
    const nameEl = document.getElementById('county-name');
    const statsEl = document.getElementById('county-stats');

    nameEl.textContent = properties.NAME || 'Unknown County';

    // Build stats HTML
    const stats = [
        { label: 'Trump 2016', value: (properties.trump_share_2016 || 0).toFixed(1) + '%' },
        { label: 'Trump 2020', value: (properties.trump_share_2020 || 0).toFixed(1) + '%' },
        { label: 'Physical Distress', value: (properties.freq_phys_distress_pct || 0).toFixed(1) + '%' },
        { label: 'Overdose Rate', value: (properties.od_1316_rate || 0).toFixed(1) },
        { label: 'Rural', value: properties.rural === 1 ? 'Yes' : 'No' }
    ];

    statsEl.innerHTML = stats.map(stat => `
        <div class="stat-row">
            <span class="stat-label">${stat.label}:</span>
            <span class="stat-value">${stat.value}</span>
        </div>
    `).join('');

    card.classList.remove('hidden');
}

window.closeInfoCard = function() {
    document.getElementById('info-card').classList.add('hidden');
};

// Setup event handlers
function setupEventHandlers() {
    // Add any additional event handlers here
}

// Start the application
document.addEventListener('DOMContentLoaded', init);