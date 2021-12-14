
import { useState } from "react"

const Header = ({groups, onClick}) => {
    const [state, _setState] = useState({activeTab:''})
    const setState = (obj) => {
        // console.log("set State", obj, state);
        _setState(st => Object.assign({}, st, obj))
    }

    const onTabClick = (tab) => {
        setState({activeTab: tab})
        onClick(tab)
        // console.log("Header clicked", state)
    }

    console.log("Header", groups, onClick)

    return (
        <ol className="tab-list">
            {groups.map((grp) => {
                let className = 'tab-list-item'
                if (state.activeTab == grp) className += ' tab-list-active';
                return (
                    <li className={className}
                        key={grp}
                        onClick={() => onTabClick(grp)}>{grp}</li>
                );
            })}
        </ol>
    )
}

export default Header;