$(document).ready(function () {
    const langsChart = echarts.init(document.getElementById('langsechart'));
    var langsOption = {
        animationDurationUpdate: 1500,
        animationEasingUpdate: 'quinticInOut',
        legend: [{
            // selectedMode: 'single',
            // selected: {'},
            data: ['alq', 'atj', 'ckt', 'clc', 'crj', 'crl', 'crx', 'ctp', 'dan', 'eng', 'fra', 'generated', 'git', 'hei', 'iku', 'kwk', 'moh', 'nav', 'norm', 'str', 'tgx', 'und', 'win']
        }],
        series: [
            {
                type: 'graph',
                layout: 'force',
                // progressiveThreshold: 700,
                data: [],
                links: [],
                categories: [{'name': 'alq'}, {'name': 'atj'}, {'name': 'ckt'}, {'name': 'clc'}, {'name': 'crj'}, {'name': 'crl'}, {'name': 'crx'}, {'name': 'ctp'}, {'name': 'dan'}, {'name': 'eng'}, {'name': 'fra'}, {'name': 'generated'}, {'name': 'git'}, {'name': 'hei'}, {'name': 'iku'}, {'name': 'kwk'}, {'name': 'moh'}, {'name': 'nav'}, {'name': 'norm'}, {'name': 'str'}, {'name': 'tgx'}, {'name': 'und'}, {'name': 'win'}],
                circular: {
                    rotateLabel: true
                },
                emphasis: {
                    label: {
                        position: 'right',
                        show: true
                    }
                },
                roam: true,
                focusNodeAdjacency: true,
                lineStyle: {
                    width: 0.5,
                    curveness: 0.3,
                    opacity: 0.7,
                    color: 'source'
                }
            }
        ]
    }
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
        if (langsChart != null && langsChart != undefined) {
            langsChart.resize();
        }
    });

    $(window).trigger('resize');
    var conversionSocket = io.connect('//' + document.domain + ':' + location.port + '/convert');
    var convert = function () {
        var input_string = $('#indexInput').val();
        if (input_string) {
            conversionSocket.emit('index conversion event', {
                data: {
                    input_string: input_string,
                    mappings: hot.getData(),
                    abbreviations: varhot.getData(),
                    kwargs: getKwargs()
                }
            });
        }
    }
    document.getElementById('animated-radio').addEventListener('click', function (event) {
        if ($('#animated').is(":hidden")) {
            $('#indexInput').val($('#input').val())
            convert()
            $('#standard').hide()
            $('#animated').show()
            $(window).trigger('resize');
        }
    })
    // Convert after any changes to tables
    Handsontable.hooks.add('afterChange', convert)
    conversionSocket.on('index conversion response', function (msg) {
        option.series[0].data = msg.index_data
        option.series[0].links = msg.index_links
        myChart.setOption(option, true)
        $(window).trigger('resize');
    });
    $.ajax({
        url: "/static/languages-network.json",
        dataType: "json",
        success: function (response) {
            // 'name': node, 'symbolSize': size, 'id': node, 'category'
            langsOption.series[0].data = response['nodes'].map(x => {
                return { 'name': x.name, 'symbolSize': x.symbolSize, 'id': x.id, 'category': x.category }
            })
            langsOption.series[0].links = response['edges']
            langsChart.setOption(langsOption, true)
        }
    });
    $('#show-langs').click(function (event) {
        $('#langsechart').show()
        $('#show-langs').hide()
        $('#hide-langs').show()
        $(window).trigger('resize');
    })
    $('#hide-langs').click(function (event) {
        $('#langsechart').hide()
        $('#hide-langs').hide()
        $('#show-langs').show()
    })
    $('#indexInput').on('keyup', function (event) {
        convert()
        return false;
    })
    $('#hot').on('change', function (event) {
        convert()
        return false;
    })
})

