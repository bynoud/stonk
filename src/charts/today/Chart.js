
import React from "react";
import PropTypes from "prop-types";

import { format } from "d3-format";
import { timeFormat } from "d3-time-format";

import { set } from "d3-collection";
import { scaleOrdinal, schemeCategory10, scalePoint } from  "d3-scale";

import { ChartCanvas, Chart } from "react-stockcharts";
import {
	BarSeries,
	StackedBarSeries,
	// VolumeProfileSeries,
	CandlestickSeries,
	LineSeries,
	AreaSeries,
	RSISeries,
} from "react-stockcharts/lib/series";
import VolumeProfileSeries from './VolumeProfileSeries';
import { XAxis, YAxis } from "react-stockcharts/lib/axes";
import {
	CrossHairCursor,
	MouseCoordinateX,
	MouseCoordinateY,
	EdgeIndicator,
} from "react-stockcharts/lib/coordinates";
import { ema, rsi, sma, atr } from "react-stockcharts/lib/indicator";

import { discontinuousTimeScaleProvider } from "react-stockcharts/lib/scale";
import {
	OHLCTooltip,
	RSITooltip,
} from "react-stockcharts/lib/tooltip";
import { change } from "react-stockcharts/lib/indicator";
import { fitWidth } from "react-stockcharts/lib/helper";
import { last } from "react-stockcharts/lib/utils";

class VolumeProfileBySessionChart extends React.Component {
	render() {

		const changeCalculator = change();

		const { type, data: initialData, width, ratio } = this.props;

		const smaVolume50 = sma()
			.id(3)
			.options({ windowSize: 50, sourcePath: "volume" })
			.merge((d, c) => {d.smaVolume50 = c;})
			.accessor(d => d.smaVolume50);

		// const calculatedData = changeCalculator(initialData);
		const calculatedData = smaVolume50(initialData);
		// console.log('data', initialData, calculatedData, changeCalculator)
		const xScaleProvider = discontinuousTimeScaleProvider
			.inputDateAccessor(d => d.date);
		const {
			data,
			xScale,
			xAccessor,
			displayXAccessor,
		} = xScaleProvider(calculatedData);

		const start = xAccessor(last(data));
		const end = xAccessor(data[Math.max(0, data.length - 150)]);
		const xExtents = [start, end];

		const f = scaleOrdinal(schemeCategory10)
			.domain(set(data.map(d => d.region)));

		const fill = (d, i) => (i==0)?'#6BA583':(i==1)?'#FF0000':'#A9A9B0';

		return (
			<ChartCanvas height={600}
				width={width}
				ratio={ratio}
				margin={{ left: 80, right: 80, top: 10, bottom: 30 }}
				type={type}
				seriesName="MSFT"
				data={data}
				xScale={xScale}
				xAccessor={xAccessor}
				displayXAccessor={displayXAccessor}
				xExtents={xExtents}
			>

				
				<Chart id={1} height={300}
					yExtents={[d => [d.high, d.low]]}
					padding={{ top: 40, bottom: 20 }}
				>
					<XAxis axisAt="bottom" orient="bottom" showTicks={false} />
					<YAxis axisAt="right" orient="right" ticks={5} />
					<MouseCoordinateX
						at="bottom"
						orient="bottom"
						displayFormat={timeFormat("%Y-%m-%d")} />
					<MouseCoordinateY
						at="right"
						orient="right"
						displayFormat={format(".2f")} />

					{/* <VolumeProfileSeries bySession orient="right" showSessionBackground
					 /> */}

					<CandlestickSeries />
					<LineSeries yAccessor={d => d.fitval} stroke="blue" 
						defined={d => !isNaN(null) && (d !== null) }/>
					<LineSeries yAccessor={d => d.fitCurve} stroke="red" 
						defined={d => !isNaN(null) && (d !== null) }/>
					<EdgeIndicator itemType="last" orient="right" edgeAt="right"
						yAccessor={d => d.close} fill={d => d.close > d.open ? "#6BA583" : "#FF0000"}/>

					<OHLCTooltip origin={[-40, 0]} />

				</Chart>

				<Chart id={2}
					yExtents={[0, d => d.volume]}
					height={120} origin={(w, h) => [0, h - 400]}
				>
					<YAxis axisAt="left" orient="left" ticks={5} tickFormat={format(".2s")}/>

					<MouseCoordinateY
						at="left"
						orient="left"
						displayFormat={format(".4s")} />

					{/* <BarSeries yAccessor={d => d.volume}
						// widthRatio={0.95}
						// opacity={0.3}
						fill={d => d.close > d.open ? "#6BA583" : "#FF0000"}
					/> */}
					<StackedBarSeries 
						yAccessor={[d => d.buyVol, d => d.sellVol, d => d.unkVol]}
						fill={fill}
						widthRatio={0.8}
						// fill={['#ff0000', '#00ff00', '#0000ff']}
					/>
					<AreaSeries yAccessor={smaVolume50.accessor()} stroke={smaVolume50.stroke()} fill={smaVolume50.fill()}/>
				</Chart>

				<Chart id={3}
					yExtents={[0, 100]}
					height={125} origin={(w, h) => [0, h - 250]}
				>
					<XAxis axisAt="bottom" orient="bottom" showTicks={false} outerTickSize={0} />
					<YAxis axisAt="right"
						orient="right"
						tickValues={[30, 50, 70]}/>
					<MouseCoordinateY
						at="right"
						orient="right"
						displayFormat={format(".2f")} />

					<RSISeries yAccessor={d => d.volRsi} 
						stroke={{insideThreshold:'#d60dd6'}}
					/>

					<RSITooltip origin={[-38, 15]}
						yAccessor={d => d.volRsi}
						options={{windowSize:14}} />
				</Chart>

				<CrossHairCursor />
			</ChartCanvas>
		);
	}
}

VolumeProfileBySessionChart.propTypes = {
	data: PropTypes.array.isRequired,
	width: PropTypes.number.isRequired,
	ratio: PropTypes.number.isRequired,
	type: PropTypes.oneOf(["svg", "hybrid"]).isRequired,
};

VolumeProfileBySessionChart.defaultProps = {
	type: "svg",
};
VolumeProfileBySessionChart = fitWidth(VolumeProfileBySessionChart);

export default VolumeProfileBySessionChart;
