import React from 'react';
import { render } from 'react-dom';
import Chart from './LineScater';
import { getData } from "./utils";

import { TypeChooser } from "react-stockcharts/lib/helper";

class TestLine extends React.Component {
	componentDidMount() {
		getData().then(data => {
			this.setState({ data })
		})
	}
	render() {
		if (this.state == null) {
			return <div>Loading...</div>
		}
		return (
			<TypeChooser>
				{type => <Chart type={type} data={this.state.data} />}
			</TypeChooser>
		)
	}
}

export default TestLine;