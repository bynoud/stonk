import logo from './logo.svg';
import './App.css';
// import TestLine from './charts/TestLine';
// import Intraday from './charts/Intraday';
// import Extdev from './charts/Extdev';
// import LineChart from './charts/Chartjs';
import Intra from './charts/Intra';
// import Intra from './charts/Intra_combine';
import Daily from './charts/Daily';
import Today from './charts/today/Today';
import Group from './charts/groups/Group';

// import ChartComponent from './charts/SChart/index';
// import ChartComponent from './charts/SChart/Area/index';
// import ChartComponent from './charts/SChart/StackedBar/index';
import ChartComponent from './charts/SChart/Candle/index';

import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link
} from "react-router-dom";

function App() {
  return (
    // <div>
    //   <div className="App">
    //     <Intra/>
    //     <Daily/>
    //     <Schart/>
    //     <Example/>
    //   </div>

    // </div>
    <Router>
      <div>
        {/* <ul>
          <li>
            <Link to="/">Home</Link>
          </li>
          <li>
            <Link to="/intra">Intra</Link>
          </li>
        </ul>

        <hr /> */}

        {/*
          A <Switch> looks through all its children <Route>
          elements and renders the first one whose path
          matches the current URL. Use a <Switch> any time
          you have multiple routes, but you want only one
          of them to render at a time
        */}
        <Switch>
          <Route exact path="/">
            <Daily />
          </Route>
          <Route path="/intra">
            <Intra />
          </Route>
          <Route path="/test">
            <ChartComponent />
          </Route>
          <Route path="/today">
            <Today />
          </Route>
          <Route path="/group">
            <Group />
          </Route>
        </Switch>
      </div>
    </Router>

  );
}

export default App;
