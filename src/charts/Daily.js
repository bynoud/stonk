import React, { PureComponent } from 'react';
import {
  ComposedChart,
  Line,
  Area,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Scatter,
  ResponsiveContainer,
  ReferenceLine,
  Brush,
  LineChart,
  BarChart,
  Cell,
} from 'recharts';
import { scaleLog } from 'd3-scale';

// import intraData from '../data/intra.json';
// const intra = JSON.parse(intraData);

// const data = [
//   {
//     name: 'Page A',
//     uv: 590,
//     pv: 0,
//     amt: 1400,
//     cnt: 490,
//   },
//   {
//     name: 'Page B',
//     uv: 868,
//     pv: 0,
//     amt: 1506,
//     cnt: 590,
//   },
//   {
//     name: 'Page C',
//     uv: 0,
//     pv: 10098,
//     amt: 989,
//     cnt: 350,
//   },
//   {
//     name: 'Page D',
//     uv: 1480,
//     pv: 0,
//     amt: 1228,
//     cnt: 480,
//   },
//   {
//     name: '',
//     uv: 0,
//     pv: 1108,
//     amt: 1100,
//     cnt: 460,
//   },
//   {
//     name: 'Page F',
//     uv: 0,
//     pv: 680,
//     amt: 1700,
//     cnt: 380,
//   },
// ];

// const scale = scaleLog().base(Math.E);

const data = [
  {label: 'aaa', mp: 10, vol: 20, buyVol: 0, sellVol: 20, unkVol:0},
  {label: '', mp: 11, vol: 30, buyVol: 30, sellVol: 0, unkVol:0},
  {label: '', mp: 12, vol: 40, buyVol: 40, sellVol: 0, unkVol:0},
  {label: 'bbb', mp: 13, vol: 10, buyVol: 0, sellVol: 0, unkVol:10},
]

class CustomizedLabel extends PureComponent {
    render() {
      const { x, y, stroke, value } = this.props;
      console.log(x,y,stroke, value)
    
      if (value == 0) return null;
      return (
        <text x={x} y={y} dy={-4} fill={stroke} fontSize={10} textAnchor="middle">
          {value}
        </text>
      );
    }
}

class CustomizedAxisTick extends PureComponent {
    render() {
      const { x, y, stroke, payload } = this.props;
      console.log(x,y,payload.value)
  
      return (
        <g transform={`translate(${x},${y})`}>
          <text x={0} y={0} dy={16} textAnchor="end" fill="#666" transform="rotate(-35)">
            {payload.value}
          </text>
        </g>
      );
    }
}

const VolumnTooltip = ({ active, payload, label }) => {
  // console.log('tool', active, payload, label)
  if (active && payload && payload.length) {
    let vol = 0;
    let kind = '';
    for (const p of payload) {
      if (p.value != 0) {
        vol = p.value;
        kind = p.name;
      }
    }
    // vol = Math.ceil(Math.pow(2, vol))
    return (
      <div className="custom-tooltip">
        {/* <p className='label'>{payload[3].value}</p> */}
        <p className="label">{`${kind} : ${vol}`}</p>
        {/* <p className="intro">{getIntroOfPage(label)}</p> */}
        {/* <p className="desc">Anything you want can be displayed here.</p> */}
      </div>
    );
  }

  return null;
};


const getPath = (x, y, width, height) => `M ${x},${y} h ${width} v ${height} h -${width} Z`;
const backgroundColorFn = ({x,y,width,height, buyVol, sellVol}) => {
  const fill = (buyVol>0) ? "#c6ebc9" : (sellVol>0) ? "#f4c983" : "";
  if (fill === '') return null;
  return <path x={x} y={y} width={width} height={height} fill={fill} className="recharts-rectangle recharts-bar-background-rectangle" radius="0" d={getPath(x, y, width, height)}></path>
}

const PosNegColorBar = (props) => {
  const { fill, x, y, width, height } = props;
  // console.log(fill, x, y, width, height)
  let c = height > 0 ? "#70af85" : "#e40017";
  return <path d={getPath(x, y, width, height)} stroke="none" fill={c} fillOpacity="0.3"/>;
};

