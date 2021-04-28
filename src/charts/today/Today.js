
import React from "react";
import Chart from './Chart';


const green_color = [
	'#D8F5D1',
	'#CDFFCC',
	'#B0F5AB',
	'#90EF90',
	'#6EF55C',
	'#4AFF37',
];
const red_color = [
	'#FCD5D6',
	'#FFCCCB',
	'#FC94A1',
	'#FC6C85',
	'#FC5F73',
	'#FF5C46',
]
const gray_color = '#DFDADA';

  
const TodayChart = ({ticket, data}) => {

  // const getData = () => {
  //   const requestOptions = {
  //     method: 'POST',
  //     headers: { 'Content-Type': 'application/json' },
  //     body: JSON.stringify({ tic: ticket })
  //   };
  //   console.log('getData .......', ticket)
  //   r = await fetch('http://localhost:5000/today-test', requestOptions)
  //     .then(response => response.json())
  //     .then(data => {
  //       if (data.status != 'ok') {
  //         console.error('Error', data);
  //         return null;
  //       }
  //       else {
  //         console.log("OK", data.payload)
  //         // onFetched();
  //         return data.payload.map( d => {d.date = new Date(d.time * 1000); return d});
  //       }
  //     })
  //   return r;
  // }

  const fill = (d, i) => {
    // console.log('fill',d,i); 
    // return d.buy==0 ? '#ff0000' : d.buy==1 ? '#00ff00' : '#0000ff'
    if (d.buy==0) return red_color[d.weight]; 
    if (d.buy==1) return green_color[d.weight]; 
    return gray_color;
  };

  console.log('Start TodayChart', ticket, data);

  // const data = React.useMemo(() => getData(ticket), [])

  return <Chart  type="hybrid" width={1280} ratio={1.5} data={data} />
}

const Today = () => {
  const [data, setData] = React.useState(null)
  const [state, _setState] = React.useState({ticket:'', waiting: false})

  // const setState = (obj) => {
  //   let newState = Object.assign({}, state, obj)
  //   console.log("newstate", obj, newState)
  //   _setState(newState)
  // }
  const setState = (obj) => {
    // console.log("set State", obj, state);
    _setState(st => Object.assign({}, st, obj))
  }

  const handleChange = (event) => {
    setState({ticket: event.target.value.toUpperCase()})
  }

  const getData = (event) => {
    event.preventDefault();
    const requestOptions = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tic: state.ticket })
    };
    console.log('getData .......', state.ticket)
    setState({waiting:true})
    fetch('http://localhost:5000/today-test', requestOptions)
      .then(response => response.json())
      .then(data => {
        if (data.status != 'ok') {
          console.error('Error', data);
          setData(null);
        }
        else {
          console.log("OK", data.payload)
          // onFetched();
          setData(data.payload.map( d => {
            d.date = new Date(d.time * 1000); 
            d.volume = d.volumn;
            return d
          }))
        }
      })
      .finally(() => setState({waiting:false}))
  }


  // const onSubmit = (event) => {
  //   event.preventDefault();
  //   console.log('submiting xx', state.ticket)
  //   setSubTicket(state.ticket)
  // }

  // const onRenderDone = React.useCallback(() => {
  //   setState({waiting: false})
  // }, [])

  console.log('start Today')

  return <div>
    {/* <button onClick={testpost}>Clickme</button> */}
    <form onSubmit={getData} >
      <fieldset>
        <label>
          <p>Ticket</p>
          <input name="tic" value={state.ticket} onChange={handleChange} />
        </label>
      </fieldset>
      <button type="submit" disabled={state.waiting} >Submit</button>
    </form>
    {data == null ? null : <TodayChart data={data} ticket={state.ticket} />}
  </div>
}


export default Today;
