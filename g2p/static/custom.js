
$(document).ready(function () {
    var size = 10;
    var dataObject = []
    for (var j = 0; j < size; j++) {
        dataObject.push({
            from: '',
            to: '',
            before: '',
            after: ''
        })
    };
    var hotElement = document.querySelector('#hot');
    var hotElementContainer = hotElement.parentNode;
    var hotSettings = {
        data: dataObject,
        columns: [
            {
                data: 'from',
                type: 'text'
            },
            {
                data: 'to',
                type: 'text'
            },
            {
                data: 'before',
                type: 'text'
            },
            {
                data: 'after',
                type: 'text'
            }
        ],
        stretchH: 'all',
        // width: 880,
        autoWrapRow: true,
        height: 287,
        maxRows: 22,
        rowHeaders: true,
        colHeaders: [
            'From',
            'To',
            'Context Before',
            'Context After'
        ],
        afterRowMove: (rows, target) => {
            convert()
        },
        manualRowMove: true,
        manualColumnMove: false,
        exportFile: true,
        licenseKey: 'non-commercial-and-evaluation'
    };
    var hot = new Handsontable(hotElement, hotSettings);
    document.getElementById("export-csv").addEventListener("click", function (event) { hot.getPlugin("exportFile").downloadFile("csv", { filename: "Cors CSV Export example" }); })

    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
    var convert = function () {
        socket.emit('conversion event', { data: { input_string: $('#input').val(), cors: hot.getData() } });
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
        hot.loadData(msg['cors'])
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
});