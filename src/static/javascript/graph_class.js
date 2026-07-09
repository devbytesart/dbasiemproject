/*

Copyright 2026 ttdantett DevBytesArt

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

author: ttdantett
title: siem project
document: graph class
*/

class Graph {
    constructor(canvasId) {
        this.canvasId = canvasId;
        this.chartInstance = null;
        this.buttonsContainerId = `buttons-${canvasId}`;
        this.dataLabelsVisible = false; // Display or hide label

        // Check if canvas exists
        const canvas = document.getElementById(this.canvasId);
        if (!canvas) {
            console.error(`Canvas with id "${this.canvasId}" not found.`);
            return;
        }

        // Create the container of buttons only once
        if (!document.getElementById(this.buttonsContainerId)) {
            this.addButtonsEventListener();
        }
    }

    addButtonsEventListener() {

        const legendButton = $("#button-legend")[0];
        if (legendButton) {
            legendButton.addEventListener('click', () => this.toggleLegend());
        }

        const valueButton = $("#button-value")[0];
        if (valueButton) {
            valueButton.addEventListener('click', () => this.toggleDataLabels());
        }
    }

    

    destroyChart() {
        if (this.chartInstance) {
            this.chartInstance.clear();
            this.chartInstance.destroy();
            this.chartInstance = null;
        }
    }

    static generateColor(index) {
        const r = (index * 53) % 255;
        const g = (index * 97) % 255;
        const b = (index * 139) % 255;
        return `rgba(${r}, ${g}, ${b}, 0.6)`;
    }

    static determineOptimalTimeUnit(timestamps) {
        if (!timestamps || timestamps.length < 2) return 'day';

        const totalDuration = new Date(timestamps[timestamps.length - 1]) - new Date(timestamps[0]);

        const timeDiffs = [];
        for (let i = 1; i < timestamps.length; i++) {
            const diff = new Date(timestamps[i]) - new Date(timestamps[i - 1]);
            if (!isNaN(diff)) {
                timeDiffs.push(diff);
            }
        }

        if (timeDiffs.length === 0) return 'day';

        const avgDiff = timeDiffs.reduce((a, b) => a + b, 0) / timeDiffs.length;

        if (avgDiff < 1000 && totalDuration < 60000) return 'millisecond';
        if (avgDiff < 60000 && totalDuration < 3600000) return 'second';
        if (avgDiff < 3600000) return 'minute';
        if (avgDiff < 86400000) return 'hour';
        if (avgDiff < 604800000) return 'day';
        if (avgDiff < 2592000000) return 'week';
        if (avgDiff < 7776000000) return 'month';
        if (avgDiff < 31536000000) return 'quarter';
        return 'year';
    }

    drawChart(data, chartType) {
        if (!data || data.length === 0) {
            console.error("Data is empty or invalid.");
            return null;
        }

        const parsedData = data.map(item => {
            try {
                return typeof item === 'string' ? JSON.parse(item) : item;
            } catch (error) {
                console.error("Error during JSON parsing", error);
                return null;
            }
        }).filter(item => item !== null);

        if (parsedData.length === 0 || !parsedData[0]) {
            console.error("Data is empty or invalid.");
            return null;
        }

        const labelKey = Object.keys(parsedData[0])[0];
        const labels = parsedData.map(item => item[labelKey]);

        // 1 Check if date
        const isDate = labels.length > 0 && !isNaN(Date.parse(labels[0]));
        let timeUnit = 'day';

        if (isDate) {
            try {
                axis_x = Graph.determineOptimalTimeUnit(labels);
            } catch (e) {
                console.error("Error during time unit calculation :", e);
                timeUnit = 'day';
            }
        }

        // 2. Configuration axis
        const xScaleConfig = isDate
            ? {
                type: 'time',
                time: {
                    unit: timeUnit,
                    // Adapted for majority adapters Chart.js (Luxon/Date-fns)
                    displayFormats: {
                        millisecond: 'HH:mm:ss.SSS',
                        second: 'HH:mm:ss',
                        minute: 'HH:mm',
                        hour: 'HH:mm',
                        day: 'dd/MM',     
                        week: 'dd/MM',
                        month: 'MMM yyyy', 
                        quarter: '[Q]Q - yyyy',
                        year: 'yyyy'
                    }
                },
                ticks: { 
                    maxTicksLimit: 10,
                    autoSkip: true
                 }
            }
            : {
                ticks: { 
                    autoSkip: true, 
                    maxTicksLimit: 10 }
            };

        const seriesKeys = Object.keys(parsedData[0]).filter(key => key !== labelKey);

        const datasets = seriesKeys.map((key, index) => {
            const color = Graph.generateColor(index);
            return {
                label: key,
                data: parsedData.map(item => item[key] !== null ? parseFloat(item[key]) : 0),
                borderWidth: 2,
                fill: false
            };
        });

        const config = {
            type: chartType,
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { x: xScaleConfig, y: { beginAtZero: true } },
                plugins: {
                    legend: { display: true },
                    datalabels: {
                        display: false,
                        borderColor: color,
                        backgroundColor: color,
                        font: { size: 10 }
                    }
                }
            },
            plugins: [ChartDataLabels]
        };

        const ctx = document.getElementById(this.canvasId)?.getContext('2d');
        if (ctx) {
            this.destroyChart(); // delete old chart before redrawing
            this.chartInstance = new Chart(ctx, config);
            return this.chartInstance; // <--Important
        } else {
            console.error("Canvas not found on the page: ", this.canvasId);
            return null;
        }
    }


    toggleLegend() {
        if (this.chartInstance) {
            const legend = this.chartInstance.options.plugins.legend;
            legend.display = !legend.display;
            this.chartInstance.update();
        }
    }

    toggleDataLabels() {
        if (this.chartInstance) {
            const dataLabels = this.chartInstance.options.plugins.datalabels;
            this.dataLabelsVisible = !this.dataLabelsVisible;
            dataLabels.display = this.dataLabelsVisible;
            this.chartInstance.update();
        }
    }
}




