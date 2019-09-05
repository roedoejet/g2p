

var size = 10;
var dataObject = []
var varsObject = []
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
var hotElement = document.querySelector('#hot');
var hotVarElement = document.querySelector('#varhot');
var hotSettings = {
    data: dataObject,
    columns: [
        {
            data: 'in',
            type: 'text'
        },
        {
            data: 'out',
            type: 'text'
        },
        {
            data: 'context_before',
            type: 'text'
        },
        {
            data: 'context_after',
            type: 'text'
        }
    ],
    stretchH: 'all',
    // width: 880,
    autoWrapRow: true,
    height: 287,
    maxRows: 250,
    rowHeaders: true,
    colHeaders: [
        'In',
        'Out',
        'Context Before',
        'Context After'
    ],
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
var hotVarSettings = {
    data: varsObject,
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
var hot = new Handsontable(hotElement, hotSettings);
var varhot = new Handsontable(hotVarElement, hotVarSettings);
document.getElementById("export-rules").addEventListener("click", function (event) {
    hot.getPlugin("exportFile").downloadFile("csv", { filename: "rules" });
})
document.getElementById("export-abbs").addEventListener("click", function (event) {
    varhot.getPlugin("exportFile").downloadFile("csv", { filename: "abbreviations" });
})

// Settings & Kwargs

document.getElementById('as_is').addEventListener('click', function (event) {
    const as_is = event.target.checked
    setKwargs({ as_is })
})

document.getElementById('case_sensitive').addEventListener('click', function (event) {
    const case_sensitive = event.target.checked
    setKwargs({ case_sensitive })
})

document.getElementById('escape_special').addEventListener('click', function (event) {
    const escape_special = event.target.checked
    setKwargs({ escape_special })
})

document.getElementById('reverse').addEventListener('click', function (event) {
    const reverse = event.target.checked
    setKwargs({ reverse })
})

document.getElementById('standard-radio').addEventListener('click', function (event) {
    $('#animated').hide()
    $('#standard').show()
})

document.getElementById('animated-radio').addEventListener('click', function (event) {
    $('#standard').hide()
    $('#animated').show()
    $(window).trigger('resize');
})

var getKwargs = function () {
    const as_is = document.getElementById('as_is').checked
    const case_sensitive = document.getElementById('case_sensitive').checked
    const escape_special = document.getElementById('escape_special').checked
    const reverse = document.getElementById('reverse').checked
    return { as_is, case_sensitive, escape_special, reverse }
}

var setKwargs = function (kwargs) {
    if ('as_is' in kwargs) {
        document.getElementById('as_is').checked = kwargs['as_is']
    }
    if ('case_sensitive' in kwargs) {
        document.getElementById('case_sensitive').checked = kwargs['case_sensitive']
    }
    if ('escape_special' in kwargs) {
        document.getElementById('escape_special').checked = kwargs['escape_special']
    }
    if ('reverse' in kwargs) {
        document.getElementById('reverse').checked = kwargs['reverse']
    }
    convert()
}

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

socket.on('conversion response', function (msg) {
    $('#output').text(msg['output_string']);
});

socket.on('connection response', function (msg) {
    $('#log').text('(' + msg.data + ')')
})

socket.on('table response', function (msg) {
    console.log(msg)
    hot.loadData(msg['mappings'])
    varhot.loadData(msg['abbs'])
    setKwargs(msg['kwargs'])
    convert()
})

$('#input').on('keyup', function (event) {
    convert()
    return false;
})
$('#hot').on('change', function (event) {
    convert()
    // convert(index = true)
    return false;
})
$('#hot-add').click(function (event) {
    rows = hot.countRows()
    hot.alter('insert_row', rows)
})
$('#varhot-add-col').click(function (event) {
    cols = varhot.countCols()
    varhot.alter('insert_col', cols)
})
$('#varhot-add-row').click(function (event) {
    rows = varhot.countRows()
    varhot.alter('insert_row', rows)
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
    socket.emit('table event', { in_lang: in_lang, out_lang: out_lang })
})

$('#animate').change(function () {
    var selected = $("#animate")[0].checked
    if (selected) {
        $('#echart').css({ 'display': 'inherit' })
    } else {
        $('#echart').css({ 'display': 'none' })
    }
})