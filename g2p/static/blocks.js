
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

function returnIndex() {
    let elements = document.querySelectorAll('li.title.abbs');
    let index = 0;
    for (var j = 0; j < elements.length; j++) {
        if ('active' in elements[j].classList) { index = j }
    };
    return index
}

function returnAbbreviations() {
    let index = returnIndex()
    var varhot = window['ABBS'][index]
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

let BLOCKLY_ABBS = returnAbbreviations();
let ABB_KEYS = Object.keys(BLOCKLY_ABBS);
let ABB_ARGS = [];
for (var i = 0; i < ABB_KEYS.length; i++) {
    ABB_ARGS.push([ABB_KEYS[i], ABB_KEYS[i]])
}

Blockly.defineBlocksWithJsonArray([
    // Block for rule creator.
    {
        "type": "create_rule",
        "message0": "set \"in\" to: %1\nset \"out\" to: %2\nset \"context_before\" to: %3\nset \"context_after\" to: %4",
        "args0": [
            {
                "type": "input_value",
                "name": "IN",
            },
            {
                "type": "input_value",
                "name": "OUT",
            },
            {
                "type": "input_value",
                "name": "CONTEXT_BEFORE",
            },
            {
                "type": "input_value",
                "name": "CONTEXT_AFTER",
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
    BLOCKLY_ABBS = returnAbbreviations();
    ABB_KEYS = Object.keys(BLOCKLY_ABBS);
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
    return [JSON.stringify(BLOCKLY_ABBS[value]), Blockly.JavaScript.ORDER_ATOMIC];
};

Blockly.Python['abbreviations'] = function (block) {
    var value = block.getFieldValue('VALUE');
    return [JSON.stringify(BLOCKLY_ABBS[value]), Blockly.Python.ORDER_ATOMIC];
};

Blockly.JavaScript['create_rule'] = function (block) {
    code = 'let rule = {};\n';
    let input = returnValueFromBlockInput(block, "IN")
    code += "rule['in'] = " + input + ";\n"
    let output = returnValueFromBlockInput(block, "OUT")
    code += "rule['out'] = " + output + ";\n"
    let before = returnValueFromBlockInput(block, "CONTEXT_BEFORE")
    code += "rule['context_before'] = " + before + ";\n"
    let after = returnValueFromBlockInput(block, "CONTEXTAFTER")
    let index = returnIndex()
    code += "rule['context_after'] = " + after + ";\n"
    code += 'console.log(rule);\n'
    code += 'let hot = window["TABLES"][' + index + '];\n'
    code += 'let rows = hot.countRows();\n'
    code += "hot.alter('insert_row', rows, 1);\n"
    code += "hot.setDataAtCell(rows, 0, rule['in']);\n"
    code += "hot.setDataAtCell(rows, 1, rule['out']);\n"
    code += "hot.setDataAtCell(rows, 2, rule['context_before']);\n"
    code += "hot.setDataAtCell(rows, 3, rule['context_after']);\n"
    return code;
}

Blockly.Python['create_rule'] = function (block) {
    code = 'rule = {}\n';
    let input = returnValueFromBlockInput(block, "IN", lang = 'py')
    code += "rule['in'] = " + input + "\n"
    let output = returnValueFromBlockInput(block, "OUT", lang = 'py')
    code += "rule['out'] = " + output + "\n"
    let before = returnValueFromBlockInput(block, "CONTEXT_BEFORE", lang = 'py')
    code += "rule['context_before'] = " + before + "\n"
    let after = returnValueFromBlockInput(block, "CONTEXT_AFTER", lang = 'py')
    code += "rule['context_after'] = " + after + "\n"
    code += 'print(rule)\n'
    return code;
}