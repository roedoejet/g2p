
function returnValueFromBlockInput(block, key, lang = 'js') {
    let val;
    if (lang === 'js') {
        val = Blockly.JavaScript.valueToCode(block, key, Blockly.JavaScript.ORDER_ATOMIC)
    } else if (lang === 'py') {
        val = Blockly.Python.valueToCode(block, key, Blockly.Python.ORDER_ATOMIC)
    }
    if (val) {
        return val
    } else {
        return "''"
    }
}

function returnAbbreviations() {
    var varhot = window['varhot']
    let data = varhot.getData()
    let abbreviations = {};
    for (var i = 0; i < data.length; i++) {
        let key = data[i][0];
        if (key && 0 !== key.length) {
            abbreviations[key] = data[i].slice(1, data[i].length)
        }
    }
    return abbreviations
}

let ABBS = returnAbbreviations();
let ABB_KEYS = Object.keys(ABBS);
let ABB_ARGS = [];
for (var i = 0; i < ABB_KEYS.length; i++) {
    ABB_ARGS.push([ABB_KEYS[i], ABB_KEYS[i]])
}

Blockly.defineBlocksWithJsonArray([
    // Block for rule creator.
    {
        "type": "create_rule",
        "message0": "set \"from\" to: %1\nset \"to\" to: %2\nset \"before\" to: %3\nset \"after\" to: %4",
        "args0": [
            {
                "type": "input_value",
                "name": "FROM",
            },
            {
                "type": "input_value",
                "name": "TO",
            },
            {
                "type": "input_value",
                "name": "BEFORE",
            },
            {
                "type": "input_value",
                "name": "AFTER",
            }
        ],
        "previousStatement": null,
        "nextStatement": null,
        "colour": 355,
        "tooltip": "",
        "helpUrl": ""
    }
]);

function setAbbreviations() {
    var options = []
    ABBS = returnAbbreviations();
    ABB_KEYS = Object.keys(ABBS);
    for (var i = 0; i < ABB_KEYS.length; i++) {
        options.push([ABB_KEYS[i], ABB_KEYS[i]])
    }
    ABB_ARGS = options
    return options
}

Blockly.Blocks['abbreviations'] = {
    init: function () {
        var dropdown = new Blockly.FieldDropdown(setAbbreviations);
        this.appendDummyInput().appendField(dropdown, 'VALUE');
        this.setColour(355);
        this.setTooltip('');
        this.setHelpUrl('');
        this.setOutput(true, 'Array')
    },
}

Blockly.JavaScript['abbreviations'] = function (block) {
    var value = block.getFieldValue('VALUE');
    return [JSON.stringify(ABBS[value]), Blockly.JavaScript.ORDER_ATOMIC];
};

Blockly.Python['abbreviations'] = function (block) {
    var value = block.getFieldValue('VALUE');
    return [JSON.stringify(ABBS[value]), Blockly.Python.ORDER_ATOMIC];
};

Blockly.JavaScript['create_rule'] = function (block) {
    code = 'let rule = {};\n';
    let from = returnValueFromBlockInput(block, "FROM")
    code += "rule['from'] = " + from + ";\n"
    let to = returnValueFromBlockInput(block, "TO")
    code += "rule['to'] = " + to + ";\n"
    let before = returnValueFromBlockInput(block, "BEFORE")
    code += "rule['before'] = " + before + ";\n"
    let after = returnValueFromBlockInput(block, "AFTER")
    code += "rule['after'] = " + after + ";\n"
    code += 'console.log(rule);\n'
    code += 'let hot = window["hot"];\n'
    code += 'let rows = hot.countRows();\n'
    code += "hot.alter('insert_row', rows, 1);\n"
    code += "hot.setDataAtCell(rows, 0, rule['from']);\n"
    code += "hot.setDataAtCell(rows, 1, rule['to']);\n"
    code += "hot.setDataAtCell(rows, 2, rule['before']);\n"
    code += "hot.setDataAtCell(rows, 3, rule['after']);\n"
    return code;
}

Blockly.Python['create_rule'] = function (block) {
    code = 'rule = {}\n';
    let from = returnValueFromBlockInput(block, "FROM", lang = 'py')
    code += "rule['from'] = " + from + "\n"
    let to = returnValueFromBlockInput(block, "TO", lang = 'py')
    code += "rule['to'] = " + to + "\n"
    let before = returnValueFromBlockInput(block, "BEFORE", lang = 'py')
    code += "rule['before'] = " + before + "\n"
    let after = returnValueFromBlockInput(block, "AFTER", lang = 'py')
    code += "rule['after'] = " + after + "\n"
    code += 'print(rule)\n'
    return code;
}