const DailyChart = ({daily}) => {
  const [state, _setState] = React.useState({moveX:-1})
  const setState = (obj) => {
    _setState(st => Object.assign({}, st, obj))
  }

  const moveMove = (obj) => {
    // console.log(obj)
    if (obj != null & obj.activeTooltipIndex != null) setState({moveX: obj.activeTooltipIndex})
  }
  const moveLeave = () => { setState({moveX: -1}) }

  console.log("daily", daily)

  return (
      <div>
        {state.moveX < 0 ? <p style={{textAlign:'left'}}> Close....</p> :
          <p style={{textAlign:'left'}}>
            <span>Close: {daily[state.moveX].close} </span>
            <span>Vol {daily[state.moveX].vol} ({daily[state.moveX].buyVol} - {daily[state.moveX].sellVol}) </span>
            <span>volRSI {daily[state.moveX].volRsi} ({daily[state.moveX].volRsiChg}) </span>
            <span>RSI {daily[state.moveX].rsi} ({daily[state.moveX].rsiChg})</span>
          </p>}

        <LineChart
            width={800}
            height={200}
            data={daily}
            syncId="anyId"
            margin={{
              top: 0,
              right: 0,
              left: 0,
              bottom: 0,
            }}
            onMouseMove={moveMove}
            onMouseLeave={moveLeave}
          >
            <CartesianGrid stroke="#f5f5f5" />
        <XAxis dataKey="label" scale="auto" interval={0} tickSize={7} tickSize={0} /> 
        <YAxis yAxisId="left" type="number" dataKey="close" name="Price" unit="k" stroke="#8884d8" domain={['auto', 'auto']}/>
        <Tooltip content={() => null} />
        <Line type="basic" yAxisId="left" dataKey="close" dot={false} stroke="#ff7300" />
      </LineChart>

      <ComposedChart
            width={800}
            height={150}
            data={daily}
            syncId="anyId"
            margin={{
              top: 0,
              right: 0,
              left: 0,
              bottom: 0,
            }}
            onMouseMove={moveMove}
            onMouseLeave={moveLeave}
          >
        <XAxis dataKey="label" tick={false}  /> 
        <YAxis
          yAxisId="right"
          type="number"
          dataKey="vol"
          name="Volumn"
          unit=""
          // orientation="right"
          stroke="#82ca9d"
          domain={['auto','auto']}
        />
        <Bar stackId='vol' yAxisId="right" dataKey="buyVol" barSize={5} fill="#70af85" />
        <Bar stackId='vol' yAxisId="right" dataKey="sellVol" barSize={5} fill="#e40017" />
        <Line type="basic" yAxisId="right" dataKey="volAvg" dot={false} stroke="#ff7300" />
        <Tooltip content={() => null} />
        {/* <Tooltip /> */}
      </ComposedChart>

      <ComposedChart
            width={800}
            height={100}
            data={daily}
            syncId="anyId"
            margin={{
              top: 0,
              right: 0,
              left: 0,
              bottom: 0,
            }}
            onMouseMove={moveMove}
            onMouseLeave={moveLeave}
          >
        <XAxis dataKey="day" tick={false} /> 
        <YAxis type="number" yAxisId="left" dataKey="volRsi" name="Price" unit="k" stroke="#8884d8" />
        <YAxis type="number" yAxisId="right" dataKey="volRsiChg" orientation='right' hide={true} name="Price" unit="k" stroke="#8884d8" />
        <Tooltip content={() => null} />
        {/* <Tooltip /> */}

        <Line type="basic" yAxisId="left" dataKey="volRsi" dot={false} stroke="#70af85" />
        <ReferenceLine y={50} yAxisId='left' />
        <ReferenceLine y={75} yAxisId='left'/>

        <Bar stackId='vol' yAxisId="right" dataKey="volRsiChg" barSize={5} fill="#70af85"
          shape={<PosNegColorBar />}/>
      </ComposedChart>
      
      {/* <BarChart
            width={800}
            height={100}
            data={daily}
            syncId="anyId"
            margin={{
              top: 10,
              right: 30,
              left: 0,
              bottom: 0,
            }}
          >
        <XAxis dataKey="day" tick={false}  /> 
        <YAxis
          yAxisId="right"
          type="number"
          dataKey="volRsiChg"
          name="Volumn"
          unit=""
          stroke="#82ca9d"
        />
        <Bar stackId='vol' yAxisId="right" dataKey="volRsiChg" barSize={5} fill="#70af85" />
        <Tooltip />
      </BarChart> */}

      <ComposedChart
            width={800}
            height={150}
            data={daily}
            syncId="anyId"
            margin={{
              top: 0,
              right: 0,
              left: 0,
              bottom: 0,
            }}
            onMouseMove={moveMove}
            onMouseLeave={moveLeave}
          >
        <XAxis dataKey="day" tick={false} /> 
        <YAxis type="number" dataKey="rsi" name="Price" unit="k" stroke="#8884d8" />
        <Tooltip content={() => null} />
        {/* <Tooltip /> */}
        <Line type="basic" dataKey="rsi" dot={false} stroke="#70af85" />
        <ReferenceLine y={70} />
        <ReferenceLine y={50} />
        <ReferenceLine y={30} />

        <YAxis
          yAxisId="right"
          type="number"
          dataKey="rsiChg"
          name="Volumn"
          unit=""
          orientation="right"
          stroke="#82ca9d"
          hide={true}
        />
        <Bar stackId='vol' yAxisId="right" dataKey="rsiChg" barSize={5} fill="#70af85" shape={<PosNegColorBar />}/>
        <ReferenceLine yAxisId="right" y={0} />

        <Brush/>

      </ComposedChart>

        {/* <BarChart
            width={800}
            height={100}
            data={daily}
            syncId="anyId"
            margin={{
              top: 10,
              right: 30,
              left: 0,
              bottom: 0,
            }}
          >
        <XAxis dataKey="day" tick={false}  /> 
        <YAxis
          yAxisId="right"
          type="number"
          dataKey="rsiChg"
          name="Volumn"
          unit=""
          // orientation="right"
          stroke="#82ca9d"
        />
        <Bar stackId='vol' yAxisId="right" dataKey="rsiChg" barSize={5} fill="#70af85" shape={<PosNegColorBar />}/>
        <Tooltip />
        <ReferenceLine yAxisId="right" y={0} />
      </BarChart> */}

    </div>
  );
}

