// Global Chart.js configuration
Chart.defaults.color = '#adb5bd';
Chart.defaults.font.family = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif";

// Custom tooltips
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(33, 37, 41, 0.9)';
Chart.defaults.plugins.tooltip.titleFont = { weight: 'bold' };
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.plugins.tooltip.cornerRadius = 3;
Chart.defaults.plugins.tooltip.caretSize = 5;

// Legend
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding = 15;

// Global themes and helpers
const chartColors = {
    primary: 'rgba(0, 123, 255, 1)',
    primaryLight: 'rgba(0, 123, 255, 0.1)',
    success: 'rgba(40, 167, 69, 1)',
    successLight: 'rgba(40, 167, 69, 0.1)',
    danger: 'rgba(220, 53, 69, 1)',
    dangerLight: 'rgba(220, 53, 69, 0.1)',
    warning: 'rgba(255, 193, 7, 1)',
    warningLight: 'rgba(255, 193, 7, 0.1)',
    info: 'rgba(23, 162, 184, 1)',
    infoLight: 'rgba(23, 162, 184, 0.1)',
    secondary: 'rgba(108, 117, 125, 1)',
    secondaryLight: 'rgba(108, 117, 125, 0.1)'
};

/**
 * Format currency for chart labels
 * @param {number} value - The value to format
 * @param {string} prefix - Currency prefix ($ by default)
 * @returns {string} Formatted currency string
 */
function formatCurrency(value, prefix = '$') {
    return prefix + value.toFixed(2);
}

/**
 * Create a gradient background for line charts
 * @param {CanvasRenderingContext2D} ctx - Canvas context 
 * @param {string} color - Base color
 * @returns {CanvasGradient} Gradient object
 */
function createGradient(ctx, color) {
    const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
    gradient.addColorStop(0, color.replace('1)', '0.4)'));
    gradient.addColorStop(1, color.replace('1)', '0)'));
    return gradient;
}

/**
 * Create dataset configuration for line charts
 * @param {string} label - Dataset label
 * @param {Array} data - Data points
 * @param {string} color - Base color
 * @param {boolean} fill - Whether to fill area under line
 * @returns {Object} Dataset configuration
 */
function createLineDataset(label, data, color, fill = true) {
    return {
        label: label,
        data: data,
        borderColor: color,
        backgroundColor: fill ? color.replace('1)', '0.1)') : 'transparent',
        fill: fill,
        tension: 0.4,
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5
    };
}

/**
 * Create dataset configuration for bar charts
 * @param {string} label - Dataset label
 * @param {Array} data - Data points
 * @param {string} color - Base color
 * @returns {Object} Dataset configuration
 */
function createBarDataset(label, data, color) {
    return {
        label: label,
        data: data,
        backgroundColor: color.replace('1)', '0.7)'),
        borderColor: color,
        borderWidth: 1,
        borderRadius: 3,
        hoverBackgroundColor: color
    };
}

/**
 * Apply consistent formatting to all tooltips
 * @param {Object} tooltipItems - Tooltip items 
 * @returns {string} Formatted tooltip
 */
function formatTooltip(tooltipItems) {
    let result = tooltipItems.label + '\n';
    
    tooltipItems.formattedValues.forEach((value, index) => {
        const color = tooltipItems.dataset.borderColor || tooltipItems.dataset.backgroundColor;
        result += `${tooltipItems.dataset.label}: ${value}\n`;
    });
    
    return result;
}
