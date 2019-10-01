/*
Copyright 2019 The Aerospace Corporation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

/*
 * Visualization source
 */
define([
            'jquery',
            'underscore',
            'api/SplunkVisualizationBase',
            'api/SplunkVisualizationUtils',
            'd3'
        ],
        function(
            $,
            _,
            SplunkVisualizationBase,
            SplunkVisualizationUtils,
            d3
        ) {

    function computeDimensions(selection) {
        var dimensions = null;
        var node = selection.node();

        if (node instanceof SVGElement) { // check if node is svg element
            dimensions = node.getBBox();
        } else { // else is html element
            dimensions = node.getBoundingClientRect();
        }

        return dimensions;
    }

    function range(start, end) {
        if (start === end) return [start];
        return [start, ...range(start + 1, end)];
    }

    // Extend from SplunkVisualizationBase
    return SplunkVisualizationBase.extend({
        initialize: function() {
            this.$el = $(this.el);

            // Add a css selector class
            this.$el.addClass('timeline-viz');
        },

        // Optionally implement to format data returned from search.
        // The returned object will be passed to updateView as 'data'
        formatData: function(data) {
            data.rows = data.rows.map(function(d) {
                return [
                    SplunkVisualizationUtils.escapeHtml(d[0]),
                    parseFloat(SplunkVisualizationUtils.escapeHtml(d[1])),
                    parseFloat(SplunkVisualizationUtils.escapeHtml(d[2]))
                ]
            })

            return data;
        },

        // Implement updateView to render a visualization.
        //  'data' will be the data object returned from formatData or from the search
        //  'config' will be the configuration property object
        updateView: function(data, config) {
            // Guard for empty data
            if (data.rows.length < 1) {
                return;
            }

            var x_axis_title = this.getConfigProperty(config, 'xAxisTitle')
            var y_axis_title = this.getConfigProperty(config, 'yAxisTitle')
            var x_axis_start_at_1 = this.getConfigProperty(config, 'xAxisStartAt1')
            var x_axis_format = this.getConfigProperty(config, 'xAxisFormat')

            // Clear the div
            this.$el.empty();

            var margin = {top: 15, right: 15, bottom: 15, left: 15}
            var width = this.$el.width() - margin.left - margin.right
            var height = this.$el.height() - margin.top - margin.bottom
            var left = margin.left
            var bottom = height

            var x_domain_start;
            if (x_axis_start_at_1)
                x_domain_start = 1;
            else
                x_domain_start = d3.min(data.rows, function(d) { return d[1]; });

            var x_domain_end = d3.max(data.rows, function(d) { return d[2]; }) + 1;

            var x;
            switch (x_axis_format) {
                case "discrete":
                    x = d3.scaleBand()
                        .domain(range(x_domain_start, x_domain_end));
                    break;
                case "time":
                    x = d3.scaleTime()
                        .domain([new Date(x_domain_start), new Date(x_domain_end)]);
                    break;
                default:
                    x = d3.scaleLinear()
                        .domain([x_domain_start, x_domain_end]);
                    break;
            }

            var y = d3.scaleBand()
                .paddingInner(.08)
                .domain(data.rows.map(function(d) { return d[0]; }));

            var xAxis = d3.axisBottom()
                .scale(x);

            var yAxis = d3.axisLeft()
                .scale(y)
                .tickSizeOuter(0);

            // SVG
            var svg = d3.select(this.el).append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
              .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

            // X-Axis
            var x_axis = svg.append("g")
                .attr("class", "x axis")
                .call(xAxis);

            // Y-Axis
            var y_axis = svg.append("g")
                .attr("class", "y axis")
                .call(yAxis);

            // X-Axis label
            var x_axis_label_margin = 0
            if (x_axis_title) {
                var x_axis_label = svg.append("text")
                    .attr("class", "axis-label")
                    .attr("x", this.$el.width() / 2 - margin.left)
                    .attr("y", bottom)
                    .attr("dy", "-1em")
                    .text(x_axis_title);

                var dims = computeDimensions(x_axis_label)

                x_axis_label.attr("dx", -dims.width / 2)
                x_axis_label_margin += dims.height + 10
            }

            var chart_bottom = bottom - x_axis_label_margin - computeDimensions(x_axis).height
            var chart_height = chart_bottom

            // Y-Axis label
            var y_axis_label_margin = 0
            if (y_axis_title) {
                var y_axis_label = svg.append("text")
                    .attr("class", "axis-label")
                    .attr("transform", "rotate(-90)")
                    .attr("x", -chart_height / 2)
                    .attr("y", margin.left)
                    .text(y_axis_title);

                var dims = computeDimensions(y_axis_label)

                y_axis_label.attr("dx", -dims.width / 2)
                y_axis_label_margin += dims.height + 10
            }

            var chart_left = y_axis_label_margin + computeDimensions(y_axis).width
            var chart_width = width - chart_left

            y_label_count = Math.ceil(chart_height / (12 + 10))

            y.rangeRound([0, chart_height])
            yAxis.scale(y)
                .tickValues(y.domain().filter(function(d, i) { return !(i % Math.ceil((20 / y_label_count))) }))
            y_axis.call(yAxis)

            x.rangeRound([0, chart_width])
            xAxis.scale(x)
            x_axis.call(xAxis)

            var grid_lines_axis = d3.axisBottom()
                .tickFormat("")
                .tickSize(-chart_height)
                .scale(x);

            var grid_lines = svg.append("g")
                .attr("class", "grid")
                .call(grid_lines_axis);

            x_axis.attr("transform", "translate(" + chart_left + ", " + chart_bottom + ")")
            y_axis.attr("transform", "translate(" + chart_left + ", 0)")
            grid_lines.attr("transform", "translate(" + chart_left + ", " + chart_bottom + ")")

            // bars
            svg.selectAll(".bar")
                .data(data.rows)
                .enter()
              .append("rect")
                .attr("class", "bar")
                .attr("y", function(d) { return y(d[0]); })
                .attr("height", y.bandwidth())
                .attr("x", function(d) { return x(d[1]) + chart_left; })
                .attr("width", function(d) { return x(d[2] + 1) - x(d[1]); });

            // tooltip
            var tooltip = d3.select(this.el)
              .append('div')
                .attr('class', 'tooltip');

            tooltip.append('div')
                .attr('class', 'run');
            tooltip.append('div')
                .attr('class', 'range');

            svg.selectAll(".bar")
                .on('mouseover', function(d) {
                    tooltip.select('.run').html("<b>" + d[0] + "</b>");
                    tooltip.select('.range').html(d[1] + " to " + d[2]);
                    tooltip.style('display', 'block');
                    tooltip.style('opacity', 2);
                })
                .on('mousemove', function(d) {
                    var dims = computeDimensions(tooltip);
                    var top = d3.event.layerY - dims.height - 10;
                    if (top < 0) {
                        top = d3.event.layerY + 10;
                    }
                    tooltip.style('top', top + 'px')
                        .style('left', (d3.event.layerX - dims.width / 2) + 'px');
                })
                .on('mouseout', function() {
                    tooltip.style('display', 'none');
                    tooltip.style('opacity', 0);
                });
        },

        // Search data params
        getInitialDataParams: function() {
            return ({
                outputMode: SplunkVisualizationBase.ROW_MAJOR_OUTPUT_MODE,
                count: 10000
            });
        },

        // Override to respond to re-sizing events
        reflow: function() {
            this.invalidateUpdateView()
        },

        getConfigProperty: function(config, property_name) {
            value = config[this.getPropertyNamespaceInfo().propertyNamespace + property_name]

            if (value == "yes")
                value = true
            else if (value == "no")
                value = false

            return value
        }
    });
});