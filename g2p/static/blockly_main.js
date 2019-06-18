(function () {
    let currentButton;
    function exportJS() {
        let ws = Blockly.getMainWorkspace()
        Blockly.JavaScript.addReservedWords('code');
        let code = Blockly.JavaScript.workspaceToCode(ws)
        alert(code)
        return code
    }
    function exportPY(codeType) {
        let ws = Blockly.getMainWorkspace()
        Blockly.Python.addReservedWords('code');
        let code = Blockly.Python.workspaceToCode(ws)
        alert(code)
        return code
    }

    function add() {
        let ws = Blockly.getMainWorkspace()
        Blockly.JavaScript.addReservedWords('code');
        var code = Blockly.JavaScript.workspaceToCode(
            ws
        );
        try {
            console.log(code)
            eval(code)
        } catch (error) {
            console.log(error)
        }
    }

    function clear() {
        let ws = Blockly.getMainWorkspace()
        ws.clear()
    }

    function handleAdd() {
        add();
        // clear();
    }

    document.querySelector('#clear').addEventListener('click', clear);
    document.querySelector('#add').addEventListener('click', handleAdd);
    document.querySelector('#exportJS').addEventListener('click', exportJS)
    document.querySelector('#exportPY').addEventListener('click', exportPY)

    Blockly.inject('blockly-div', {
        toolbox: document.getElementById('toolbox'),
        toolboxPosition: 'end',
        horizontalLayout: true,
        scrollbars: false
    });


})();
