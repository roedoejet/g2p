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
    series: [{
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
    }]
};

$(window).on('resize', function() {
    if (myChart != null && myChart != undefined) {
        myChart.resize();
    }
});

function createSettings(index, data) {
    let include = 'checked';
    let rule_ordering = '';
    let case_sensitive = '';
    let preserve_case = '';
    let escape_special = '';
    let reverse = '';
    let active = '';
    let out_delimiter = '';
    let prevent_feeding = '';
    let norm_form = 'NFC';
    let type = 'mapping';
    let in_lang = '';
    let out_lang = '';
    if (index === 0) {
        active = 'active'
    }
    if ('include' in data && data['include']) {
        include = 'checked'
    }
    if (data['rule_ordering'] === 'as-written') {
        rule_ordering = 'as-written'
    } else {
        rule_ordering = 'apply-longest-first'
    }
    if (data['case_sensitive']) {
        case_sensitive = 'checked'
    }
    if (data['preserve_case']) {
        preserve_case = 'checked'
    }
    if (data['escape_special']) {
        escape_special = 'checked'
    }
    // Don't reverse because reversed mappings already come reversed
    // if (data['reverse']) {
    //     reverse = 'checked'
    // }
    if (data['prevent_feeding']) {
        prevent_feeding = 'checked'
    }
    if (data['out_delimiter']) {
        out_delimiter = data['out_delimiter']
    }
    if (data['norm_form']) {
        norm_form = data['norm_form']
    }
    if (data['type']) {
        type = data['type']
    }
    // For lexicon mappings, we can only use the built-in mapping
    if (type == ['lexicon']) {
        in_lang = data['in_lang']
        out_lang = data['out_lang']
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
                    <input  ${case_sensitive} id='case_sensitive-${index}' type='checkbox' name='case_sensitive'
                        value='case_sensitive'>
                    <label for='case_sensitive'>Rules are case sensitive</label>
                </div>
                <div>
                    <input ${preserve_case} id='preserve_case-${index}' type='checkbox' name='preserve_case' value='preserve_case'>
                    <label for='preserve_case'>Preserve input case in output</label>
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
                    <label for='prevent_feeding'>Prevent all rules from feeding</label>
                </div>
                <div>
                    <label for='rule_ordering'>Rule Ordering Approach</label>
                    <select id='rule_ordering-${index}' name='rule_ordering'>
                    <option ${rule_ordering === 'apply-longest-first' ? "selected" : ""} value='apply-longest-first'>Longest first</option>
                    <option ${rule_ordering === 'as-written' ? "selected" : ""} value='as-written'>As written</option>
                    </select>
                </div>
                <div>
                    <label for='reverse'>Normalization</label>
                    <input id='norm_form-${index}' type='text' name='norm_form' value='${norm_form}' maxlength='4' minlength='3'>
                </div>
                <div>
                    <label for='out_delimiter'>Output Delimiter</label>
                    <input id='out_delimiter-${index}' type='text' name='out_delimiter' value='${out_delimiter}' placeholder='delimiter' maxlength='1'>
                </div>
                <input id='type-${index}' type='hidden' name='type' value='${type}' maxlength='20' minlength='0'>
                <input id='in_lang-${index}' type='hidden' name='in_lang' value='${in_lang}' maxlength='20' minlength='0'>
                <input id='out_lang-${index}' type='hidden' name='out_lang' value='${out_lang}' maxlength='20' minlength='0'>
            </fieldset>
        </form>
    </div>`
    $('#settings-container').append(settings_template)
    document.getElementById(`include-${index}`).addEventListener('click', function(event) {
        const include = event.target.checked
        setKwargs(index, { include })
    })

    $(`#rule_ordering-${index}`).on('change', function(event) {
        const rule_ordering = $(`#rule_ordering-${index}`).val()
        setKwargs(index, { rule_ordering })
    })

    document.getElementById(`case_sensitive-${index}`).addEventListener('click', function(event) {
        const case_sensitive = event.target.checked
        if (case_sensitive) {
            document.getElementById(`preserve_case-${index}`).checked = false
        }
        setKwargs(index, { case_sensitive })
    })

    document.getElementById(`preserve_case-${index}`).addEventListener('click', function(event) {
        const preserve_case = event.target.checked
        if (preserve_case) {
            document.getElementById(`case_sensitive-${index}`).checked = false
        }
        setKwargs(index, { preserve_case })
    })

    document.getElementById(`escape_special-${index}`).addEventListener('click', function(event) {
        const escape_special = event.target.checked
        setKwargs(index, { escape_special })
    })

    document.getElementById(`reverse-${index}`).addEventListener('click', function(event) {
        const reverse = event.target.checked
        setKwargs(index, { reverse })
    })

    document.getElementById(`out_delimiter-${index}`).addEventListener('change', function(event) {
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
        colHeaders: ["Abbreviation Name"],
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
        columns: headers.map(x => { if (x !== "prevent_feeding") { return { 'data': x, type: 'text' } } else { return { 'data': x, type: 'checkbox' } } }),
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
    $(id).on('change', function(event) {
        convert()
        return false;
    })
    return hot
}
var size = 10;
var dataObject = []
var varsObject = []
var settingsObject = { 'include': true, 'rule_ordering': "as-written", 'case_sensitive': true, 'preserve_case': false, 'escape_special': false, 'reverse': false }
for (var j = 0; j < size; j++) {
    dataObject.push({
        "in": '',
        "out": '',
        "context_before": '',
        "context_after": '',
        "prevent_feeding": false
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

document.getElementById('standard-radio').addEventListener('click', function(event) {
    if ($('#standard').is(":hidden")) {
        $('#input').val($('#indexInput').val())
        convert()
        $('#animated').hide()
        $('#standard').show()
    }
})

getIncludedIndices = function() {
    indices = []
    let mappings = $(".include")
    for (var j = 0; j < mappings.length; j++) {
        if (mappings[j].checked) {
            indices.push(j)
        }
    }
    return indices
}

getIncludedMappings = function() {
    let indices = getIncludedIndices()
    let mappings = []
    if (TABLES.length === indices.length && ABBS.length === indices.length) {

        for (index of indices) {
            mapping = {}
            let kwargs = getKwargs(index)
            if (kwargs["type"] == "lexicon")
                mapping['rules'] = null;
            else
                mapping['rules'] = TABLES[index].getSourceData().filter(v => v.in)
                // Extract only non-empty rules and abbreviations for processing
            mapping['abbreviations'] = ABBS[index].getData().filter(v => v[0])
            mapping['kwargs'] = getKwargs(index)
            mappings.push(mapping)
        }
    }
    return mappings
}

var getKwargs = function(index) {
    const rule_ordering = $(`#rule_ordering-${index}`).val()
    const case_sensitive = document.getElementById(`case_sensitive-${index}`).checked
    const preserve_case = document.getElementById(`preserve_case-${index}`).checked
    const escape_special = document.getElementById(`escape_special-${index}`).checked
    const reverse = document.getElementById(`reverse-${index}`).checked
    const include = document.getElementById(`include-${index}`).checked
    const out_delimiter = document.getElementById(`out_delimiter-${index}`).value
    const prevent_feeding = document.getElementById(`prevent_feeding-${index}`).checked
    const norm_form = document.getElementById(`norm_form-${index}`).value
    const type = document.getElementById(`type-${index}`).value
    if (type === "lexicon") {
        const in_lang = document.getElementById(`in_lang-${index}`).value
        const out_lang = document.getElementById(`out_lang-${index}`).value
        // Lexicon G2P cannot be customized (FIXME: likewise for unidecode actually)
        return { type, in_lang, out_lang }
    } else
        return {
            rule_ordering,
            case_sensitive,
            preserve_case,
            escape_special,
            reverse,
            include,
            out_delimiter,
            norm_form,
            prevent_feeding,
            type
        }
}

var setKwargs = function(index, kwargs) {
    if ('rule_ordering' in kwargs) {
        $(`#rule_ordering-${index}`).val(kwargs['rule_ordering'])
    }
    if ('case_sensitive' in kwargs) {
        document.getElementById(`case_sensitive-${index}`).checked = kwargs['case_sensitive']
    }
    if ('preserve_case' in kwargs) {
        document.getElementById(`preserve_case-${index}`).checked = kwargs['preserve_case']
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
    if ('type' in kwargs) {
        document.getElementById(`type-${index}`).value = kwargs['type']
    }
    if ('in_lang' in kwargs) {
        document.getElementById(`in_lang-${index}`).value = kwargs['in_lang']
    }
    if ('out_lang' in kwargs) {
        document.getElementById(`out_lang-${index}`).value = kwargs['out_lang']
    }
    convert()
}

var magicalMysteryOptions = { path: '/ws/socket.io', transports: ['websocket', 'polling', 'flashsocket']};
var conversionSocket = io('/convert', magicalMysteryOptions)
var connectionSocket = io('/connect', magicalMysteryOptions)
var tableSocket = io('/table', magicalMysteryOptions)

var trackIndex = function() {
    return $('#animated-radio').is(":checked")
}

var convert = function() {
    // prevent conversion from happening before TABLES, ABBS, and SETTINGS are populated.
    if (TABLES.length == 0 || ABBS.length == 0)
        return;
    let index = trackIndex()
    var input_string = $('#input').val();
    if (index) {
        input_string = $('#indexInput').val();
    }
    let mappings = getIncludedMappings()
    // we will still request a conversion if the input is empty (that
    // way if you delete it you aren't stuck with a phantom output)
    conversionSocket.emit('conversion event', {
        data: {
            index,
            input_string,
            mappings
        }
    });
}

document.getElementById('animated-radio').addEventListener('click', function(event) {
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
conversionSocket.on('conversion response', function(msg) {
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

connectionSocket.on('connection response', function(msg) {
    $('#log').text('(' + msg.data + ')')
})

connectionSocket.on('disconnect', function() {
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

tableSocket.on('table response', function(msg) {
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

$('#input').on('keyup', function(event) {
    convert()
    return false;
})
$('#indexInput').on('keyup', function(event) {
    convert(index = true)
    return false;
})
$('#hot-add').click(function(event) {
    let active = $('li.title.rules.active')
    let index = $('li.title.rules').index(active)
    rows = TABLES[index].countRows()
    TABLES[index].alter('insert_row', rows)
})
$('#varhot-add-col').click(function(event) {
    let active = $('li.title.abbs.active')
    let index = $('li.title.abbs').index(active)
    cols = ABBS[index].countCols()
    ABBS[index].alter('insert_col', cols)
})
$('#varhot-add-row').click(function(event) {
    let active = $('li.title.abbs.active')
    let index = $('li.title.abbs').index(active)
    rows = ABBS[index].countRows()
    ABBS[index].alter('insert_row', rows)
})
$('#export-abbs').click(function(event) {
    let active = $('li.title.abbs.active')
    let index = $('li.title.abbs').index(active)
    // TODO: filter out lines where the first column (i.e., the abbreviation name) is empty
    ABBS[index].getPlugin("exportFile").downloadFile("csv", { filename: "abbreviations" });
})
$('#export-rules').click(function(event) {
    let active = $('li.title.rules.active')
    let index = $('li.title.rules').index(active)
    // TODO: filter out lines where .in is empty
    TABLES[index].getPlugin("exportFile").downloadFile("csv", { filename: "rules" });
})
$('#langselect').change(function() {
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

$(document).ready(function() {
    $.ajax({
        url: "/api/v1/langs",
        dataType: "json",
        success: function(response) {
            $.each(response, function(index, value) {
                $("#input-langselect").append("<option value=" + value + ">" + value + "</option>")
            })
        }
    });

    $("#input-langselect").on('change', function(event) {
        let in_lang = $("#input-langselect option:selected").val()
        $.ajax({
            url: "/api/v1/descendants/" + in_lang,
            dataType: "json",
            success: function(response) {
                $("#output-langselect").empty()
                $.each(response, function(index, value) {
                    $("#output-langselect").append("<option value=" + value + ">" + value + "</option>")
                })
                changeTable()
            },
            error: function(xhr, ajaxOptions, thrownError) {
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

    $("#output-langselect").on('change', function(event) {
        changeTable()
    })

});
