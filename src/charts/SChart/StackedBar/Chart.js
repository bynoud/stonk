
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

		const fill = (d, i) => {console.log('fill',d,i); return d.y3 ? '#ff0000' : '#00ff00'};
		return (
			<ChartCanvas ratio={ratio} width={width} height={400}
					margin={{ left: 40, right: 10, top: 20, bottom: 30 }} type={type}
					seriesName="Fruits"
					// xExtents={list => list.map(d => d.x)}
					data={data}
					xAccessor={d => {console.log('xa', d); return d.x} }
					xScale={scalePoint()}
					padding={1}>
				<Chart id={1}
						yExtents={[0, d => d.y1]}>
					<XAxis axisAt="bottom" orient="bottom" />
					<YAxis axisAt="left" orient="left" />
					<BarSeries 
                        // yAccessor={[d => d.y1, d => d.y2, d => d.y3]}
                        yAccessor={d => d.y1}
							fill={fill} widthRatio={1.0} stroke={false} />
				</Chart>
			</ChartCanvas>
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
