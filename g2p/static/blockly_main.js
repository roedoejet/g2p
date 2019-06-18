(function () {
    let currentButton;

    function add() {
        let ws = Blockly.getMainWorkspace()
        Blockly.JavaScript.addReservedWords('code');
        var code = Blockly.JavaScript.workspaceToCode(
            Blockly.getMainWorkspace()
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

    Blockly.inject('blockly-div', {
        toolbox: document.getElementById('toolbox'),
        toolboxPosition: 'end',
        horizontalLayout: true,
        scrollbars: false
    });


})();
