
import React from "react";
import PropTypes from "prop-types";

import { format } from "d3-format";
import { timeFormat } from "d3-time-format";

import { set } from "d3-collection";
import { scaleOrdinal, schemeCategory10, scalePoint } from  "d3-scale";

import { ChartCanvas, Chart, ZoomButtons } from "react-stockcharts";
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
	constructor(props) {
		super(props);
		this.saveNode = this.saveNode.bind(this);
		this.resetYDomain = this.resetYDomain.bind(this);
		this.handleReset = this.handleReset.bind(this);
	}
	componentWillMount() {
		this.setState({
			suffix: 1
		});
	}
	saveNode(node) {
		this.node = node;
	}
	resetYDomain() {
		this.node.resetYDomain();
	}
	handleReset() {
		this.setState({
			suffix: this.state.suffix + 1
		});
	}

	render() {

		const changeCalculator = change();

		const { type, data: initialData, width, height, ratio } = this.props;
		const priceChartHeight = height * 0.58; //0.72;
		const volChartHeight = priceChartHeight / 1.8;
		const indexChartHeight = height * 0.2;
		const cciChartHeight = height * 0.2;

		console.log('height', height, priceChartHeight, volChartHeight, indexChartHeight);

		const smaVolume50 = sma()
			.id(3)
			.options({ windowSize: 50, sourcePath: "volumn" })
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

		const start = xAccessor(last(data))+1;
		const end = xAccessor(data[Math.max(0, data.length - 150)]);
		const xExtents = [start, end];

		let cciMin = 0;
		let cciMax = 100;
		let abvMin = 0;
		let abvMax = 100;

		const f = scaleOrdinal(schemeCategory10)
			.domain(set(data.map(d => d.region)));

		const fill = (d, i) => (i==0)?'#6BA583':(i==1)?'#FF0000':'#A9A9B0';

		return (
			<ChartCanvas ref={this.saveNode} height={height}
				width={width}
				ratio={ratio}
				// margin={{ left: 80, right: 80, top: 10, bottom: 30 }}
				margin={{ left: 1, right: 40, top: 1, bottom: 1 }}
				type={type}
				seriesName={`MSFT_${this.state.suffix}`}
				data={data}
				xScale={xScale}
				xAccessor={xAccessor}
				displayXAccessor={displayXAccessor}
				xExtents={xExtents}
			>

				
				<Chart id={1} height={priceChartHeight}
					yExtents={[d => [d.high, d.low]]}
					// padding={{ top: 40, bottom: 20 }}
				>
					<XAxis axisAt="bottom" orient="bottom" showTicks={false} />
					<YAxis axisAt="right" orient="right" ticks={5} />
					{/* <MouseCoordinateX
						at="bottom"
						orient="bottom"
						displayFormat={timeFormat("%Y-%m-%d")} /> */}
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

					<OHLCTooltip origin={[0, 10]} />
					<ZoomButtons
						onReset={this.handleReset}
					/>

				</Chart>

				<Chart id={2}
					yExtents={[0, d => d.volumn]}
					height={volChartHeight} origin={(w, h) => [0, priceChartHeight - volChartHeight]}
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
						opacity={0.3}
						// fill={['#ff0000', '#00ff00', '#0000ff']}
					/>
					<AreaSeries yAccessor={smaVolume50.accessor()} stroke={smaVolume50.stroke()} fill={smaVolume50.fill()}/>
				</Chart>

				<Chart id={3}
					yExtents={[d => Math.min(abvMin, d.volRsi), d => Math.max(abvMax, d.volRsi)]}
					height={indexChartHeight} origin={(w, h) => [0, priceChartHeight+1]}
				>
					<XAxis axisAt="bottom" orient="bottom" showTicks={false} outerTickSize={0} />
					{/* <YAxis axisAt="right"
						orient="right"
						tickValues={[30, 50, 70]}
						/> */}
					{/* <MouseCoordinateY
						at="right"
						orient="right"
						displayFormat={format(".2f")} /> */}

					<RSISeries yAccessor={d => d.volRsi} 
						overSold='75' overBought='25' middle='50'
						stroke={{insideThreshold:'#d60dd6'}}
					/>

					<RSITooltip origin={[0, 15]}
						yAccessor={d => d.volRsi}
						options={{windowSize:14}} />
				</Chart>

				<Chart id={4}
					yExtents={[d => Math.min(cciMin, d.cci), d => Math.max(cciMax, d.cci)]}
					height={cciChartHeight} origin={(w, h) => [0, priceChartHeight+indexChartHeight+2]}
				>
					<XAxis axisAt="bottom" orient="bottom" showTicks={false} outerTickSize={0} />
					{/* <YAxis axisAt="right"
						orient="right"
						tickValues={[30, 50, 70]}
						/> */}
					{/* <MouseCoordinateY
						at="right"
						orient="right"
						displayFormat={format(".2f")} /> */}

					<RSISeries yAccessor={d => d.cci} 
						overSold='-100' overBought='100' middle='0'
						stroke={{insideThreshold:'#d60dd6'}}
					/>

					<RSITooltip origin={[0, 15]}
						yAccessor={d => d.cci}
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
	height: 600,
};
VolumeProfileBySessionChart = fitWidth(VolumeProfileBySessionChart);

export default VolumeProfileBySessionChart;
