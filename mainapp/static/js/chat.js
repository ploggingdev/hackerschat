$(function() {
    $('#all_messages').scrollTop($('#all_messages')[0].scrollHeight);
    var to_focus = $("#message");
    var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    //temporarily hardcoded
    var chatsock = new ReconnectingWebSocket(ws_scheme + '://' + window.location.host + "/topics/general/chat/ws/");

    chatsock.onmessage = function(message) {

        if($("#no_messages").length){
            $("#no_messages").remove();
        }
        var data = JSON.parse(message.data);
        if(data.type == "presence"){
            //lurkers count
            var lurkers = data.payload.lurkers;
            $('#lurkers-online').text(lurkers);
            if(lurkers == 1){
                $('#onlookers-online-indicator').text("onlooker");
            }
            else{
                $('#onlookers-online-indicator').text("onlookers");
            }

            //users count count
            var user_list = data.payload.members;
            $('#users-online').text(user_list.length);
            if(user_list.length == 1){
                $('#users-online-indicator').text("user");
            }
            else{
                $('#users-online-indicator').text("users");
            }

            //update user list
            var user_list_ele = $('#user_list');
            user_list_ele.text("");

            for(i=0; i<user_list.length; i++){
                var username_ele = document.createElement('p');
                username_ele.setAttribute('class','text-dark');
                username_ele.innerText = user_list[i];
                var li_user = document.createElement('li');
                li_user.append(username_ele);
                user_list_ele.append(li_user);
            }
            return;
        }
        var chat = $("#chat")
        var ele = $('<li class="list-group-item"></li>')
        
        ele.append(
            '<strong><a href="'+data.user_profile_url+'">'+data.user+'</a></strong> : ')
        
        ele.append(
            data.message)
        
        chat.append(ele)
        $('#all_messages').scrollTop($('#all_messages')[0].scrollHeight);
    };

    $("#chatform").on("submit", function(event) {
        var message = {
            message: $('#message').val()
        }
        chatsock.send(JSON.stringify(message));
        $("#message").val('').focus();
        return false;
    });

    //temporarily hardcoded
    var scrollbacksock = new ReconnectingWebSocket(ws_scheme + '://' + window.location.host + window.location.pathname+ "topics/general/chat/scrollback/");

    scrollbacksock.onmessage = function(message) {

        var data = JSON.parse(message.data);

        new_messages = data.messages

        last_id = data.previous_id
        
        if(last_id == -1){
            $("#load_old_messages").remove();
            $("#last_message_id").text(last_id)
            if(new_messages.length == 0){
                return;
            }
        }
        else{
            $("#last_message_id").text(last_id)
        }

        var chat = $("#chat")

        for(var i=new_messages.length - 1; i>=0; i--){
            var ele = $('<li class="list-group-item"></li>')
            
            ele.append(
                '<strong><a href="'+new_messages[i]['user_profile_url']+'">'+new_messages[i]['user']+'</a></strong> : '
                )
            
            ele.append(
                new_messages[i]['message'])
            
            chat.prepend(ele)
        }

    };

    $("#load_old_messages").on("click", function(event) {
        var message = {
            last_message_id: $('#last_message_id').val()
        }
        scrollbacksock.send(JSON.stringify(message));
        return false;
    });
    
    //hearbeat
    setInterval(function() {
        chatsock.send(JSON.stringify("heartbeat"));
    }, 5000);
});