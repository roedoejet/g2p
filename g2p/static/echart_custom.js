$(document).ready(function () {
    const langsChart = echarts.init(document.getElementById('langsechart'));
    var langsOption = {
        animationDurationUpdate: 1500,
        animationEasingUpdate: 'quinticInOut',
        legend: [{}],
        series: [
            {
                type: 'graph',
                layout: 'force',
                // progressiveThreshold: 700,
                data: [],
                links: [],
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
    $(window).on('resize', function () {
        if (langsChart != null && langsChart != undefined) {
            langsChart.resize();
        }
    });
    $.ajax({
        url: "/static/languages-network.json",
        dataType: "json",
        success: function (response) {
            let categories = response['nodes'].map(x => x.category)
            langsOption.series[0].data = response['nodes'].map(x => {
                return { 'name': x.name, 'symbolSize': x.symbolSize, 'id': x.id, 'category': x.category }
            })
            langsOption['legend']['data'] = categories
            langsOption['series'][0]['categories'] = Array.from(new Set(categories)).map(x => { return { 'name': x } })
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
})

