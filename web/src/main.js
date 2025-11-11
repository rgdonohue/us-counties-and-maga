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
    if (countyData && countyData.features) {
        initMap();
        initScrollama();
        setupEventHandlers();
    } else {
        console.error('Failed to load data, cannot initialize map');
    }
}

// Data validation and schema checking
function validateDataSchema(data) {
    const warnings = [];
    const errors = [];
    
    if (!data || !data.features || data.features.length === 0) {
        errors.push('GeoJSON has no features');
        return { valid: false, errors, warnings };
    }
    
    // Check required fields
    const requiredFields = ['fips', 'NAME'];
    const sampleFeature = data.features[0];
    
    requiredFields.forEach(field => {
        if (!(field in sampleFeature.properties)) {
            errors.push(`Missing required field: ${field}`);
        }
    });
    
    // Check expected fields (warn if missing)
    const expectedFields = {
        'trump_share_2016': 'Electoral data',
        'freq_phys_distress_pct': 'Distress metrics',
        'bv_cluster': 'Bivariate LISA',
        'trump_share_2016_hotspot_conf': 'Hot spot analysis'
    };
    
    Object.entries(expectedFields).forEach(([field, category]) => {
        if (!(field in sampleFeature.properties)) {
            warnings.push(`Missing ${category} field: ${field} (visualization may be limited)`);
        }
    });
    
    // Validate bivariate cluster values
    if ('bv_cluster' in sampleFeature.properties) {
        const validBvValues = ['HH', 'HL', 'LH', 'LL', 'Not Significant'];
        const bvValues = new Set(data.features
            .map(f => f.properties.bv_cluster)
            .filter(v => v !== null && v !== undefined));
        
        bvValues.forEach(val => {
            if (!validBvValues.includes(val)) {
                warnings.push(`Unexpected bv_cluster value: "${val}"`);
            }
        });
    }
    
    return {
        valid: errors.length === 0,
        errors,
        warnings
    };
}

// Load data
async function loadData() {
    try {
        const response = await fetch(CONFIG.dataUrl);
        countyData = await response.json();
        console.log('Data loaded:', countyData.features.length, 'counties');
        
        // Validate schema
        const validation = validateDataSchema(countyData);
        if (!validation.valid) {
            console.error('Data validation errors:', validation.errors);
            alert('Data validation failed. Check console for details.');
            return;
        }
        
        if (validation.warnings.length > 0) {
            console.warn('Data validation warnings:', validation.warnings);
        }
        
        // Store data statistics for data-driven breaks
        computeDataStatistics();
    } catch (error) {
        console.error('Error loading data:', error);
        alert('Failed to load data. Check console for details.');
    }
}

// Compute data-driven statistics for breaks/legends
let dataStats = {};

