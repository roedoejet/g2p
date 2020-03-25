var TABLES = []
var ABBS = []

// index graph echart
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
                        fontSize: 36
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

$(window).on('resize', function () {
    if (myChart != null && myChart != undefined) {
        myChart.resize();
    }
});

function createSettings(index, data) {
    let include = 'checked';
    let as_is = '';
    let case_sensitive = '';
    let escape_special = '';
    let reverse = '';
    let active = '';
    let out_delimiter = '';
    let prevent_feeding = '';
    let norm_form = 'NFC';
    if (index === 0) {
        active = 'active'
    }
    if ('include' in data && data['include']) {
        include = 'checked'
    }
    if (data['as_is']) {
        as_is = 'checked'
    }
    if (data['case_sensitive']) {
        case_sensitive = 'checked'
    }
    if (data['escape_special']) {
        escape_special = 'checked'
    }
    if (data['reverse']) {
        reverse = 'checked'
    }
    if (data['prevent_feeding']) {
        prevent_feeding = 'checked'
    }
    if (data['out_delimiter']) {
        out_delimiter = data['out_delimiter']
    }
    if (data['norm_form']) {
        norm_form = data['norm_form']
    }
    let settings_template = `
    <div class='${active} settings'>
        <form>
            <fieldset>
                <div></div>
                <div>
                    <input ${include} class='include' id='include-${index}' type='checkbox' name='include' value='include'>
                        <label for='include'>Include rules in output</label>
                </div>
                <div>
                    <input ${as_is} checked id='as_is-${index}' type='checkbox' name='as_is' value='as_is'>
                        <label for='as_is'>Leave order as is</label>
                </div>
                <div>
                    <input  ${case_sensitive} checked id='case_sensitive-${index}' type='checkbox' name='case_sensitive'
                        value='case_sensitive'>
                        <label for='case_sensitive'>Rules are case sensitive</label>
                </div>
                <div>
                    <input ${escape_special} id='escape_special-${index}' type='checkbox' name='escape_special' value='escape_special'>
                        <label for='escape_special'>Escape special characters</label>
                </div>
                <div>
                    <input ${reverse} id='reverse-${index}' type='checkbox' name='reverse' value='reverse'>
                        <label for='reverse'>Reverse the rules</label>
                </div>
                <div>
                <input ${prevent_feeding} id='prevent_feeding-${index}' type='checkbox' name='prevent_feeding' value='prevent_feeding'>
                    <label for='reverse'>Prevent all rules from feeding</label>
                </div>
                 <div>
                    <label for='reverse'>Normalization</label>
                    <input id='norm_form-${index}' type='text' name='norm_form' value='${norm_form}' maxlength='4' minlength='3'>
                </div>
                <div>
                <label for='out_delimiter'>Output Delimiter</label>
                <input id='out_delimiter-${index}' type='text' name='out_delimiter' value='${out_delimiter}' placeholder='delimiter' maxlength='1'>
            </div>
        </fieldset>
    </form>
</div>`
    $('#settings-container').append(settings_template)
    document.getElementById(`include-${index}`).addEventListener('click', function (event) {
        const include = event.target.checked
        setKwargs(index, { as_is })
    })

    document.getElementById(`as_is-${index}`).addEventListener('click', function (event) {
        const as_is = event.target.checked
        setKwargs(index, { as_is })
    })

    document.getElementById(`case_sensitive-${index}`).addEventListener('click', function (event) {
        const case_sensitive = event.target.checked
        setKwargs(index, { case_sensitive })
    })

    document.getElementById(`escape_special-${index}`).addEventListener('click', function (event) {
        const escape_special = event.target.checked
        setKwargs(index, { escape_special })
    })

    document.getElementById(`reverse-${index}`).addEventListener('click', function (event) {
        const reverse = event.target.checked
        setKwargs(index, { reverse })
    })

    document.getElementById(`out_delimiter-${index}`).addEventListener('change', function (event) {
        const out_delimiter = event.target.value
        setKwargs(index, { out_delimiter })
    })
}

