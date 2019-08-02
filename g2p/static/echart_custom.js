$(document).ready(function () {
    var myChart = echarts.init(document.getElementById('echart'));
    var option = {
        title: {
            text: 'g2p Indices'
        },
        tooltip: {},
        animationDurationUpdate: 1500,
        animationEasingUpdate: 'quinticInOut',
        series: [
            {
                type: 'graph',
                layout: 'none',
                symbolSize: 70,
                roam: true,
                label: {
                    normal: {
                        show: true
                    }
                },
                edgeSymbol: ['circle', 'arrow'],
                edgeSymbolSize: [4, 10],
                edgeLabel: {
                    normal: {
                        textStyle: {
                            fontSize: 20
                        }
                    }
                },
                data: [{
                    name: 't (in-1)',
                    x: 300,
                    y: 300,
                }, {
                    name: 'e (in-2)',
                    x: 300,
                    y: 350
                }, {
                    name: 's (in-3)',
                    x: 300,
                    y: 400
                }, {
                    name: 't (in-4)',
                    x: 300,
                    y: 450,
                },
                {
                    name: 'p (out-1)',
                    x: 500,
                    y: 300
                }, {
                    name: 'e (out-2)',
                    x: 500,
                    y: 350
                }, {
                    name: 's (out-3)',
                    x: 500,
                    y: 400
                }, {
                    name: 't (out-4)',
                    x: 500,
                    y: 450
                }],
                // links: [],
                links: [{
                    source: 0,
                    target: 4,
                    symbolSize: [5, 20]
                }, {
                    source: 0,
                    target: 5,
                    symbolSize: [5, 20]
                }, {
                    source: 0,
                    target: 6,
                    symbolSize: [5, 20],
                }, {
                    source: 1,
                    target: 5,
                    symbolSize: [5, 20],
                }],
                lineStyle: {
                    normal: {
                        opacity: 0.9,
                        width: 2,
                        curveness: 0
                    }
                }
            }
        ]
    };
    // use configuration item and data specified to show chart
    myChart.setOption(option);
})