function computeDataStatistics() {
    const features = countyData.features;
    
    // Helper to extract non-null values
    const getValues = (field) => features
        .map(f => f.properties[field])
        .filter(v => v !== null && v !== undefined && !isNaN(v));
    
    // Compute quantiles for continuous variables
    // d3.quantile takes sorted array and single probability, so map over probabilities
    const probabilities = [0, 0.2, 0.4, 0.6, 0.8, 1.0];
    
    const computeQuantiles = (field) => {
        const sortedValues = getValues(field).sort(d3.ascending);
        return probabilities.map(p => d3.quantile(sortedValues, p));
    };
    
    dataStats.distress = {
        values: getValues('freq_phys_distress_pct'),
        quantiles: computeQuantiles('freq_phys_distress_pct')
    };
    
    dataStats.trump2016 = {
        values: getValues('trump_share_2016'),
        quantiles: computeQuantiles('trump_share_2016')
    };
    
    dataStats.overdose = {
        values: getValues('od_1316_rate'),
        quantiles: computeQuantiles('od_1316_rate')
    };
    
    console.log('Data statistics computed:', dataStats);
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
    // Ensure data is loaded
    if (!countyData || !countyData.features) {
        console.error('County data not loaded, cannot add layers');
        return;
    }
    
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
        if (e.features.length > 0 && e.features[0].properties) {
            const props = e.features[0].properties;
            // Only highlight if FIPS exists
            if (props.fips) {
                map.getCanvas().style.cursor = 'pointer';
                map.setFilter('counties-highlight', ['==', 'fips', props.fips]);
                map.setPaintProperty('counties-highlight', 'line-opacity', 1);
            }
        }
    });

    map.on('mouseleave', 'counties-fill', () => {
        map.getCanvas().style.cursor = '';
        map.setPaintProperty('counties-highlight', 'line-opacity', 0);
    });

    // Click to show info card
    map.on('click', 'counties-fill', (e) => {
        if (e.features.length > 0 && e.features[0].properties) {
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
    // Check if field exists
    if (!dataStats.distress || dataStats.distress.values.length === 0) {
        console.warn('freq_phys_distress_pct not available, using fallback');
        map.setPaintProperty('counties-fill', 'fill-color', '#cccccc');
        map.setPaintProperty('counties-fill', 'fill-opacity', 0.3);
        return;
    }
    
    // Use data-driven quantiles
    const q = dataStats.distress.quantiles;
    const breaks = [q[0], q[1], q[2], q[3], q[4], q[5]];
    
    // Create color stops using quantiles
    map.setPaintProperty('counties-fill', 'fill-color', [
        'interpolate',
        ['linear'],
        ['get', 'freq_phys_distress_pct'],
        breaks[0], CONFIG.colors.distress[0],
        breaks[1], CONFIG.colors.distress[2],
        breaks[2], CONFIG.colors.distress[4],
        breaks[3], CONFIG.colors.distress[5],
        breaks[4], CONFIG.colors.distress[6],
        breaks[5], CONFIG.colors.distress[7]
    ]);
    
    // Handle null values with neutral color
    map.setPaintProperty('counties-fill', 'fill-opacity', [
        'case',
        ['has', 'freq_phys_distress_pct'],
        0.8,
        0.3  // Lower opacity for null counties
    ]);

    showLegend('Frequent Physical Distress (%)', CONFIG.colors.distress, breaks);
}

function showTrumpMap2016() {
    // Check if field exists
    if (!dataStats.trump2016 || dataStats.trump2016.values.length === 0) {
        console.warn('trump_share_2016 not available, using fallback');
        map.setPaintProperty('counties-fill', 'fill-color', '#cccccc');
        map.setPaintProperty('counties-fill', 'fill-opacity', 0.3);
        return;
    }
    
    // Use data-driven quantiles
    const q = dataStats.trump2016.quantiles;
    const breaks = [q[0], q[1], q[2], q[3], q[4], q[5]];
    
    // Create color stops using quantiles
    map.setPaintProperty('counties-fill', 'fill-color', [
        'interpolate',
        ['linear'],
        ['get', 'trump_share_2016'],
        breaks[0], CONFIG.colors.trump[0],
        breaks[1], CONFIG.colors.trump[1],
        breaks[2], CONFIG.colors.trump[2],
        breaks[3], CONFIG.colors.trump[3],
        breaks[4], CONFIG.colors.trump[4]
    ]);
    
    // Handle null values
    map.setPaintProperty('counties-fill', 'fill-opacity', [
        'case',
        ['has', 'trump_share_2016'],
        0.8,
        0.3
    ]);

    showLegend('Trump Vote Share 2016 (%)', CONFIG.colors.trump, breaks);
}

function showBivariateAnalysis() {
    // Check if bv_cluster field exists
    const sampleFeature = countyData.features.find(f => f.properties.bv_cluster);
    if (!sampleFeature) {
        console.warn('bv_cluster not available, using fallback');
        map.setPaintProperty('counties-fill', 'fill-color', '#cccccc');
        map.setPaintProperty('counties-fill', 'fill-opacity', 0.3);
        hideLegend();
        return;
    }
    
    // Show bivariate LISA clusters with null handling
    const bivariateExpression = [
        'case',
        ['has', 'bv_cluster'],
        ['match', ['get', 'bv_cluster'],
            'HH', CONFIG.colors.bivariate.HH,
            'HL', CONFIG.colors.bivariate.HL,
            'LH', CONFIG.colors.bivariate.LH,
            'LL', CONFIG.colors.bivariate.LL,
            'Not Significant', CONFIG.colors.bivariate['Not Significant'],
            '#cccccc'  // fallback for unexpected values
        ],
        '#e0e0e0'  // null values (lighter gray)
    ];

    map.setPaintProperty('counties-fill', 'fill-color', bivariateExpression);
    map.setPaintProperty('counties-fill', 'fill-opacity', [
        'case',
        ['has', 'bv_cluster'],
        0.9,
        0.3  // Lower opacity for null counties
    ]);

    showBivariateLegend();
    showScatterPlot();
}

function showOverdoseMap() {
    // Check if field exists
    if (!dataStats.overdose || dataStats.overdose.values.length === 0) {
        console.warn('od_1316_rate not available, using fallback');
        map.setPaintProperty('counties-fill', 'fill-color', '#cccccc');
        map.setPaintProperty('counties-fill', 'fill-opacity', 0.3);
        return;
    }
    
    // Use data-driven quantiles
    const q = dataStats.overdose.quantiles;
    const breaks = [q[0], q[1], q[2], q[3], q[4], q[5]];
    const colors = ['#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26', '#a50f15'];
    
    // Create color stops using quantiles
    map.setPaintProperty('counties-fill', 'fill-color', [
        'interpolate',
        ['linear'],
        ['get', 'od_1316_rate'],
        breaks[0], colors[0],
        breaks[1], colors[1],
        breaks[2], colors[2],
        breaks[3], colors[3],
        breaks[4], colors[4],
        breaks[5], colors[5]
    ]);
    
    // Handle null values
    map.setPaintProperty('counties-fill', 'fill-opacity', [
        'case',
        ['has', 'od_1316_rate'],
        0.8,
        0.3
    ]);

    showLegend('Overdose Rate (per 100k)', colors, breaks);
}

function showHotspots() {
    // Check if hotspot field exists
    const sampleFeature = countyData.features.find(f => f.properties.trump_share_2016_hotspot_conf);
    if (!sampleFeature) {
        console.warn('trump_share_2016_hotspot_conf not available, using fallback');
        map.setPaintProperty('counties-fill', 'fill-color', '#cccccc');
        map.setPaintProperty('counties-fill', 'fill-opacity', 0.3);
        hideLegend();
        return;
    }
    
    // Show hot spot analysis results with null handling
    const hotspotExpression = [
        'case',
        ['has', 'trump_share_2016_hotspot_conf'],
        ['match', ['get', 'trump_share_2016_hotspot_conf'],
            'Hot Spot - 99% Conf', CONFIG.colors.hotspot['Hot Spot - 99% Conf'],
            'Hot Spot - 95% Conf', CONFIG.colors.hotspot['Hot Spot - 95% Conf'],
            'Hot Spot - 90% Conf', CONFIG.colors.hotspot['Hot Spot - 90% Conf'],
            'Cold Spot - 90% Conf', CONFIG.colors.hotspot['Cold Spot - 90% Conf'],
            'Cold Spot - 95% Conf', CONFIG.colors.hotspot['Cold Spot - 95% Conf'],
            'Cold Spot - 99% Conf', CONFIG.colors.hotspot['Cold Spot - 99% Conf'],
            'Not Significant', CONFIG.colors.hotspot['Not Significant'],
            '#cccccc'  // fallback for unexpected values
        ],
        '#e0e0e0'  // null values
    ];

    map.setPaintProperty('counties-fill', 'fill-color', hotspotExpression);
    map.setPaintProperty('counties-fill', 'fill-opacity', [
        'case',
        ['has', 'trump_share_2016_hotspot_conf'],
        0.9,
        0.3
    ]);

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

    // Add title
    const titleEl = document.createElement('h3');
    titleEl.textContent = title;
    titleEl.style.marginTop = '0';
    titleEl.style.marginBottom = '10px';
    content.appendChild(titleEl);

    // Handle data-driven breaks
    if (!breaks || breaks.length === 0) {
        // Fallback: use color index as label
        colors.forEach((color, i) => {
            const item = document.createElement('div');
            item.className = 'legend-item';

            const colorBox = document.createElement('div');
            colorBox.className = 'legend-color';
            colorBox.style.backgroundColor = color;

            const label = document.createElement('span');
            label.textContent = `Category ${i + 1}`;

            item.appendChild(colorBox);
            item.appendChild(label);
            content.appendChild(item);
        });
    } else {
        // Create legend items with break labels
        colors.forEach((color, i) => {
            const item = document.createElement('div');
            item.className = 'legend-item';

            const colorBox = document.createElement('div');
            colorBox.className = 'legend-color';
            colorBox.style.backgroundColor = color;

            const label = document.createElement('span');
            // Format numbers appropriately (defined outside if/else)
            const formatNum = (n) => {
                if (n === null || n === undefined || isNaN(n)) return 'N/A';
                if (n >= 100) return Math.round(n).toString();
                if (n >= 10) return n.toFixed(1);
                return n.toFixed(2);
            };
            
            if (i < breaks.length) {
                const currentBreak = breaks[i];
                const nextBreak = breaks[i + 1];
                
                if (nextBreak !== undefined) {
                    label.textContent = `${formatNum(currentBreak)} - ${formatNum(nextBreak)}`;
                } else {
                    label.textContent = `${formatNum(currentBreak)}+`;
                }
            } else {
                label.textContent = `Category ${i + 1}`;
            }

            item.appendChild(colorBox);
            item.appendChild(label);
            content.appendChild(item);
        });
    }

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

// Helper function to format values with null handling
function formatValue(value, format = 'number', decimals = 1) {
    if (value === null || value === undefined || isNaN(value)) {
        return 'Data suppressed';
    }
    
    if (format === 'percent') {
        return value.toFixed(decimals) + '%';
    } else if (format === 'number') {
        return value.toFixed(decimals);
    } else if (format === 'integer') {
        return Math.round(value).toString();
    }
    return value.toString();
}

// Info card functions
function showInfoCard(properties) {
    const card = document.getElementById('info-card');
    const nameEl = document.getElementById('county-name');
    const statsEl = document.getElementById('county-stats');

    nameEl.textContent = properties.NAME || properties.county_name || 'Unknown County';

    // Build stats HTML with null handling
    const stats = [
        { 
            label: 'Trump 2016', 
            value: formatValue(properties.trump_share_2016, 'percent'),
            show: properties.trump_share_2016 !== null && properties.trump_share_2016 !== undefined
        },
        { 
            label: 'Trump 2020', 
            value: formatValue(properties.trump_share_2020, 'percent'),
            show: properties.trump_share_2020 !== null && properties.trump_share_2020 !== undefined
        },
        { 
            label: 'Physical Distress', 
            value: formatValue(properties.freq_phys_distress_pct, 'percent'),
            show: properties.freq_phys_distress_pct !== null && properties.freq_phys_distress_pct !== undefined
        },
        { 
            label: 'Overdose Rate', 
            value: formatValue(properties.od_1316_rate, 'number'),
            show: properties.od_1316_rate !== null && properties.od_1316_rate !== undefined
        },
        { 
            label: 'Rural', 
            value: properties.rural === 1 ? 'Yes' : (properties.rural === 0 ? 'No' : 'Data suppressed'),
            show: properties.rural !== null && properties.rural !== undefined
        },
        { 
            label: 'Bivariate Cluster', 
            value: properties.bv_cluster || 'Not Significant',
            show: properties.bv_cluster !== null && properties.bv_cluster !== undefined
        }
    ].filter(stat => stat.show);  // Only show stats with data

    if (stats.length === 0) {
        statsEl.innerHTML = '<div class="stat-row">No data available for this county</div>';
    } else {
        statsEl.innerHTML = stats.map(stat => `
            <div class="stat-row">
                <span class="stat-label">${stat.label}:</span>
                <span class="stat-value">${stat.value}</span>
            </div>
        `).join('');
    }

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