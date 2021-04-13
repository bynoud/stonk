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
} from 'recharts';
import { scaleLog } from 'd3-scale';
import intraData from '../data/intra.json';

const intra = JSON.parse(intraData);

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

const IntraChart = ({intra}) => {
  return (
      <div>
        <LineChart
            width={800}
            height={200}
            data={intra}
            syncId="anyId"
            margin={{
              top: 10,
              right: 30,
              left: 0,
              bottom: 0,
            }}
          >
            <CartesianGrid stroke="#f5f5f5" />
        {/* <XAxis dataKey="name" scale="band" tick={<CustomizedAxisTick />}/> */}
        <XAxis dataKey="label" scale="auto" interval={0} tickSize={7} tickSize={0} /*tick={<CustomizedAxisTick />}*/ /> 
        <YAxis yAxisId="left" type="number" dataKey="mp" name="Price" unit="k" stroke="#8884d8" domain={['auto', 'auto']}/>
        <Tooltip />
        <Line type="basic" yAxisId="left" dataKey="mp" dot={false} stroke="#ff7300" /*label={<CustomizedLabel />}*/ />
      </LineChart>

      <BarChart
            width={800}
            height={200}
            data={intra}
            syncId="anyId"
            margin={{
              top: 10,
              right: 30,
              left: 0,
              bottom: 0,
            }}
          >
        <XAxis dataKey="label" tick={false} /*tick={<CustomizedAxisTick />}*/ /> 
        <YAxis
          yAxisId="right"
          type="number"
          dataKey="vol"
          name="Volumn"
          unit=""
          // orientation="right"
          stroke="#82ca9d"
        />
        <Bar stackId='vol' yAxisId="right" dataKey="buyVol" barSize={5} fill="#70af85" background={backgroundColorFn} />
        {/* <Bar stackId='vol' yAxisId="right" dataKey="buyVol" barSize={5} fill="#70af85" background={{ fill: "#f4c983" }} /> */}
        <Bar stackId='vol' yAxisId="right" dataKey="sellVol" barSize={5} fill="#e40017" /*background={{ fill: "#f4c983" }}*/ />
        <Bar stackId='vol' yAxisId="right" dataKey="unkVol" barSize={5} fill="#C3B998" />
        <Tooltip content={<VolumnTooltip />}/>
        <Brush/>
      </BarChart>

      <LineChart
            width={800}
            height={200}
            data={intra}
            syncId="anyId"
            margin={{
              top: 10,
              right: 30,
              left: 0,
              bottom: 0,
            }}
          >
            {/* <CartesianGrid stroke="#f5f5f5" /> */}
        {/* <XAxis dataKey="name" scale="band" tick={<CustomizedAxisTick />}/> */}
        <XAxis dataKey="label" tick={false}  /*tick={<CustomizedAxisTick />}*/ /> 
        <YAxis yAxisId="left" type="number" dataKey="buyPerc" name="Price" unit="%" stroke="#8884d8" domain={[0, 100]}/>
        <Tooltip />
        <Line type="basic" yAxisId="left" dataKey="buyPerc" dot={false} stroke="#ff7300" /*label={<CustomizedLabel />}*/ />
      </LineChart>

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


const Intra = () => {
  const [state, _setState] = React.useState({ticket:'', intra:intra, waiting: false})

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
    // console.log(state.ticket.toUpperCase(), state.intra);
    setState({waiting: true})
    const requestOptions = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tic: state.ticket })
    };
    fetch('http://localhost:5000/intra', requestOptions)
        .then(response => {
          console.log(response.body);
          return response.json()})
        .then(data => {
          if (data.status != 'ok') console.error('Error', data)
          else setState({intra: data.payload})
          console.log("OK", data)
        })
        .finally(() => setState({waiting: false}))
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
    {(state.intra != null) ? <IntraChart intra={state.intra}/> : null}
  </div>
}

export default Intra;
