// Wrapper class for Chart.js integrations

export function createChart(canvasId, type, labels, data, labelName = 'Value') {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  // Destroy previous chart if it exists
  const existingChart = Chart.getChart(ctx);
  if (existingChart) {
    existingChart.destroy();
  }

  const isDark = true; // Nexus default dark theme
  const gridColor = 'rgba(255, 255, 255, 0.05)';
  const textColor = '#94a3b8';

  const chartConfig = {
    type: type === 'horizontalBar' ? 'bar' : type,
    data: {
      labels: labels,
      datasets: [{
        label: labelName,
        data: data,
        backgroundColor: type === 'pie' || type === 'doughnut' 
          ? [
              'rgba(0, 212, 255, 0.7)',
              'rgba(139, 92, 246, 0.7)',
              'rgba(236, 72, 153, 0.7)',
              'rgba(59, 130, 246, 0.7)',
              'rgba(16, 185, 129, 0.7)'
            ]
          : 'rgba(0, 212, 255, 0.65)',
        borderColor: type === 'pie' || type === 'doughnut'
          ? [
              'rgba(0, 212, 255, 1)',
              'rgba(139, 92, 246, 1)',
              'rgba(236, 72, 153, 1)',
              'rgba(59, 130, 246, 1)',
              'rgba(16, 185, 129, 1)'
            ]
          : 'rgba(0, 212, 255, 1)',
        borderWidth: 1.5,
        borderRadius: type === 'bar' || type === 'horizontalBar' ? 6 : 0,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: type === 'horizontalBar' ? 'y' : 'x',
      plugins: {
        legend: {
          display: type === 'pie' || type === 'doughnut',
          labels: {
            color: textColor,
            font: { family: 'Inter' }
          }
        },
      },
    }
  };

  // Add scale config for non-radial charts
  if (type !== 'pie' && type !== 'doughnut') {
    chartConfig.options.scales = {
      x: {
        grid: { color: gridColor },
        ticks: { color: textColor, font: { family: 'Inter', size: 11 } }
      },
      y: {
        grid: { color: gridColor },
        ticks: { color: textColor, font: { family: 'Inter', size: 11 } }
      }
    };
  }

  return new Chart(ctx, chartConfig);
}
