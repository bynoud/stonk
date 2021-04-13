import React from 'react';

import { Chart, SeriesTemplate, CommonSeriesSettings, Title } from 'devextreme-react/chart';

const dataSource = [
    { age: '13-17', number: 5900000 },
    { age: '18-24', number: 38250000 },
    { age: '25-34', number: 52820000 },
    { age: '35-44', number: 38420000 },
    { age: '45-54', number: 32340000 },
    { age: '55-64', number: 14060000 },
    { age: '65+', number: 20020000 }
  ];

class Extdev extends React.Component {
  render() {
    return (
      <Chart
        id="chart"
        palette="Soft"
        dataSource={dataSource}>
        <CommonSeriesSettings
          argumentField="age"
          valueField="number"
          type="bar"
          ignoreEmptyPoints={true}
        />
        <SeriesTemplate nameField="age" />
        <Title
          text="Age Breakdown of Facebook Users in the U.S."
          subtitle="as of January 2017"
        />
      </Chart>
    );
  }
}

export default Extdev;