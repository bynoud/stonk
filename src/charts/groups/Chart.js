
import React from "react";
import PropTypes from "prop-types";

import { format } from "d3-format";

import { set } from "d3-collection";
import { scaleOrdinal, schemeCategory10, scalePoint } from  "d3-scale";

import { ChartCanvas, Chart } from "react-stockcharts";
import {
	StackedBarSeries,
	CandlestickSeries,
	LineSeries,
	AreaSeries,
	RSISeries,
} from "react-stockcharts/lib/series";
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

import {getTicketPrice, favoriteTicket} from '../../connectors/api'

class MiniChart extends React.Component {
	// state = {initialData: null};
	constructor(props) {
		super(props);
		console.log("Creating Chart", this.props.ticket)
		this.state = {initialData: null}
		// this.refresh()
	}

	refresh(refetch) {
		const { ticket, getLive } = this.props
        console.log("refreshing", ticket)
        getTicketPrice(ticket, getLive?0:1, refetch).then(data => this.setState({initialData:data.map( d => {
			d.date = new Date(d.time * 1000); 
			return d
		})}))
    }

	componentDidMount() {
		this.refresh(0);
	}

	render() {
		console.log("Rendering", this.props)
		const initialData = this.state.initialData
		if (initialData == null) {
			// this.refresh();
			return <div>Wating</div>;
		}

		// const { type, ticket, data: initialData, width, height, ratio } = this.props;
		const { type, ticket, isFav, socket, width, height, ratio } = this.props;
		const priceChartHeight = height * 0.72;
		const volChartHeight = priceChartHeight / 2.5;
		const indexChartHeight = height * 0.26;

		console.log("MiniChart", ticket, initialData)

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

		const start = xAccessor(last(data)) + 1;
		const end = xAccessor(data[Math.max(0, data.length - 81)]);
		const xExtents = [start, end];

		const f = scaleOrdinal(schemeCategory10)
			.domain(set(data.map(d => d.region)));

		const fill = (d, i) => (i==0)?'#6BA583':(i==1)?'#FF0000':'#A9A9B0';

		const favUpdate = () => {
			socket.emit('appdb',
						{op: isFav ? 'delFavorite' : 'addFavorite',
						params:{tic:ticket}});
		}

		return (<div>
			<label>{ticket}</label>
			{/* <button onClick={() => favoriteTicket(ticket,isFav?'remove':'add')}>{isFav ? 'Unfavor':'Favor'}</button> */}
			<button onClick={favUpdate}>{isFav ? 'Unfavor':'Favor'}</button>
			<button onClick={() => this.refresh(1)}>Live Data</button>

			<ChartCanvas height={height}
				width={width}
				ratio={ratio}
				margin={{ left: 1, right: 10, top: 1, bottom: 1 }}
				type={type}
				seriesName={ticket}
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


					<CandlestickSeries />
					<LineSeries yAccessor={d => d.fitval} stroke="blue" 
						defined={d => !isNaN(null) && (d !== null) }/>
					<LineSeries yAccessor={d => d.fitCurve} stroke="red" 
						defined={d => !isNaN(null) && (d !== null) }/>
					{/* <EdgeIndicator itemType="last" orient="right" edgeAt="right"
						yAccessor={d => d.close} fill={d => d.close > d.open ? "#6BA583" : "#FF0000"}/> */}

					<OHLCTooltip origin={[0, 10]} />

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

					{/* <BarSeries yAccessor={d => d.volumn}
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
					yExtents={[0, 100]}
					height={indexChartHeight} origin={(w, h) => [0, priceChartHeight+1]}
				>
					<XAxis axisAt="bottom" orient="bottom" showTicks={false} outerTickSize={0} />
					{/* <YAxis axisAt="right"
						orient="right"
						tickValues={[30, 50, 70]}
						/>
					<MouseCoordinateY
						at="right"
						orient="right"
						displayFormat={format(".2f")} /> */}

					<RSISeries yAccessor={d => d.volRsi} 
						overSold={100} overBought={0} middle={50}
						stroke={{insideThreshold:'#d60dd6'}}
					/>

					<RSITooltip origin={[0, 15]}
						yAccessor={d => d.volRsi}
						options={{windowSize:14}} />
				</Chart>

				<CrossHairCursor />
			</ChartCanvas>
		</div>
		);
	}
}

MiniChart.propTypes = {
	data: PropTypes.array.isRequired,
	width: PropTypes.number.isRequired,
	ratio: PropTypes.number.isRequired,
	type: PropTypes.oneOf(["svg", "hybrid"]).isRequired,
};

MiniChart.defaultProps = {
	type: "svg",
	height: 600,
};
MiniChart = fitWidth(MiniChart);

export default MiniChart;
