
import React from 'react'
import Chart from './Chart'
import { getTicketPrice } from '../../connectors/api'

const MultiChart = ({tickets, favorites, socket, getLive}) => {
    const [data, _setData] = React.useState({})
    console.log("MultiChart", tickets)
    const setData = (key, prices) => {
        let obj = {};
        obj[key] = prices;
        console.log("Updating", obj)
        _setData(st => Object.assign({}, st, obj))
    }

    // const refresh = (ticket) => {
    //     console.log("refreshing", ticket)
    //     getTicketPrice(ticket).then(d => setData(ticket,d))
    // }

    // React.useEffect(() => {
    //     tickets.map(ticket => refresh(ticket))
    // }, [])

    // return (<div>
    //     {Object.keys(data).map(ticket => {
    //         return <Chart key={ticket} ticket={ticket} data={data[ticket]}></Chart>
    //     })}
    // </div>)
    return (<div>
        {tickets.map(ticket => {
            return <Chart key={ticket} ticket={ticket} isFav={favorites.includes(ticket)}
                socket={socket} getLive={getLive}
                type="hybrid" width={600} height={300} ratio={1.5}
            ></Chart>
        })}
    </div>)
}

export default MultiChart;