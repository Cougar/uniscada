var ws = null;
var lines = [];

// Original JavaScript code by Chirp Internet: www.chirp.com.au
// Please acknowledge use of this code by including this header.
function getCookie(name) {
    var re = new RegExp(name + "=([^;]+)");
    var value = re.exec(document.cookie);
    return (value != null) ? unescape(value[1]) : null;
}

function ChangeButtonFocus() {
    var wsconnected = false;
    if (ws == null) {
        wsconnected = true;
    }
    document.getElementById("wsopen").disabled = ! wsconnected;
    document.getElementById("wsclose").disabled = wsconnected;
}

function get_ws_url(s) {
    var l = window.location;
    return ((l.protocol === "https:") ? "wss://" : "ws://") + l.hostname + (((l.port != 80) && (l.port != 443)) ? ":" + l.port : "") + s;
}

function WebSocketOpen() {
    if (! "WebSocket" in window) {
        alert("Websocket not supported");
        return;
    }
    ws = new WebSocket(get_ws_url("/api/v1/ws"));
    ws.onopen = wsOnOpen;
    ws.onmessage = wsOnMessage;
    ws.onclose = wsOnClose;
    ChangeButtonFocus();
}

function WebSocketClose() {
    if (ws == null) {
        return;
    }
    ws.close();
    ws = null;
    ChangeButtonFocus();
}

function wsOnOpen() {
    Display("----------------------------------------------\nWebsocket connected\n");
    ChangeButtonFocus();
}

function wsOnMessage(evt) {
    var received_msg = evt.data;
    Display(received_msg);
}

function wsOnClose() {
    Display("Connection is closed...\n")
    ws = null;
    ChangeButtonFocus();
}

function WebSocketSend(msg) {
    if (ws != null) {
        ws.send(msg);
    }
}

function WebSocketSend(method, res) {
    if (ws != null) {
        var msg = {}
        msg.method = method;
        msg.resource = res;
        token = document.getElementById('token').value;
        if (token != '') {
            msg.token = token;
        }
        var json = JSON.stringify(msg);
        Display('Send: ' + json);
        ws.send(json)
    }
}


function WebSocketSubscribe(res) {
    WebSocketSend('subscribe', res);
}

function WebSocketGet(res) {
    WebSocketSend('get', res);
}

function WebSocketSubscribe(res) {
    WebSocketSend('subscribe', res);
}

function Display(msg) {
        lines = lines.concat(msg.match(/[^\r\n]+/g))
        lines = lines.slice(-40);
        document.getElementById("messages").innerHTML = lines.join('\n');
}

function ClearDisplay() {
    lines = [];
    Display('');
}