function createAbbs(index, data) {
    let id = 'abbs-' + index
    let el = '<div class="abbs-container" id="' + id + '-container"><div id="' + id + '"></div></div>';
    if (index === 0) {
        el = '<div class="abbs-container active" id="' + id + '-container"><div id="' + id + '"></div></div>';
    }
    $("#abbs-table-container").append(el)
    var hotVarElement = document.querySelector('#abbs-' + index);
    var hotVarSettings = {
        data: data,
        stretchH: 'all',
        // width: 880,
        autoWrapRow: true,
        height: 287,
        maxRows: 150,
        rowHeaders: true,
        colHeaders: true,
        afterRowMove: (rows, target) => {
            convert()
        },
        manualRowMove: true,
        manualColumnMove: false,
        manualColumnResize: true,
        manualRowResize: true,
        exportFile: true,
        licenseKey: 'non-commercial-and-evaluation'
    };
    var hotVar = new Handsontable(hotVarElement, hotVarSettings);
    const callback = (mutationsList, observer) => {
        for (var mutation of mutationsList) {
            if (mutation.attributeName == 'class' && !mutation.target.hidden) {
                hotVar.refreshDimensions();
            }
        }
    };
    const observer = new MutationObserver(callback);
    const targetNode = document.getElementById('abbs-' + index + '-container');
    const config = { attributes: true };
    observer.observe(targetNode, config);
    ABBS.push(hotVar)
    return hotVar
}
function createTable(index, data) {
    let id = 'hot-' + index
    let el = '<div class="hot-container" id="' + id + '-container"><div id="' + id + '"></div></div>';
    if (index === 0) {
        el = '<div class="hot-container active" id="' + id + '-container"><div id="' + id + '"></div></div>';
    }
    $("#table-container").append(el)
    var hotElement = document.querySelector('#hot-' + index);
    let headers = [...new Set([].concat(...data.map(x => Object.keys(x))))]
    let headerLabels = headers.map(header => header.replace('_', ' ').split(' ').map(x => { return x.charAt(0).toUpperCase() + x.slice(1) }).join(' '))
    var hotSettings = {
        data: data,
        columns: headers.map(x => { return { 'data': x, type: 'text' } }),
        stretchH: 'all',
        width: 880,
        autoWrapRow: true,
        height: 287,
        maxRows: 250,
        rowHeaders: true,
        colHeaders: headerLabels,
        afterRowMove: (rows, target) => {
            convert()
        },
        manualRowMove: true,
        manualColumnMove: false,
        manualColumnResize: true,
        manualRowResize: true,
        exportFile: true,
        licenseKey: 'non-commercial-and-evaluation'
    };
    var hot = new Handsontable(hotElement, hotSettings);
    const callback = (mutationsList, observer) => {
        for (var mutation of mutationsList) {
            if (mutation.attributeName == 'class' && !mutation.target.hidden) {
                hot.refreshDimensions();
            }
        }
    };

    const observer = new MutationObserver(callback);
    const targetNode = document.getElementById('hot-' + index + '-container');
    const config = { attributes: true };
    observer.observe(targetNode, config);
    TABLES.push(hot)
    $(id).on('change', function (event) {
        convert()
        return false;
    })
    return hot
}
var size = 10;
var dataObject = []
var varsObject = []
var settingsObject = { 'include': true, 'as_is': true, 'case_sensitive': true, 'escape_special': false, 'reverse': false }
for (var j = 0; j < size; j++) {
    dataObject.push({
        "in": '',
        "out": '',
        "context_before": '',
        "context_after": ''
    });
    if (j === 0) {
        varsObject.push(['Vowels', 'a', 'e', 'i', 'o', 'u'])
    }
    varsObject.push(['', '', '', '', '', ''])
};
// Create Initial table
createTable(0, dataObject)
createAbbs(0, varsObject)
createSettings(0, settingsObject)

document.getElementById("export-abbs").addEventListener("click", function (event) {
    varhot.getPlugin("exportFile").downloadFile("csv", { filename: "abbreviations" });
})

// Kwargs

document.getElementById('standard-radio').addEventListener('click', function (event) {
    if ($('#standard').is(":hidden")) {
        $('#input').val($('#indexInput').val())
        convert()
        $('#animated').hide()
        $('#standard').show()
    }
})

getIncludedIndices = function () {
    indices = []
    let mappings = $(".include")
    for (var j = 0; j < mappings.length; j++) {
        if (mappings[j].checked) {
            indices.push(j)
        }
    }
    return indices
}

getIncludedMappings = function () {
    let indices = getIncludedIndices()
    let mappings = []
    if (TABLES.length === indices.length && ABBS.length === indices.length) {
        for (index of indices) {
            mapping = {}
            mapping['mapping'] = TABLES[index].getData()
            mapping['abbreviations'] = ABBS[index].getData()
            mapping['kwargs'] = getKwargs(index)
            mappings.push(mapping)
        }
    }
    return mappings
}

