
import React from "react";
import PropTypes from "prop-types";

import { set } from "d3-collection";
import { scaleOrdinal, schemeCategory10, scalePoint } from  "d3-scale";

import { ChartCanvas, Chart } from "react-stockcharts";
import {
	BarSeries,
} from "react-stockcharts/lib/series";
import { XAxis, YAxis } from "react-stockcharts/lib/axes";
import { fitWidth } from "react-stockcharts/lib/helper";

class StackedBarChart extends React.Component {
	render() {
		const { data, type, width, ratio } = this.props;
		console.log(this.props)

		const f = scaleOrdinal(schemeCategory10)
			.domain(set(data.map(d => d.region)));

		// const fill = (d, i) => {
        //     return d.y3 ? '#ff0000' : '#00ff00'
        // };
        const fill = (d, i) => f(i);
		return (
            <StackedBarSeries 
                yAccessor={[d => d.buyVol, d => d.y2, d => d.y3, d => d.y4]}
                fill={fill} />
    );
	}
}

StackedBarChart.propTypes = {
	data: PropTypes.array.isRequired,
	width: PropTypes.number.isRequired,
	ratio: PropTypes.number.isRequired,
	type: PropTypes.oneOf(["svg", "hybrid"]).isRequired,
};

StackedBarChart.defaultProps = {
	type: "svg",
};
StackedBarChart = fitWidth(StackedBarChart);

export default StackedBarChart;
