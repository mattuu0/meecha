//マップ設定
const main_map = L.map('show_map')

var tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="http://osm.org/copyright">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>',
});

tileLayer.addTo(main_map);

//各ユーザーのピン
var user_pins = {};
var myself_marker = null;

//Websockeet
let ws_conn;
var ws_connected = false;

function connect_ws() {
    //Websocketに接続
    ws_conn = new WebSocket('ws://' + window.location.host + '/ws/connect');
   

    ws_conn.onmessage = function(evt) {
        const parse_data = JSON.parse(evt.data);
        
        switch (parse_data.msgtype) {
            case "server_msg":
                let msg_data = parse_data.data;

                console.log(msg_data.msgtype);
                switch (msg_data.msgtype) {
                    case "search_response":
                        show_search_result(msg_data.match_users);
                        break;
                    case "recv_friend_request":
                        show_recving_request(msg_data.request_data);
                        break;
                    case "recved_friend_request":
                        show_recved_requests(msg_data.recved_requests);
                        break;
                    case "sended_friend_request":
                        show_sended_friend_requests(msg_data.sended_requests);
                        break;
                    case "friends_response":
                        show_friend(msg_data.friends);
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

        console.log('Socket is closed. 3秒後に再接続します。', event.reason);
        setTimeout(() => {
            connect_ws();
        }, 3000);
    };

    ws_conn.onopen = function(evt) {
        ws_connected = true;
        console.log("接続しました")
    }
}

connect_ws();

//検索ボタン
const search_button = document.getElementById("user_search_button");

//検索するユーザー名
const search_value = document.getElementById("search_username_value");

//ユーザー検索結果
const search_result_area = document.getElementById("user_searh_result");

//受信済みリクエスト表示場所
const recved_request_show_area = document.getElementById("recved_request_show_area");

//受信済みリクエスト取得ボタン
const get_recved_request_button = document.getElementById("get_request_button");

//送信済みリクエスト取得ボタン
const get_sended_request_button = document.getElementById("sended_request_button");

//送信済みリクエスト表示場所
const sended_request_show_area = document.getElementById("sended_request_show_area");

//フレンド取得ボタン
const get_friends_btn = document.getElementById("get_friends_button");

//フレンド表示場所
const friend_show_area = document.getElementById("friends_show_area");

function init(evt) {
    //オブジェクト取得
    
    //イベント関連
    function search_user(evt){
        send_command("search_user",{username : search_value.value});
    }

    //イベント登録
    search_button.addEventListener("click",search_user);
    get_recved_request_button.addEventListener("click",get_friend_request);
    get_sended_request_button.addEventListener("click",get_sended_friend_request);
    get_friends_btn.addEventListener("click",get_friends);
}

window.onload = init;

//ユーザー検索関連
function clear_child_elems(elem) {
    //結果を削除する
    while (elem.lastChild) {
        elem.removeChild(elem.lastChild);
    }
}

//受信したフレンドリクエストを表示する
function show_recving_request(result) {
    show_friend_request(result.sender_id,result.username,result.requestid,recved_request_show_area);

}

//受信済みフレンドリクエストを表示する
function show_recved_requests(result) {
    clear_child_elems(recved_request_show_area);

    for (let requestid in result) {
        //送信者ID
        let senderid = result[requestid].sender_userid;  
        
        //送信者名
        let sender_name = result[requestid].user_name;

        show_friend_request(senderid,sender_name,requestid,recved_request_show_area)
    }
}
 
//フレンドリクエストを表示する
function show_friend_request(senderid,username,requestid,showdiv) {
    //結果のdiv
    let add_div = document.createElement("div");

    //ID表示
    let sender_userid_area = document.createElement("p");
    sender_userid_area.textContent = "ID : " + senderid;

    //追加
    add_div.appendChild(sender_userid_area);

    //ID表示
    let username_area = document.createElement("p");
    username_area.textContent = "ユーザー名 : " + username;

    //追加
    add_div.appendChild(username_area);

    //承認ボタン
    let accept_btn = document.createElement("input");
    accept_btn.type = "button";
    accept_btn.value = "承認";
    accept_btn.requestid = requestid;

    //イベント登録
    accept_btn.addEventListener("click",accept_friend_request);
    add_div.append(accept_btn);

    //フレンドリクエストボタン
    let reject_btn = document.createElement("input");
    reject_btn.type = "button";
    reject_btn.value = "拒否";
    reject_btn.requestid = requestid;

    //イベント登録
    reject_btn.addEventListener("click",reject_friend_request);
    add_div.append(reject_btn);


    showdiv.appendChild(add_div);
}

//取得した受信済みフレンドリクエストを表示する
function show_friend_requests(result) {
    clear_child_elems(recved_request_show_area);

    for (let requestid in result) {
        show_friend_request(result[requestid].sender_id,result[requestid].user_name,requestid,recved_request_show_area);
    }
}

//取得した送信済みフレンドリクエストを表示する
function show_sended_friend_requests(result) {
    clear_child_elems(sended_request_show_area);

    for (let requestid in result) {
        let senderid = result[requestid].sender_id;
        let username = result[requestid].user_name;

        //結果のdiv
        let add_div = document.createElement("div");

        //ID表示
        let sender_userid_area = document.createElement("p");
        sender_userid_area.textContent = "ID : " + senderid;

        //追加
        add_div.appendChild(sender_userid_area);

        //ID表示
        let username_area = document.createElement("p");
        username_area.textContent = "ユーザー名 : " + username;

        //追加
        add_div.appendChild(username_area);

        //承認ボタン
        let cancel_btn = document.createElement("input");
        cancel_btn.type = "button";
        cancel_btn.value = "取り消し";
        cancel_btn.requestid = requestid;

        //イベント登録
        cancel_btn.addEventListener("click",cancel_friend_request);
        add_div.append(cancel_btn);

        sended_request_show_area.appendChild(add_div);
    }
}

//フレンドを表示する
function show_friend(result) {
    clear_child_elems(friend_show_area);

    result.forEach((val,index) => {
        //結果のdiv
        let add_div = document.createElement("div");

        //ID表示
        let sender_userid_area = document.createElement("p");
        sender_userid_area.textContent = "ID : " + val["friend_userid"];

        //追加
        add_div.appendChild(sender_userid_area);

        //ID表示
        let username_area = document.createElement("p");
        username_area.textContent = "ユーザー名 : " + val["friend_username"];

        //追加
        add_div.appendChild(username_area);


        //削除ボタン
        let remove_btn = document.createElement("input");
        remove_btn.type = "button";
        remove_btn.value = "フレンド削除";
        remove_btn.friendid = val["friendid"];

        //イベント登録
        remove_btn.addEventListener("click",remove_friend);
        add_div.append(remove_btn);


        //メモ編集エリア
        let friend_memo_area = document.createElement("div");
        friend_memo_area.classList.add("friend_memo");

        //フレンドリクエストボタン
        let memo_area = document.createElement("textarea");
        memo_area.friendid = val["friendid"];
        memo_area.friend_userid = val["friend_userid"];
        memo_area.value = val["friend_memo"];
        friend_memo_area.append(memo_area);

        //フレンドリクエストボタン
        let memo_btn = document.createElement("input");
        memo_btn.type = "button";
        memo_btn.value = "メモ更新";
        memo_btn.friendid = val["friendid"];
        memo_btn.friend_userid = val["friend_userid"];
        memo_btn.memo_text_area = memo_area;

        //イベント登録
        memo_btn.addEventListener("click",update_memo);
        friend_memo_area.append(memo_btn);

        add_div.appendChild(friend_memo_area);


        friend_show_area.appendChild(add_div);
    })
}

//サーバーにコマンドを送信する
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

//フレンドリクエストを承認
function accept_friend_request(evt) {
    //ユーザーID
    let send_id = evt.target.requestid;

    send_command("accept_request",{requestid:send_id});
}

//フレンドを削除
function remove_friend(evt) {
    //ユーザーID
    let send_id = evt.target.friendid;

    send_command("remove_friend",{friendid:send_id});
}


//メモ更新
function update_memo(evt) {
    //ユーザーID
    let send_id = evt.target.friend_userid;
    let memo_value = evt.target.memo_text_area;

    send_command("update_memo",{friendid:send_id,uodate_memo : memo_value.value});
}


//フレンドリクエストを拒否
function reject_friend_request(evt) {
    //ユーザーID
    let send_id = evt.target.requestid;

    send_command("reject_request",{requestid:send_id});
}

//フレンドリクエストをキャンセル
function cancel_friend_request(evt) {
    //ユーザーID
    let send_id = evt.target.requestid;

    send_command("cancel_request",{requestid:send_id});
}

//検索結果表示
function show_search_result(result) {
    clear_child_elems(search_result_area);

    for (let userid in result) {
        //結果のdiv
        let add_div = document.createElement("div");

        //ID表示
        let userid_area = document.createElement("p");
        userid_area.textContent = "ID : " + userid;

        //追加
        add_div.appendChild(userid_area);

        //ID表示
        let username_area = document.createElement("p");
        username_area.textContent = "ユーザー名 : " + result[userid].user_name;

        //追加
        add_div.appendChild(username_area);
        
        let request_btn = document.createElement("input");
        request_btn.type = "button";
        
        request_btn.userid = userid;
        request_btn.value = "フレンドリクエスト";

        //イベント登録
        if (result[userid].is_friend == "0") {
            //フレンドリクエストボタン
            request_btn.addEventListener("click",send_firend_req);
        } else {
            //フレンドならボタンを無効にする
            request_btn.disabled = true;
        }

        add_div.append(request_btn);
        search_result_area.appendChild(add_div);
    }
}

//フレンドリクエストを送る
function send_firend_req(evt) {
    //ユーザーID
    let send_id = evt.target.userid;

    send_command("friend_request",{userid:send_id});
}

//受信済みフレンドリクエストを取得する
function get_friend_request(evt) {
    send_command("get_recved_request",{});
}

//送信済みフレンドリクエストを取得する
function get_sended_friend_request(evt) {
    send_command("get_sended_request",{});
}

//フレンド一覧を取得する
function get_friends(evt) {
    send_command("get_friends",{});
}

//位置情報取得
var id, target, options;

function success(pos) {
    var crd = pos.coords;

    //マーカーが設定されていなかったら現在地に打つ
    if (myself_marker == null) {
        main_map.setView([crd.latitude,crd.longitude],15);

        var popup = L.popup();
        myself_marker = L.marker([crd.latitude,crd.longitude]).addTo(main_map).on('click', function (e) {
                popup
                .setLatLng(e.latlng)
                .setContent("あなたの現在地")
                .openOn(main_map);
        });
    } else {
        //マーカーがあったら移動する
        myself_marker.setLatLng([crd.latitude,crd.longitude])
    }

    send_command("post_location",{
        latitude : crd.latitude,
        longitude : crd.longitude
    });
}

function error(err) {
    console.warn('ERROR(' + err.code + '): ' + err.message);
}

function clear_watch() {
    navigator.geolocation.clearWatch(id);
}

options = { 
    enableHighAccuracy: true,
    timeout: 5000,
    maximumAge: 5000
};

function start_gps() {
    id = navigator.geolocation.watchPosition(success, error, options);
}

start_gps();