var getKwargs = function (index) {
    const as_is = document.getElementById(`as_is-${index}`).checked
    const case_sensitive = document.getElementById(`case_sensitive-${index}`).checked
    const escape_special = document.getElementById(`escape_special-${index}`).checked
    const reverse = document.getElementById(`reverse-${index}`).checked
    const include = document.getElementById(`include-${index}`).checked
    const out_delimiter = document.getElementById(`out_delimiter-${index}`).value
    const prevent_feeding = document.getElementById(`prevent_feeding-${index}`).checked
    const norm_form = document.getElementById(`norm_form-${index}`).value
    return { as_is, case_sensitive, escape_special, reverse, include, out_delimiter, norm_form, prevent_feeding }
}

var setKwargs = function (index, kwargs) {
    if ('as_is' in kwargs) {
        document.getElementById(`as_is-${index}`).checked = kwargs['as_is']
    }
    if ('case_sensitive' in kwargs) {
        document.getElementById(`case_sensitive-${index}`).checked = kwargs['case_sensitive']
    }
    if ('escape_special' in kwargs) {
        document.getElementById(`escape_special-${index}`).checked = kwargs['escape_special']
    }
    if ('reverse' in kwargs) {
        document.getElementById(`reverse-${index}`).checked = kwargs['reverse']
    }
    if ('prevent_feeding' in kwargs) {
        document.getElementById(`prevent_feeding-${index}`).checked = kwargs['prevent_feeding']
    }
    if ('include' in kwargs) {
        document.getElementById(`include-${index}`).checked = kwargs['include']
    }
    if ('out_delimiter' in kwargs) {
        document.getElementById(`out_delimiter-${index}`).value = kwargs['out_delimiter']
    }
    if ('norm_form' in kwargs) {
        document.getElementById(`norm_form-${index}`).value = kwargs['norm_form']
    }
    convert()
}

var conversionSocket = io.connect('//' + document.domain + ':' + location.port + '/convert');
var connectionSocket = io.connect('//' + document.domain + ':' + location.port + '/connect');
var tableSocket = io.connect('//' + document.domain + ':' + location.port + '/table');

var trackIndex = function () {
    return $('#animated-radio').is(":checked")
}

