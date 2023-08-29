//トースター初期化
toastr.options = {
    "closeButton": true,
    "debug": false,
    "newestOnTop": true,
    "progressBar": true,
    "positionClass": "toast-top-center",
    "preventDuplicates": false,
    "onclick": null,
    "showDuration": "300",
    "hideDuration": "1000",
    "timeOut": "3000",
    "extendedTimeOut": "1000",
    "showEasing": "swing",
    "hideEasing": "linear",
    "showMethod": "fadeIn",
    "hideMethod": "fadeOut"
}


//Websockeet
let ws_conn;
var ws_connected = false;

function connect_ws() {
    //Websocketに接続
    //ws_conn = new WebSocket('ws://' + window.location.host + '/ws/connect');
    ws_conn = new WebSocket('wss://' + window.location.hostname + ':11113/ws/connect');

    ws_conn.onmessage = function(evt) {
        const parse_data = JSON.parse(evt.data);
        
        switch (parse_data.msgtype) {
            case "server_msg":
                let msg_data = parse_data.data;

                switch (msg_data.msgtype) {
                    case "success_update_distance":
                        toastr["info"]("距離設定を更新しました");

                        show_distance(msg_data.distance);
                        break;
                    case "now_distance":
                        show_distance(msg_data.distance);
                        break;
                    default:
                        console.log(msg_data);
                        break;
                }
                break;
        }
    };
        
    ws_conn.onclose = function(evt) {
        console.error('socket closed unexpectedly');
        ws_connected = false;

        toastr["warning"]("サーバーとの接続が切断しました、再接続するにはリロードしてください","通知",{disableTimeOut: true, closeButton:true,timeOut : "0",extendedTimeOut : "0"});
    };

    ws_conn.onopen = function(evt) {
        ws_connected = true;
        toastr["info"]("接続しました","通知");
        
        send_command("get_now_distance",{});
    }
}

connect_ws();

function change_distance(evt) {
    const num = evt.target.selectedIndex;
	const select_val = evt.target.options[num].value;

    send_command("update_distance",{"distance" : select_val});
}

function show_distance(distance) {
    distance_show_area.textContent = "現在は" + distance + "mで通知します"
}

function send_command(command,data) {
    if (ws_connected) {
        var packet = {
            "command":command,
            "data":data
        }
        
        var send_data = JSON.stringify(packet);

        ws_conn.send(send_data);
    }
}


let select_box = document.getElementById("notify_distances_select");
let distance_show_area = document.getElementById("distance_show");

select_box.addEventListener("change",change_distance);