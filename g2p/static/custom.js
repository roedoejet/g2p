var TABLES = []
function create_table(index, data) {
    let id = 'hot-' + index
    let el = '<div class="hot-container" id="' + id + '-container"><div id="' + id + '"></div></div>';
    if (index === 0) {
        el = '<div class="hot-container active" id="' + id + '-container"><div id="' + id + '"></div></div>';
    }
    $("#table-container").append(el)
    var hotElement = document.querySelector('#hot-' + index);
    var hotSettings = {
        data: data,
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
        width: 880,
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
    document.getElementById("export-rules").addEventListener("click", function (event) {
        hot.getPlugin("exportFile").downloadFile("csv", { filename: "rules" });
    })
    TABLES.push(hot)
    return hot
}
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
var hotVarElement = document.querySelector('#varhot');
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
var varhot = new Handsontable(hotVarElement, hotVarSettings);

// Create Initial table
create_table(0, dataObject)

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
    if ($('#standard').is(":hidden")) {
        $('#input').val($('#indexInput').val())
        convert()
        $('#animated').hide()
        $('#standard').show()
    }
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

var conversionSocket = io.connect('//' + document.domain + ':' + location.port + '/convert');
var connectionSocket = io.connect('//' + document.domain + ':' + location.port + '/connect');
var tableSocket = io.connect('//' + document.domain + ':' + location.port + '/table');

var convert = function () {
    var active = $('#table-nav li.title.active')
    var index = $('#table-nav li.title').index(active)
    var input_string = $('#input').val();
    if (input_string) {
        conversionSocket.emit('conversion event', {
            data: {
                input_string: $('#input').val(),
                mappings: TABLES[index].getData(),
                abbreviations: varhot.getData(),
                kwargs: getKwargs()
            }
        });
    }
}
// Convert after any changes to tables
Handsontable.hooks.add('afterChange', convert)

conversionSocket.on('conversion response', function (msg) {
    $('#output').val(msg['output_string']);
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
        $('li.title').eq(j).removeClass('active')
        if (index === j) {
            $('li.title').eq(j).addClass('active')
            $('.hot-container').eq(j).addClass('active')
        }
    }
    convert()
}

tableSocket.on('table response', function (msg) {
    TABLES = []
    $("#table-nav").empty()
    $("#table-container").empty()
    for (var j = 0; j < msg.length; j++) {
        let li = '<li class="title"><a onclick="showTable(' + j + ')" id="link-' + j + '">' + msg[j]['kwargs']['display_name'] + '</a></li>'
        if (j === 0) {
            li = '<li class="active title"><a onclick="showTable(' + j + ')" id="link-' + j + '">' + msg[j]['kwargs']['display_name'] + '</a></li>'
        }
        $("#table-nav").append(li)
        create_table(j, msg[j]['mappings'])
    }
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
