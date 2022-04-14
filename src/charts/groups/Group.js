import { useState, useEffect } from "react"

import {getGroupTickets, getFocusTickets, updatePrice, ws_open} from '../../connectors/api'
import Header from "./Header"
import MultiChart from './MultiChart'
import './Group.css'

const _FAV_ = '* Favorites *'
const _FOCUS_ = '* Focus *'

const Today = () => {
    const [groups, _setGroup] = useState({})
    const [groupNames, _setGroupName] = useState([])
    const [state, _setState] = useState({
        waiting: true,
        logmsg: '',
        activeTab: '',
        getLive: false,
        refetchHistory: false,
    })
    const [socket, setSocket] = useState(null);
    const [appdb, setAppdb] = useState(null);

    // const setState = (obj) => {
    //   let newState = Object.assign({}, state, obj)
    //   console.log("newstate", obj, newState)
    //   _setState(newState)
    // }
    const setState = (obj) => {
        _setState(st => Object.assign({}, st, obj))
        // console.log("set State", obj, state);
    }
    const setGroup = (obj) => {
        // console.log("set Group", obj, state);
        _setGroup(st => Object.assign({}, st, obj))
        _setGroupName(st => [...new Set([...st,...Object.keys(obj)])])
    }
    const addGroup = (name, tickets) => {
        let obj={}; obj[name] = tickets;
        _setGroup(st => Object.assign({}, st, obj))
        // _setGroupName(st => [name].concat(st))
        _setGroupName(st => [...new Set([name,...st,])])
    }

    const onClickTabItem = (tab) => {
        if (tab === _FOCUS_) {
            getFocusTickets(state.getLive?0:1).then(tickets => {
                addGroup(_FOCUS_, tickets);
                setState({logmsg:'Fetched focus tickets'});
                setState({activeTab: tab})
            })
        } else {
            setState({activeTab: tab})
        }
    }

    // fetch once
    useEffect(() => {
        setState({logmsg:'Fetching ticket groups...'})
        getGroupTickets()
            .then(grp => {
                setGroup(grp)
                setState({logmsg:'Groups fetched'})
            })
            .catch(err => setState({logmsg:`Failed to fetch ticket group: ${err}`}))
            .finally(() => setState({waiting: false}))
        // favoriteTicket('','get')
        //     .then(fav => {
        //         addGroup(_FAV_, fav)
        //         console.log("FAV", fav)
        //     })
        const newWs = ws_open();
        console.log("WS opened")
        newWs.on('appdb', (msg) => {
            console.log("WS on appdb", msg)
            addGroup(_FAV_, msg.fav)
            addGroup(_FOCUS_, [])
            setAppdb(msg)
        })
        newWs.emit('appdb', {op:'get',params:{}})
        setSocket(newWs)
        return () => newWs.close()
    }, [setSocket])

    // const testMe = () => {
    //     fetch('http://localhost:5000/favorite', {method: 'POST',
    //         headers: { 'Content-Type': 'application/json' },
    //         body: JSON.stringify({tic: 'DEF', add:0})
    //     })
    //     .then(response => console.log(response.json()))
    // }
    
    return <div>
        <label>{state.logmsg}</label>
        <button onClick={() => {
            console.log("updating", state);
            updatePrice(state.refetchHistory, state.getLive?0:1)
                .then((stt) => setState({logmsg:`Updated: ${stt}`}))
        }
        }>Update</button>
        <label>
        <input type='checkbox' checked={state.getLive} 
            onChange={() => setState({getLive:!state.getLive})}></input>
            Get Live
        </label>
        <label>
        <input type='checkbox' checked={state.refetchHistory} 
            onChange={() => setState({refetchHistory:!state.refetchHistory})}></input>
            Refetch
        </label>
        <hr/>
        
        <Header groups={groupNames} onClick={onClickTabItem}/>
        {(state.activeTab === '') ? null :
            <MultiChart tickets={groups[state.activeTab]}
                socket={socket} 
                favorites={groups[_FAV_]}
                getLive={state.getLive}></MultiChart>}
        {/* <div className="tab-content">
          {state.groups.map((grp) => {
                if (grp !== state.activeTab) return undefined;
                return child.props.children;
          })}
        </div> */}
    </div>
}
  
export default Today;
  