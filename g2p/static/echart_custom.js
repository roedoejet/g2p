$(document).ready(function () {
    const myChart = echarts.init(document.getElementById('echart'));
    var option = {
        title: {
            text: ''
        },
        color: '#1EAEDB',
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
                edgeSymbol: ['none', 'arrow'],
                edgeSymbolSize: [0, 10],
                edgeLabel: {
                    normal: {
                        textStyle: {
                            fontSize: 24
                        }
                    }
                },
                data: [{ "name": "a (in-0)", "x": 300, "y": 300 }, { "name": "a (out-0)", "x": 500, "y": 300 }],
                links: [{ "source": 0, "target": 1 }],
                lineStyle: {
                    normal: {
                        color: '#333',
                        opacity: 0.8,
                        width: 2,
                        curveness: 0
                    }
                }
            }
        ]
    };
    // use configuration item and data specified to show chart
    // myChart.setOption(option);

    $(window).on('resize', function () {
        if (myChart != null && myChart != undefined) {
            myChart.resize();
        }
    });

    $(window).trigger('resize');
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
    var convert = function (index = false) {
        if (index) {
            var input_string = $('#indexInput').val();
            if (input_string) {
                socket.emit('index conversion event', {
                    data: {
                        input_string: input_string,
                        mappings: hot.getData(),
                        abbreviations: varhot.getData(),
                        kwargs: getKwargs()
                    }
                });
            }
        } else {
            var input_string = $('#input').val();
            if (input_string) {
                socket.emit('conversion event', {
                    data: {
                        input_string: $('#input').val(),
                        mappings: hot.getData(),
                        abbreviations: varhot.getData(),
                        kwargs: getKwargs()
                    }
                });
            }
        }
    }
    socket.on('index conversion response', function (msg) {
        option.series[0].data = msg.index_data
        option.series[0].links = msg.index_links
        myChart.setOption(option, true)
    });

    $('#indexInput').on('keyup', function (event) {
        convert(index = true)
        return false;
    })
})

