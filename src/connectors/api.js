
import io from 'socket.io-client'

const _URL = 'http://localhost:5000'

const _dopost = (endpoint, body=null) => {
    const opts = {method: 'POST'}
    if (body != null) {
        opts['headers'] = { 'Content-Type': 'application/json' }
        opts['body'] = JSON.stringify(body)
    }
    return fetch(_URL + endpoint, opts)
        .then(response => response.json())
        .then(data => {
            if (data.status != 'ok') {
                console.error('Error', data);
                return null;
            }
            else {
                // console.log("OK", data.payload)
                return data.payload
            }
        })
}

const getGroupTickets = () => {
    return _dopost('/grouped-tickets')
}

const getTicketPrice = (tic) => {
    return _dopost('/abv-test', {tic})
}

const favoriteTicket = (tic, op) => {
    return _dopost('/favorite', {tic, op})
}

const updatePrice = (refetch,tillDate=1) => {
    return _dopost('/update-intra', {tillDate:tillDate,refetch:refetch})
}

let _WS = null
const ws_open = () => {
    if (_WS == null || !_WS.connected) _WS = io(_URL+'/test')
    return _WS
}

export {getGroupTickets, getTicketPrice, favoriteTicket,
        updatePrice,
        ws_open}