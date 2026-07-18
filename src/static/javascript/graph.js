/*

Copyright 2026 ttdantett DevBytesArt®

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
document: graph
*/

var myChart = null;

function destroyChart() {
    if (myChart) {
        myChart.clear();
        myChart.destroy();
        myChart = null;
    }
}

function generateColor(index) {
    const r = (index * 53) % 255;
    const g = (index * 97) % 255;
    const b = (index * 139) % 255;
    return `rgba(${r}, ${g}, ${b}, 0.6)`;
}

function determineOptimalTimeUnit(timestamps) {
    const timeDiffs = timestamps.slice(1).map((label, index) =>
        (new Date(label) - new Date(timestamps[index]))
    );
    const avgDiff = timeDiffs.reduce((a, b) => a + b, 0) / timeDiffs.length;

    if (avgDiff < 1000) return 'millisecond';
    else if (avgDiff < 60000) return 'second';
    else if (avgDiff < 3600000) return 'minute';
    else if (avgDiff < 86400000) return 'hour';
    else if (avgDiff < 604800000) return 'day';
    else if (avgDiff < 2592000000) return 'week';
    else if (avgDiff < 7776000000) return 'month';
    else if (avgDiff < 31536000000) return 'quarter';
    return 'year';
}

function drawChart(data, chartType, canvasId) {
    if (!data || data.length === 0) {
        console.error("Data is empty or invalid.");
        return;
    }

    const parsedData = data.map(item => {
        try {
            return typeof item === 'string' ? JSON.parse(item) : item;
        } catch (error) {
            console.error("Erreur during JSON analysis", error);
            return null;
        }
    }).filter(item => item !== null);

    if (parsedData.length === 0 || !parsedData[0]) {
        console.error("Data is empty or invalid.");
        return;
    }

    const labelKey = Object.keys(parsedData[0])[0];
    const labels = parsedData.map(item => item[labelKey]);

    const isDate = !isNaN(Date.parse(labels[0]));

    const xScaleConfig = isDate
        ? {
            type: 'time',
            time: {
                unit: determineOptimalTimeUnit(labels),
                displayFormats: {
                    millisecond: 'HH:mm:ss.SSS',
                    second: 'HH:mm:ss',
                    minute: 'HH:mm',
                    hour: 'HH:mm',
                    day: 'MM/dd',
                    week: 'MM/dd',
                    month: 'MMM YYYY',
                    quarter: '[Q]Q - yyyy',
                    year: 'YYYY'
                }
            },
            ticks: {
                maxTicksLimit: 10
            }
        }
        : {
            ticks: {
                autoSkip: true,
                maxTicksLimit: 10
            }
        };

    const seriesKeys = Object.keys(parsedData[0]).filter(key => key !== labelKey);

    const datasets = seriesKeys.map((key, index) => ({
        label: key,
        data: parsedData.map(item => item[key] !== null ? parseFloat(item[key]) : 0),
        // backgroundColor: generateColor(index),
        // borderColor: generateColor(index),
        borderWidth: 2,
        fill: false
    }));

    const config = {
        type: chartType,
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            scales: {
                x: xScaleConfig,
                y: {
                    beginAtZero: true
                }
            }
        }
    };

    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (ctx) {
        if (myChart) destroyChart();
        myChart = new Chart(ctx, config);
    } else {
        console.error("Canvas unfound in the page: ", canvasId);
    }
}