// const getIntra = (event) => {
//   event.preventDefault();
//   console.log(event);
//   return;
//   const requestOptions = {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json' },
//     body: JSON.stringify({ tic: 'EVG' })
//   };
//   fetch('http://localhost:5000/intra', requestOptions)
//       .then(response => response.json())
//       .then(data => console.log('post response', data));
// }


const Daily = () => {
  const [state, _setState] = React.useState({ticket:'', intra:null, waiting: false})

  // const setState = (obj) => {
  //   let newState = Object.assign({}, state, obj)
  //   console.log("newstate", obj, newState)
  //   _setState(newState)
  // }
  const setState = (obj) => {
    console.log("set State", obj, state);
    _setState(st => Object.assign({}, st, obj))
  }

  const getIntra = (event) => {
    event.preventDefault();
    console.log(state.ticket.toUpperCase(), state.intra);
    setState({waiting: true})
    const requestOptions = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tic: state.ticket })
    };
    fetch('http://localhost:5000/daily', requestOptions)
        .then(response => {
          console.log(response.body);
          return response.json()})
        .then(data => {
          if (data.status != 'ok') console.error('Error', data)
          else setState({intra: data.payload, waiting: false})
          console.log(state, data)
        })
        .catch(() => setState({waiting: false}))
  }

  const handleChange = (event) => {
    setState({ticket: event.target.value.toUpperCase()})
  }

  return <div>
    {/* <button onClick={testpost}>Clickme</button> */}
    <form onSubmit={getIntra} >
      <fieldset>
        <label>
          <p>Ticket</p>
          <input name="tic" value={state.ticket} onChange={handleChange} />
        </label>
      </fieldset>
      <button type="submit" disabled={state.waiting} >Submit</button>
    </form>
    {(state.intra != null) ? <DailyChart daily={state.intra}/> : null}
  </div>
}

export default Daily;
