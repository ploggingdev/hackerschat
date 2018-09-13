$(function() {
    var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    var window_pathname = window.location.pathname;
    if(window_pathname.slice(-1) != "/"){
        window_pathname = window_pathname + "/";
    }
    var n = window_pathname.indexOf('forum');
    window_pathname = window_pathname.substring(0, n != -1 ? n : window_pathname.length);
    //temporarily hardcoded
    var chatsock = new ReconnectingWebSocket(ws_scheme + '://' + window.location.host + window_pathname + "chat/ws/");

    chatsock.onmessage = function(message) {
        var data = JSON.parse(message.data);
        if(data.type == "error"){
            return;
        }
        if(data.message_type == "presence"){
            //lurkers count
            var lurkers = data.payload.lurkers;
            $('#lurkers-online').text(lurkers);
            $('#lurkers-online-modal').text(lurkers);
            if(lurkers == 1){
                $('#onlookers-online-indicator').text("onlooker");
                $('#onlookers-online-indicator-modal').text("onlooker");
            }
            else{
                $('#onlookers-online-indicator').text("onlookers");
                $('#onlookers-online-indicator-modal').text("onlookers");
            }

            //users count count
            var user_list = data.payload.members;
            user_list.sort();
            $('#users-online').text(user_list.length);
            $('#users-online-modal').text(user_list.length);
            if(user_list.length == 1){
                $('#users-online-indicator').text("user");
                $('#users-online-indicator-modal').text("user");
            }
            else{
                $('#users-online-indicator').text("users");
                $('#users-online-indicator-modal').text("users");
            }

            //update user list
            var user_list_ele = $('#user_list');
            user_list_ele.text("");
            var user_list_ele_modal = $('#user_list-modal');
            user_list_ele_modal.text("");

            for(i=0; i<user_list.length; i++){
                var username_ele = document.createElement('p');
                username_ele.setAttribute('class','text-dark');
                username_ele.innerText = user_list[i];
                var li_user = document.createElement('li');
                li_user.append(username_ele);
                user_list_ele.append(li_user);
                user_list_ele_modal.append(li_user.cloneNode(true));
            }
            return;
        }
    };

    //hearbeat
    setInterval(function() {
        var message = {
            heartbeat : true
        }
        chatsock.send(JSON.stringify(message));
    }, 10000);
});