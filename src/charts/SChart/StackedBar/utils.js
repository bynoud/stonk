

import { tsvParse, csvParse } from  "d3-dsv";
import { timeParse } from "d3-time-format";

function parseData(parse) {
	return function(d) {
		d.date = parse(d.date);
		d.open = +d.open;
		d.high = +d.high;
		d.low = +d.low;
		d.close = +d.close;
		d.volume = +d.volume;

		return d;
	};
}


export function getData() {
	const promiseBarData = fetch("https://cdn.rawgit.com/rrag/react-stockcharts/master/docs/data/groupedBarData.json")
		.then(response => response.json())
		.then(groupedBarData => {
            return [
                {x:'a', y1:12, y2:20, y3:0},
                {x:'', y1:34, y2:23, y3:1},
                {x:'', y1:22, y2:52, y3:1},
                {x:'', y1:22, y2:52, y3:1},
                {x:'', y1:22, y2:52, y3:1},
            ]
			// return groupedBarData.map(d => {
            //     return d;
			// 	// return {
			// 	// 	y: d.x,
			// 	// 	x1: d.y1,
			// 	// 	x2: d.y2,
			// 	// 	x3: d.y3,
			// 	// 	x4: d.y4,
			// 	// };
			// });
		});
	return promiseBarData;
}
