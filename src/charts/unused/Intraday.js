
import React from "react";
import Chart from 'react-apexcharts';
import intra from '../data/intra.json';

function generateDayWiseTimeSeries(baseval, count, yrange) {
    var i = 0;
    var series = [];
    while (i < count) {
        // var x = baseval;
        var x = i;
        var y =
        Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;

        series.push([x, y]);
        baseval += 86400000;
        i++;
    }
    return series;
}

var data = generateDayWiseTimeSeries(new Date("22 Apr 2017").getTime(), 3, {
    min: 30,
    max: 90
});

var options1 = {
    chart: {
        id: "chart2",
        type: "line",
        height: 230,
        foreColor: "#ccc",
        toolbar: {
            autoSelected: "pan",
            show: false
        }
    },
    colors: ["#2E93fA"],
    // stroke: {
    //     width: 4,
    //     curve: 'straight',
    //     colors: ['#2E93fA']
    // },
    grid: {
        borderColor: "#555",
        clipMarkers: false,
        // yaxis: {
        //     lines: {
        //         show: false
        //     }
        // }
    },
    dataLabels: {
        enabled: false
    },
    // fill: {
    //     gradient: {
    //         enabled: true,
    //         opacityFrom: 0.55,
    //         opacityTo: 0
    //     }
    // },
    fill: {
        colors: ['#2E93fA']
    },
    markers: {
        size: 2,
        colors: ["#000524"],
        strokeColor: "#00BAEC",
        strokeWidth: 3
    },
    series: [
        {
            data: data
        }
    ],
    tooltip: {
        theme: "dark"
    },
    xaxis: {
        // type: "datetime"
        type: "numeric"
    },
    yaxis: {
        min: 0,
        tickAmount: 4
    }
};

var options2 = {
    chart: {
    id: "chart1",
    height: 130,
    type: "bar",
    foreColor: "#ccc",
    brush: {
        target: "chart2",
        enabled: true
    },
    selection: {
        enabled: true,
        fill: {
            color: "#ffffff",
            opacity: 0.4
        },
        xaxis: {
            // min: new Date("27 Jul 2017 10:00:00").getTime(),
            // max: new Date("14 Aug 2017 10:00:00").getTime()
            min: 0,
            max: 2
        }
    }
    },
    colors: [function({ value, seriesIndex, w }) {
        console.log(value, seriesIndex, w);
        return "#00ff00";
    }],
    series: [
    {
        data: [[1,11],[2,0],[3,33]]
    },
    {
        data: [[1,0], [2,22], [3,0]]
    }
    ],
    stroke: {
        width: 2
    },
    grid: {
        borderColor: "#444"
    },
    markers: {
        size: 0
    },
    xaxis: {
        // type: "datetime",
        type: "numeric",
        tooltip: {
            enabled: false
        }
    },
    yaxis: {
        tickAmount: 2
    }
};
  

function Intraday () {
    return (<div>
        <div id="chart-area"><Chart options={options1} series={options1.series} type={options1.chart.type} height={options1.chart.height}></Chart></div>
        <div id="chart-bar"><Chart options={options2} series={options2.series} type={options2.chart.type} height={options2.chart.height}></Chart></div>
    </div>)
}
  
  

// class Intraday extends React.Component {
//     constructor(props) {
//       super(props);
//       this.intra = JSON.parse(intra);
//       console.log(this.intra);

//       this.state = {
      
//         series: [{
//           name: 'Peter',
//           data: [5, 5, 10, 8, 7, 5, 4, null, null, null, 10, 10, 7, 8, 6, 9]
//         }, {
//           name: 'Johnny',
//           data: [10, 15, null, 12, null, 10, 12, 15, null, null, 12, null, 14, null, null, null]
//         }, {
//           name: 'David',
//           data: [null, null, null, null, 3, 4, 1, 3, 4,  6,  7,  9, 5, null, null, null]
//         }],
//         options: {
//           chart: {
//             height: 350,
//             type: 'line',
//             zoom: {
//               enabled: false
//             },
//             animations: {
//               enabled: false
//             }
//           },
//           stroke: {
//             width: [5,5,4],
//             curve: 'straight'
//           },
//           labels: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
//           title: {
//             text: 'Missing data (null values)'
//           },
//           xaxis: {
//           },
//         },
      
      
//       };
//     }

  

//     render() {
//         return (
//             <div id="chart">
//                 <Chart options={this.state.options} series={this.state.series} type="line" height={350} />
//             </div>
//         );
//     }
// }

export default Intraday;