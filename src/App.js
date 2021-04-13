import logo from './logo.svg';
import './App.css';
// import TestLine from './charts/TestLine';
// import Intraday from './charts/Intraday';
// import Extdev from './charts/Extdev';
// import LineChart from './charts/Chartjs';
import Intra from './charts/Intra';
// import Intra from './charts/Intra_combine';
import Daily from './charts/Daily';


function App() {
  return (
    <div>
      <div className="App">
        {/* <Intra/> */}
        <Daily/>
        {/* <Example/> */}
      </div>

    </div>

  );
}

export default App;
