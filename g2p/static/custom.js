

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
    maxRows: 150,
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

var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
var convert = function () {
    socket.emit('conversion event', { data: { input_string: $('#input').val(), mappings: hot.getData(), abbreviations: varhot.getData() } });
}
socket.on('conversion response', function (msg) {
    $('#output').text(msg['output_string']);
});
socket.on('connection response', function (msg) {
    console.log(msg)
    $('#log').text('(' + msg.data + ')')
})
socket.on('table response', function (msg) {
    console.log(msg)
    hot.loadData(msg['mappings'])
    varhot.loadData(msg['abbs'])
    convert()
})
$('#input').on('keyup', function (event) {
    convert()
    return false;
})
$('#hot').on('change', function (event) {
    convert()
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
    if (selected !== 'custom') {
        var arr = selected.split('-');
        var lang = arr[0]
        var table = arr[1]
        socket.emit('table event', { lang: lang, table: table })
    } else {
        socket.emit('table event', { lang: 'custom', table: 'custom' })
    }
})

$('#animate').change(function () {
    var selected = $("#animate")[0].checked
    if (selected) {
        $('#echart').css({ 'display': 'inherit' })
    } else {
        $('#echart').css({ 'display': 'none' })
    }
})