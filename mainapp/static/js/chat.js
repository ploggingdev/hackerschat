$(function() {
    $('#all_messages').scrollTop($('#all_messages')[0].scrollHeight);
    var to_focus = $("#message");
    var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    //temporarily hardcoded
    var chatsock = new ReconnectingWebSocket(ws_scheme + '://' + window.location.host + "/topics/general/chat/ws/");

    // Set the name of the hidden property
    var hidden; 
    if (typeof document.hidden !== "undefined") { // Opera 12.10 and Firefox 18 and later support 
    hidden = "hidden";
    } else if (typeof document.msHidden !== "undefined") {
    hidden = "msHidden";
    } else if (typeof document.webkitHidden !== "undefined") {
    hidden = "webkitHidden";
    }
    var original_page_title = $(document).attr("title");
    //remove chat message notice when user scrolls to bottom of div
    jQuery(function($) {
        $('#all_messages').on('scroll', function() {
            if($(this).scrollTop() + $(this).innerHeight() >= $(this)[0].scrollHeight - 10) {
                var new_message_notice = $("#new_message_element");
                if(new_message_notice.length != 0){
                    new_message_notice.remove();
                    $(document).attr("title", original_page_title);
                }
            }
        })
    });
    chatsock.onmessage = function(message) {

        if($("#no_messages").length){
            $("#no_messages").remove();
        }
        var data = JSON.parse(message.data);
        if(data.type == "error"){
            //display error message
            var fail_text = document.createElement('div');
            fail_text.innerText = data.payload.message;
            fail_text.setAttribute('class', 'alert alert-danger');
            fail_text.setAttribute('role', 'alert');
            $('#chat-form-container').prepend(fail_text);
            setTimeout(function () {
                fail_text.remove();
            }, 10000);
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
                user_list_ele_modal.append(li_user);
            }
            return;
        }
        if(data.message_type == "scrollback"){
            update_scrollback(data.messages, data.previous_id);
            return;
        }
        var chat = $("#chat");
        var scroll_top = true;
        var new_message_notice = $("#new_message_element");
        if (document[hidden]) {
            if(new_message_notice.length == 0){
                var new_message_element = $('<li id="new_message_element" class="list-group-item active">New messages : <span id="new_message_count">1</span></li>');
                chat.append(new_message_element);
                $('#all_messages').scrollTop($('#all_messages')[0].scrollHeight);
                $(document).attr("title", "(1) "+original_page_title);
            }
            else{
                var new_message_count_element = $('#new_message_count');
                var new_message_count = parseInt(new_message_count_element.html());
                if(isNaN(new_message_count)){
                    new_message_count = 0;
                }
                new_message_count += 1;
                new_message_count_element.html(new_message_count);
                $(document).attr("title", "("+new_message_count+") "+original_page_title);
            }
            scroll_top = false;
        }
        else{
            var chat_div = $("#all_messages");
            //update new message count if page is active but user has scrolled to view history
            if($(chat_div).scrollTop() + $(chat_div).innerHeight() < $(chat_div)[0].scrollHeight - 10){
                var new_message_count_element = $('#new_message_count');
                if(new_message_count_element.length==0){
                    var new_message_element = $('<li id="new_message_element" class="list-group-item active">New messages : <span id="new_message_count">1</span></li>');
                    chat.append(new_message_element);
                    $(document).attr("title", "(1) "+original_page_title);
                }
                else{
                    var new_message_count = parseInt(new_message_count_element.html());
                    if(isNaN(new_message_count)){
                        new_message_count = 0;
                    }
                    new_message_count += 1;
                    new_message_count_element.html(new_message_count);
                    $(document).attr("title", "("+new_message_count+") "+original_page_title);
                }
                scroll_top = false;
            }
        }
        var ele = $('<li class="list-group-item"></li>');
        ele.append('<strong><a href="'+data.user_profile_url+'">'+data.user+'</a></strong> : ');
        ele.append(data.message);
        chat.append(ele);
        if(scroll_top){
            $('#all_messages').scrollTop($('#all_messages')[0].scrollHeight);
        }
    };

    $("#chatform").on("submit", function(event) {
        var message = {
            message: $('#message').val()
        }
        chatsock.send(JSON.stringify(message));
        $("#message").val('').focus();
        return false;
    });

    function update_scrollback(new_messages, previous_id) {

        last_id = previous_id;
        
        if(last_id == -1){
            $("#load_old_messages").remove();
            $("#last_message_id").val(last_id)
            if(new_messages.length == 0){
                return;
            }
        }
        else{
            $("#last_message_id").val(last_id)
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

    }

    $("#load_old_messages").on("click", function(event) {
        var message = {
            last_message_id: $('#last_message_id').val()
        }
        chatsock.send(JSON.stringify(message));
        return false;
    });

    //hearbeat
    setInterval(function() {
        var message = {
            heartbeat : true
        }
        chatsock.send(JSON.stringify(message));
    }, 10000);
});