var convert = function () {
    // prevent conversion from happening before TABLES, ABBS, and SETTINGS are populated.
    if (TABLES.length > 0 && ABBS.length > 0) {
        let index = trackIndex()
        var input_string = $('#input').val();
        if (index) {
            input_string = $('#indexInput').val();
        }
        if (input_string) {
            let mappings = getIncludedMappings()
            conversionSocket.emit('conversion event', {
                data: {
                    index,
                    input_string,
                    mappings
                }
            });
        }
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
conversionSocket.on('conversion response', function (msg) {
    let index = trackIndex()
    if (index) {
        // Convert after any changes to tables
        option.series[0].data = msg.index_data
        option.series[0].links = msg.index_links
        myChart.setOption(option, true)
        $(window).trigger('resize');
    } else {
        $('#output').val(msg['output_string']);
    }
});

connectionSocket.on('connection response', function (msg) {
    $('#log').text('(' + msg.data + ')')
})

connectionSocket.on('disconnect', function () {
    $('#log').text('(Disconnected)')
})

function showTable(index) {
    let containers = $(".hot-container")
    for (var j = 0; j < containers.length; j++) {
        $('.hot-container').eq(j).removeClass('active')
        $('li.title.rules').eq(j).removeClass('active')
        if (index === j) {
            $('li.title.rules').eq(j).addClass('active')
            $('.hot-container').eq(j).addClass('active')
        }
    }
    convert()
}

function showAbbs(index) {
    let containers = $(".abbs-container")
    for (var j = 0; j < containers.length; j++) {
        $('.abbs-container').eq(j).removeClass('active')
        $('li.title.abbs').eq(j).removeClass('active')
        if (index === j) {
            $('li.title.abbs').eq(j).addClass('active')
            $('.abbs-container').eq(j).addClass('active')
        }
    }
    convert()
}

function showSettings(index) {
    let containers = $(".settings")
    for (var j = 0; j < containers.length; j++) {
        $('div.settings').eq(j).removeClass('active')
        $('li.title.settings').eq(j).removeClass('active')
        if (index === j) {
            $('li.title.settings').eq(j).addClass('active')
            $('div.settings').eq(j).addClass('active')
        }
    }
    convert()
}

tableSocket.on('table response', function (msg) {
    // msg arg is list of {
    //  mappings: io pairs to be applied to hot table 
    //  abbs: abbreviations to be included in abbreviations table
    //  kwargs: settings to be added to settings forms
    // }
    TABLES = []
    ABBS = []
    // Clear navs
    $("#table-nav").empty()
    $("#settings-nav").empty()
    $('#abbs-nav').empty()
    // Clear others
    $("#table-container").empty()
    $('#abbs-table-container').empty()
    $('#settings-container').empty()

    for (var j = 0; j < msg.length; j++) {
        // Create nav element
        let table_nav_li = '<li class="title rules"><a onclick="showTable(' + j + ')" id="link-' + j + '">' + msg[j]['kwargs']['display_name'] + '</a></li>'
        let abbs_nav_li = '<li class="title abbs"><a onclick="showAbbs(' + j + ')" id="link-' + j + '">' + msg[j]['kwargs']['display_name'] + '</a></li>'
        let settings_nav_li = '<li class="title settings"><a onclick="showSettings(' + j + ')" id="link-' + j + '">' + msg[j]['kwargs']['display_name'] + '</a></li>'
        if (j === 0) {
            table_nav_li = '<li class="active title rules"><a onclick="showTable(' + j + ')" id="link-' + j + '">' + msg[j]['kwargs']['display_name'] + '</a></li>'
            abbs_nav_li = '<li class="active title abbs"><a onclick="showAbbs(' + j + ')" id="link-' + j + '">' + msg[j]['kwargs']['display_name'] + '</a></li>'
            settings_nav_li = '<li class="active title settings"><a onclick="showSettings(' + j + ')" id="link-' + j + '">' + msg[j]['kwargs']['display_name'] + '</a></li>'
        }
        // append nav element
        $("#table-nav").append(table_nav_li)
        $('#settings-nav').append(settings_nav_li.replace('showTable', 'showSettings'))
        $('#abbs-nav').append(abbs_nav_li.replace('showTable', 'showAbbs'))
        // update other elements
        createAbbs(j, msg[j]['abbs'])
        createSettings(j, msg[j]['kwargs'])
        createTable(j, msg[j]['mappings'])
    }
    // convert
    convert()
})

$('#input').on('keyup', function (event) {
    convert()
    return false;
})
$('#indexInput').on('keyup', function (event) {
    convert(index = true)
    return false;
})
$('#hot-add').click(function (event) {
    let active = $('li.title.rules.active')
    let index = $('li.title.rules').index(active)
    rows = TABLES[index].countRows()
    TABLES[index].alter('insert_row', rows)
})
$('#varhot-add-col').click(function (event) {
    let active = $('li.title.abbs.active')
    let index = $('li.title.abbs').index(active)
    cols = ABBS[index].countCols()
    ABBS[index].alter('insert_col', cols)
})
$('#varhot-add-row').click(function (event) {
    let active = $('li.title.abbs.active')
    let index = $('li.title.abbs').index(active)
    rows = ABBS[index].countRows()
    ABBS[index].alter('insert_row', rows)
})
$('#export-abbs').click(function (event) {
    let active = $('li.title.abbs.active')
    let index = $('li.title.abbs').index(active)
    ABBS[index].getPlugin("exportFile").downloadFile("csv", { filename: "rules" });
})
$('#export-rules').click(function (event) {
    let active = $('li.title.rules.active')
    let index = $('li.title.rules').index(active)
    TABLES[index].getPlugin("exportFile").downloadFile("csv", { filename: "rules" });
})
$('#langselect').change(function () {
    var selected = $("#langselect option:selected").val();
    var in_lang = selected;
    var out_lang = selected;
    if (selected !== 'custom') {
        var arr = selected.split('-to-');
        in_lang = arr[0]
        out_lang = arr[1]
    }
    tableSocket.emit('table event', { in_lang: in_lang, out_lang: out_lang })
})

$(document).ready(function () {
    $.ajax({
        url: "/api/v1/langs",
        dataType: "json",
        success: function (response) {
            $.each(response, function (index, value) {
                $("#input-langselect").append("<option value=" + value + ">" + value + "</option>")
            })
        }
    });

    $("#input-langselect").on('change', function (event) {
        let in_lang = $("#input-langselect option:selected").val()
        $.ajax({
            url: "/api/v1/descendants/" + in_lang,
            dataType: "json",
            success: function (response) {
                $("#output-langselect").empty()
                $.each(response, function (index, value) {
                    $("#output-langselect").append("<option value=" + value + ">" + value + "</option>")
                })
                changeTable()
            },
            error: function (xhr, ajaxOptions, thrownError) {
                if (xhr.status == 404) {
                    $('#input-langselect option[value=custom]').attr('selected', 'selected');
                    $("#output-langselect").empty();
                    $("#output-langselect").append("<option value='custom' selected>Custom</option>");
                    changeTable()
                }
            }
        });
    })

    function changeTable() {
        let in_lang = $("#input-langselect option:selected").val()
        let out_lang = $("#output-langselect option:selected").val()
        tableSocket.emit('table event', { in_lang, out_lang })
    }

    $("#output-langselect").on('change', function (event) {
        changeTable()
    })

});
