function initChart (options) {
    var bpChart = c3.generate(options);
    // Resize chart on sidebar width change
    $('.sidebar-control').on('click', function() {
        bpChart.resize();
    });
    return bpChart;
};

// Build Line Chart
function buildLineChart (element) {
    var url = $(element).attr('data-url');
    if (url !== undefined) {
        var baseOptions = {
            bindto: element,
            size: { height: 300 },
            legend: { show: false },
            data: {
                mimeType: 'json',
            },
            color: { pattern: ['#000'] },
            axis : {
                x : {
                    padding: {top:0, bottom:0},
                    type : 'timeseries',
                    tick: {
                        format: '%m/%d/%Y',
                        culling: false
                    },
                },
                y: {
                    tick: {
                        format: d3.format('.1f'),
                    },
                }
            },
            point: {
                show: true,
                r: 3,
                select: {r: 10},
            },
            tooltip: {
                contents: function (d) {
                    return "<span class='badge badge-secondary'>" + d[0].value + "</span>"
                },
            }
        };
        $.get(url, function(data, status) {
            if ($.isEmptyObject(data)) {
                return;
            }
            var dataValues = data.json;
            baseOptions.data.json = dataValues;
            baseOptions.data.keys = data.keys;
            baseOptions.axis.x.min = data.x_min;
            baseOptions.axis.x.max = data.x_max;
            baseOptions.color.pattern = data.color;
            baseOptions.axis.y.tick.values = data.y_values;
            baseOptions.axis.y.min = data.y_min;
            baseOptions.axis.y.max = data.y_max;
            if (dataValues.length > 3) {
                // rotate xaxis labels
                baseOptions.axis.x.tick.rotate = 90;
            }
            initChart(baseOptions);
        });
    }
};

function calcPadding(start, end, width) {
    var startDate = new Date(start),
        endDate = new Date(end);
    return Math.round(150 / ((width - 150) / (endDate - startDate)) - 86400000);
}


// Build Line Chart with regions
function buildRegionsChart (element, callback) {
    var url = $(element).attr('data-url');
    if (url !== undefined) {
        var baseOptions = {
            bindto: element,
            size: { height: 300 },
            legend: { show: false },
            onresize: function () {
                // add space before x axis for regions names
                this.config.axis_x_padding.left = calcPadding(
                    this.config.axis_x_min,
                    this.config.axis_x_max,
                    $(this.config.bindto).width()
                );
            },
            data: {
                mimeType: 'json',
            },
            color: { pattern: ['#000'] },
            axis : {
                x : {
                    padding: {top:0, bottom:0},
                    type : 'timeseries',
                    tick: {
                        format: '%m/%d/%Y',
                        culling: false,
                    },
                },
                y: {
                    show: false,
                    min: 0,
                    padding: {top:20, bottom: 10},
                }
            },
            point: {
                show: true,
                r: 3,
                select: {r: 10},
            },
            grid: {
                y: { lines: [] }
            },
            regions: [],
            tooltip: {
                contents: function (d) {
                    return "<span class='badge badge-secondary'>" + d[0].value + "</span>"
                },
            }
        };
        $.get(url, function(data, status) {
            if ($.isEmptyObject(data)) {
                return;
            }

            var dataValues = data.json;
            baseOptions.data.json = dataValues;
            baseOptions.data.keys = data.keys;
            baseOptions.axis.x.min = data.x_min;
            baseOptions.axis.x.max = data.x_max;
            baseOptions.axis.x.padding.left = calcPadding(data.x_min, data.x_max, $(element).width());
            baseOptions.axis.y.max = data.y_max;
            baseOptions.grid.y.lines = data.lines;
            baseOptions.regions = data.regions;

            if (dataValues.length > 3) {
                // rotate xaxis labels
                baseOptions.axis.x.tick.rotate = 90;
            }
            if (data.values) {
                baseOptions.tooltip.contents = function (d) {
                    return "<span class='badge badge-secondary'>" + data.values[d[0].index] + "</span>"
                };
            }
            initChart(baseOptions);
            if (typeof callback != 'undefined') {
                callback();
            }
        });
    }
};

// Build Bar Char
function buildBarChart (element) {
    var url = $(element).attr('data-url');
    if (url !== undefined) {
        var baseOptions = {
            bindto: element,
            size: { height: 400 },
            data: {
                x : 'x',
                mimeType: 'json',
                type: 'bar',
            },
            color: {
                pattern: ['#2196F3', '#FF9800', '#4CAF50']
            },
            bar: { width: { ratio: 0.5 } },
            grid: {
                y: {
                    show: true
                }
            },
            axis: {
                x: {
                    type: 'category'
                }
            },
        };
        $.get(url, function(data, status) {
            if ($.isEmptyObject(data)) {
                return;
            }
            baseOptions.data.json = data.json;
            baseOptions.data.keys = data.keys;
            baseOptions.data.names = data.names;
            baseOptions.color.pattern = data.color;
            initChart(baseOptions);
        });
    }
};


function buildMultipleBarChart (element) {
    var url = $(element).attr('data-url');
    if (url !== undefined) {
        var baseOptions = {
            bindto: element,
            size: { height: 400 },
            legend: { show: false },
            data: {
                x : 'x',
                type: 'bar',
            },
            color: {
                pattern: ['#496BF8', '#F91D00', '#FFC200', '#2196F3', '#FF9800', '#4CAF50', ]
            },
            bar: { width: { ratio: 0.8 } },
            grid: {
                y: {
                    show: true
                }
            },
            axis: {
                x: {
                    type: 'category',
                    tick: {
                        rotate: 45,
                        culling: false
                    }
                }
            },
            tooltip: { order: false },
        };
        $.get(url, function(data, status) {
            if ($.isEmptyObject(data)) {
                return;
            }
            baseOptions.data.columns = data.columns;
            baseOptions.axis.x.categories = data.categories;
            initChart(baseOptions);
        });
    }
};
