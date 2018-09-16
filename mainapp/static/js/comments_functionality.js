var base_url = 'https://www.hackerschat.net/';
//var base_url = 'http://127.0.0.1:8000/';
$(document).ready(function() {
    $(document).on("submit", ".commentform", function (e) {
        e.preventDefault();
        var val = $("input[type=submit][clicked=true]").parent();
        add_comment(val);
    });

    $(".commentform input[type=submit]").click(function () {
        $("input[type=submit]", $(this).parents(".commentform")).removeAttr("clicked");
        $(this).attr("clicked", "true");
    });

    $(document).on("submit", ".editform", function (e) {
        e.preventDefault();
        var val = $("input[type=submit][clicked=true]").parent().parent().parent();
        edit_comment(val);
    });

    $(".editform input[type=submit]").click(function () {
        $("input[type=submit]", $(this).parents(".editform")).removeAttr("clicked");
        $(this).attr("clicked", "true");
    });

});

function delete_button_clicked(id){
    var prompt = $('#' + id + '_delete_button_confirm');
    if(prompt.attr('style') == undefined){
        return false;
    }
    prompt.removeAttr('style');
    return false;
}

function cancel_delete_comment(id){
    var prompt = $('#' + id + '_delete_button_confirm');
    prompt.attr('style', 'display:None');
    return false;
}

function confirm_delete_comment(event, id){

    event.preventDefault();
    var comment = $('#' + id + "-media");
    var csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    var delete_comment_endpoint = base_url + 'forum/deletecomment/' + get_post_id() + '/';
    $.ajax({

        // The URL for the request
        url: delete_comment_endpoint,

        // The data to send (will be converted to a query string)
        data: {
            comment_id: id
        },

        // Whether this is a POST or GET request
        type: "POST",

        // The type of data we expect back
        dataType: "json",
    })
        // Code to run if the request succeeds (is done);
        // The response is passed to the function
        .done(function (json) {
            var success_text = document.createElement('p');
            success_text.innerText = json.success;
            success_text.setAttribute('class', 'text-success');

            comment.parent().prepend(success_text);
            setTimeout(function () {
                success_text.remove();
            }, 10000);
            //show deleted text
            $('#'+id+"-username").remove();
            $('#'+id+"-points").remove();
            $('#'+id+"-points-suffix").remove();
            var deleted_msg = document.createTextNode("[deleted]");
            $('#'+id+"-em").prepend(deleted_msg);
            $('#'+id+"-on-delete").html("[deleted]<br><br>");
            
            comments_count_object = $('#total_comments_count');
            var comments_count = parseInt(comments_count_object.text());
            if(comments_count == 2){
                var new_comments_text = document.createElement('span');
                new_comments_text.setAttribute('id', 'total_comments_count');
                new_comments_text.innerText='1';
                var comments_count_suffix = document.createTextNode(' comment');
            }
            else{
                var new_comments_text = document.createElement('span');
                new_comments_text.setAttribute('id', 'total_comments_count');
                new_comments_text.innerText=comments_count-1;
                var comments_count_suffix = document.createTextNode(' comments');
            }
            var total_comments_container = $('#total_comments_container');
            total_comments_container.text("");
            total_comments_container.append(new_comments_text);
            total_comments_container.append(comments_count_suffix);
            return false;
        })
        // Code to run if the request fails; the raw request and
        // status codes are passed to the function
        .fail(function (data) {
            var fail_text = document.createElement('p');
            fail_text.innerText = data.responseJSON.error;
            fail_text.setAttribute('class', 'text-danger');
            $("#"+id+"-on-delete").append(fail_text);
            setTimeout(function () {
                fail_text.remove();
            }, 10000);
            return false;
        });
}

function edit_button_clicked(id){
    cancel_reply(id);
    var comment_html = $('#'+id+'_comment_html');
    comment_html.attr('style', 'display:None;');
    var edit_comment_form = $('#'+id+'_edit_form');
    edit_comment_form.removeAttr('style');
    return false;
}

function cancel_edit(id){
    var comment_html = $('#'+id+'_comment_html');
    comment_html.removeAttr('style');
    var edit_comment_form = $('#'+id+'_edit_form');
    edit_comment_form.attr('style', 'display:None;');
    return false;
}

function edit_comment(frm) {

    var csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    var edit_comment_endpoint = base_url + 'forum/editcomment/' + get_post_id() + '/';
    $.ajax({

        // The URL for the request
        url: edit_comment_endpoint,

        // The data to send (will be converted to a query string)
        data: frm.serialize(),

        // Whether this is a POST or GET request
        type: "POST",

        // The type of data we expect back
        dataType: "json",
    })
        // Code to run if the request succeeds (is done);
        // The response is passed to the function
        .done(function (json) {
            frm.children('p').children('textarea').val("");
            var success_text = document.createElement('p');
            success_text.innerText = json.success;
            success_text.setAttribute('class', 'text-success');

            var comment_html = $('#' + json.comment_id + '_comment_html');
            comment_html.removeAttr('style');
            comment_html.html(json.comment_html);
            var edit_comment_textarea = $('#' + json.comment_id + '_edit_comment_textarea');
            edit_comment_textarea.val(json.comment_raw);
            $('#' + json.comment_id + '_edit_form').attr('style', 'display:None;');
            $('#' + json.comment_id + '-on-delete').prepend(success_text);
            setTimeout(function () {
                success_text.remove();
            }, 10000);
        })
        // Code to run if the request fails; the raw request and
        // status codes are passed to the function
        .fail(function (data) {
            var fail_text = document.createElement('p');
            fail_text.innerText = data.responseJSON.error;
            fail_text.setAttribute('class', 'text-danger');
            frm.prepend(fail_text);
            setTimeout(function () {
                fail_text.remove();
            }, 10000);
        });
}

function cancel_reply(id){
    var current_frm = document.getElementById(id+"-reply-form");
    if(current_frm == null){
        return false;
    }
    current_frm.remove();
}

function generate_reply_button(id){
    cancel_edit(id);
    var current_frm = document.getElementById(id+"-reply-form");
    if(current_frm != null){
        return false;
    }
    var frm = generate_reply_form(id);
    var selector = id+"-comment-children";
    var to_prepend = $("#"+selector);
    if(to_prepend.length){
        to_prepend.prepend(frm);
    }
    else{
        var comment_body_selector = id+"-media-body";
        var comment_body = $("#"+comment_body_selector);
        var new_comment_list = document.createElement('ul');
        new_comment_list.setAttribute("id", id+"-comment-children");
        new_comment_list.setAttribute("class", "media-list children");
        new_comment_list.append(frm);
        comment_body.append(new_comment_list);
    }
    $("#"+id+"-reply-form").submit(function (event) {
        event.preventDefault();
        var val = $("#"+id+"-reply-form");
        add_comment(val);
    });
    return false;
}

function generate_reply_form(id){
    //label
    var label = document.createElement('label');
    label.setAttribute('for', 'id_comment');
    label.append("Reply using the below form");

    //textarea
    var txtarea = document.createElement("textarea");
    txtarea.setAttribute('name', 'comment');
    txtarea.setAttribute('maxlength', '2000');
    txtarea.setAttribute("required", '');
    txtarea.setAttribute('id', 'id_comment');
    txtarea.setAttribute('class', 'form-control');
    txtarea.setAttribute('cols', '40');
    txtarea.setAttribute('rows', '5');
    txtarea.setAttribute('style', 'white-space:pre-wrap;');
    txtarea.addEventListener( 'keydown', function ( e ) {
        if ( e.which != 9 ) return;

        var start           = this.selectionStart;
        var end             = this.selectionEnd;

        this.value          = this.value.substr( 0, start ) + "\t" + this.value.substr( end );
        this.selectionStart = this.selectionEnd = start + 1;

        e.preventDefault();
        return false;
    });

    //hidden parent id input
    var parent_id_ip = document.createElement('input');
    parent_id_ip.setAttribute('type', 'hidden');
    parent_id_ip.setAttribute('name', 'parent_id');
    parent_id_ip.setAttribute('value', id+"");
    parent_id_ip.setAttribute('id', 'id_parent_id');
    parent_id_ip.setAttribute('class', 'parent_id');

    var p_container = document.createElement('p');
    p_container.append(label);
    p_container.append(txtarea);
    p_container.append(parent_id_ip);

    //submit button
    var submit_btn = document.createElement('input');
    submit_btn.setAttribute('type', 'submit');
    submit_btn.setAttribute('class', 'btn btn-primary');
    submit_btn.setAttribute('value', 'Submit');
    submit_btn.setAttribute('id', 'id_submit');
    var submit_btn_container = document.createElement('li');
    submit_btn_container.setAttribute('class', 'list-inline-item');
    submit_btn_container.append(submit_btn);

    //cancel button
    var cancel_btn = document.createElement('input');
    cancel_btn.setAttribute('type', 'button');
    cancel_btn.setAttribute('class', 'btn btn-default');
    cancel_btn.setAttribute('value', 'Cancel');
    cancel_btn.setAttribute('id', 'id_cancel');
    cancel_btn.setAttribute('onclick', 'return cancel_reply('+id+')');
    var cancel_btn_container = document.createElement('li');
    cancel_btn_container.setAttribute('class', 'list-inline-item');
    cancel_btn_container.append(cancel_btn);

    //btn container
    var btn_container = document.createElement('ul');
    btn_container.setAttribute('class', 'list-inline');
    btn_container.append(submit_btn_container);
    btn_container.append(cancel_btn_container);
    btn_container.append(document.createElement('br'));
    btn_container.append(document.createElement('br'));

    //main form
    var frm = document.createElement('form');
    frm.setAttribute('action', '');
    frm.setAttribute('method', 'post');
    frm.setAttribute('id', id+"-reply-form")
    frm.setAttribute('data-parent-id', id)

    frm.append(p_container);
    frm.append(btn_container);
    return frm;
}

function generate_edit_form(id, comment_raw){
    //label
    var label = document.createElement('label');
    label.setAttribute('for', id+'_edit_comment_textarea');
    label.append("Edit comment");

    //textarea
    var txtarea = document.createElement("textarea");
    txtarea.setAttribute('name', 'comment');
    txtarea.setAttribute('maxlength', '2000');
    txtarea.setAttribute("required", '');
    txtarea.setAttribute('id', id+'_edit_comment_textarea');
    txtarea.setAttribute('class', 'form-control');
    txtarea.setAttribute('cols', '40');
    txtarea.setAttribute('rows', '5');
    txtarea.setAttribute('style', 'white-space:pre-wrap;');
    txtarea.value = comment_raw;

    txtarea.addEventListener( 'keydown', function ( e ) {
        if ( e.which != 9 ) return;

        var start           = this.selectionStart;
        var end             = this.selectionEnd;

        this.value          = this.value.substr( 0, start ) + "\t" + this.value.substr( end );
        this.selectionStart = this.selectionEnd = start + 1;

        e.preventDefault();
        return false;
    });

    //hidden input id
    var parent_id_ip = document.createElement('input');
    parent_id_ip.setAttribute('type', 'hidden');
    parent_id_ip.setAttribute('name', 'comment_id');
    parent_id_ip.setAttribute('value', id+"");
    parent_id_ip.setAttribute('id', id+'_comment_id');
    parent_id_ip.setAttribute('class', 'parent_id');

    var p_container = document.createElement('p');
    p_container.append(label);
    p_container.append(txtarea);
    p_container.append(parent_id_ip);

    //submit button
    var submit_btn = document.createElement('input');
    submit_btn.setAttribute('type', 'submit');
    submit_btn.setAttribute('class', 'btn btn-primary');
    submit_btn.setAttribute('value', 'Update');
    var submit_btn_container = document.createElement('li');
    submit_btn_container.setAttribute('class', 'list-inline-item');
    submit_btn_container.append(submit_btn);

    //cancel button
    var cancel_btn = document.createElement('input');
    cancel_btn.setAttribute('type', 'button');
    cancel_btn.setAttribute('class', 'btn btn-default');
    cancel_btn.setAttribute('value', 'Cancel');
    cancel_btn.setAttribute('onclick', 'return cancel_edit('+id+')');
    var cancel_btn_container = document.createElement('li');
    cancel_btn_container.setAttribute('class', 'list-inline-item');
    cancel_btn_container.append(cancel_btn);

    //btn container
    var btn_container = document.createElement('ul');
    btn_container.setAttribute('class', 'list-inline');
    btn_container.append(submit_btn_container);
    btn_container.append(cancel_btn_container);


    //main form
    var frm = document.createElement('form');
    frm.setAttribute('action', '');
    frm.setAttribute('method', 'post');
    frm.setAttribute('id', id+"_edit_form")
    frm.setAttribute('style', 'display:None;');

    frm.append(p_container);
    frm.append(btn_container);

    $(document).on("submit","#"+id+"_edit_form" ,function (e) {
        e.preventDefault();
        var val = $("#"+id+"_edit_form");
        edit_comment(val);
    });

    return frm;
}

function add_comment(frm) {

        var csrftoken = getCookie('csrftoken');
    
        $.ajaxSetup({
            beforeSend: function (xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });

        var add_comment_url = base_url + 'forum/addcomment/' + get_post_id() + '/';
        $.ajax({
    
            // The URL for the request
            url: add_comment_url,
    
            // The data to send (will be converted to a query string)
            data: frm.serialize(),
    
            // Whether this is a POST or GET request
            type: "POST",
    
            // The type of data we expect back
            dataType: "json",
        })
            // Code to run if the request succeeds (is done);
            // The response is passed to the function
            .done(function (json) {
                frm.children('p').children('textarea').val("");
                var success_text = document.createElement('p');
                success_text.innerText = json.success;
                success_text.setAttribute('class', 'text-success');
                
                var latest_comment = generate_comment(json.comment_id, json.comment_html, json.username, json.comment_raw);

                if(frm.data('parent-id') == "None"){
                    $('#root_comments').prepend(latest_comment);
                    frm.prepend(success_text);
                    setTimeout(function() {
                        success_text.remove();
                      }, 10000);
                }
                else{
                    $('#' + frm.data('parent-id') + '-comment-children').prepend(latest_comment);
                    $('#' + frm.data('parent-id') + '-comment-children').prepend(success_text);
                    setTimeout(function() {
                        success_text.remove();
                      }, 10000);
                    frm.remove();
                }

                comments_count_object = $('#total_comments_count');
                var comments_count = parseInt(comments_count_object.text());
                if(comments_count == 0){
                    var new_comments_text = document.createElement('span');
                    new_comments_text.setAttribute('id', 'total_comments_count');
                    new_comments_text.innerText='1';
                    var comments_count_suffix = document.createTextNode(' comment');
                }
                else{
                    var new_comments_text = document.createElement('span');
                    new_comments_text.setAttribute('id', 'total_comments_count');
                    new_comments_text.innerText=comments_count+1;
                    var comments_count_suffix = document.createTextNode(' comments');
                }
                var total_comments_container = $('#total_comments_container');
                total_comments_container.text("");
                total_comments_container.append(new_comments_text);
                total_comments_container.append(comments_count_suffix);
            })
            // Code to run if the request fails; the raw request and
            // status codes are passed to the function
            .fail(function (data) {
                var fail_text = document.createElement('p');
                fail_text.innerText = data.responseJSON.error;
                fail_text.setAttribute('class', 'text-danger');
                frm.prepend(fail_text);
                setTimeout(function() {
                    fail_text.remove();
                  }, 10000);
            });
    }

function generate_comment(comment_id, comment_html, username, comment_raw){

    //create upvote button
    var upvote_btn = document.createElement('i');
    upvote_btn.setAttribute('id', comment_id+'-up');
    upvote_btn.setAttribute('class', 'fas fa-angle-up fa-lg');
    upvote_btn.setAttribute('style', 'color : orangered');
    upvote_btn.setAttribute('aria-hidden', 'true');
    upvote_btn.setAttribute('onclick', "handle_vote("+comment_id+",'up')");

    var upvote_container = document.createElement('div');
    upvote_container.appendChild(upvote_btn);
    
    //downvote button
    var downvote_btn = document.createElement('span');
    downvote_btn.setAttribute('id', comment_id+'-down');
    downvote_btn.setAttribute('class', 'fas fa-angle-down fa-lg');
    downvote_btn.setAttribute('aria-hidden', 'true');
    downvote_btn.setAttribute('onclick', "handle_vote("+comment_id+",'down')");

    var downvote_container = document.createElement('div');
    downvote_container.appendChild(downvote_btn);

    //container for vote buttons
    var media_left_container = document.createElement('div');
    media_left_container.setAttribute('class', 'media-left');
    media_left_container.setAttribute('style', 'color : grey')
    media_left_container.appendChild(upvote_container);
    media_left_container.appendChild(downvote_container);

    //profile link
    var profile_link = document.createElement('a');
    profile_link.setAttribute('href', '/profile/'+username);
    profile_link.setAttribute('id', comment_id+'-username');
    profile_link.innerText = username+" ";

    //points count
    points_count = document.createElement('span');
    points_count.setAttribute('id', comment_id+'-points');
    points_count.innerText = "1";

    //points suffix
    var points_suffix = document.createElement('span');
    points_suffix.setAttribute('id', comment_id+'-points-suffix');
    points_suffix.innerText = "point";
    var time_since_posted = document.createTextNode(' posted 0 minutes ago');
    var sp = document.createTextNode(" ");

    //em container
    var em_container = document.createElement('em');
    em_container.setAttribute('id', comment_id+'-em');
    em_container.appendChild(profile_link);
    em_container.appendChild(points_count);
    em_container.appendChild(sp);
    em_container.append(points_suffix);
    em_container.appendChild(time_since_posted);

    //comment content
    var comment_content = document.createElement('div');
    comment_content.setAttribute('id', comment_id+"_comment_html");
    comment_content.innerHTML = comment_html;

    //edit form
    var edit_form = generate_edit_form(comment_id, comment_raw);

    //reply button
    var reply_button = document.createElement('a');
    reply_button.setAttribute('href', '#');
    reply_button.innerText = 'reply';
    reply_button.setAttribute('onclick', "return generate_reply_button(" + comment_id + ")");
    var reply_button_li = document.createElement('li');
    reply_button_li.appendChild(reply_button);

    //edit button
    var edit_button = document.createElement('a');
    edit_button.setAttribute('href', '#');
    edit_button.innerText = 'edit';
    edit_button.setAttribute('onclick', "return edit_button_clicked(" + comment_id + ")");
    var edit_button_li = document.createElement('li');
    edit_button_li.appendChild(edit_button);

    //delete button
    var delete_button = document.createElement('a');
    delete_button.setAttribute('href', '#');
    delete_button.setAttribute('onclick', 'return delete_button_clicked('+ comment_id + ');');
    delete_button.innerText = 'delete';
    var delete_button_li = document.createElement('li');
    delete_button_li.setAttribute('id', comment_id+'_delete_button');
    delete_button_li.appendChild(delete_button);

    //delete button confirm
    var sure_txt = document.createTextNode('sure? ');
    //yes btn
    var yes_btn = document.createElement('a');
    yes_btn.setAttribute('href', '#');
    yes_btn.setAttribute('onclick', 'return confirm_delete_comment(event,'+ comment_id + ');');
    yes_btn.innerText = 'yes';
    // slash
    var slash_txt = document.createTextNode(' / ');
    //no btn
    var no_btn = document.createElement('a');
    no_btn.setAttribute('href', '#');
    no_btn.setAttribute('onclick', 'return cancel_delete_comment('+ comment_id + ');');
    no_btn.innerText = 'no';
    //li
    var delete_button_confirm_li = document.createElement('li');
    delete_button_confirm_li.setAttribute('id', comment_id+'_delete_button_confirm');
    delete_button_confirm_li.setAttribute('style', 'display:None;');
    delete_button_confirm_li.append(sure_txt);
    delete_button_confirm_li.append(yes_btn);
    delete_button_confirm_li.append(slash_txt);
    delete_button_confirm_li.append(no_btn);

    //ul buttons
    var ul_buttons = document.createElement('ul');
    ul_buttons.setAttribute('class', 'list-inline');
    reply_button_li.setAttribute('class', 'list-inline-item');
    ul_buttons.appendChild(reply_button_li);
    edit_button_li.setAttribute('class', 'list-inline-item');
    ul_buttons.appendChild(edit_button_li);
    delete_button_li.setAttribute('class', 'list-inline-item');
    ul_buttons.appendChild(delete_button_li);
    delete_button_confirm_li.setAttribute('class', 'list-inline-item');
    ul_buttons.appendChild(delete_button_confirm_li);

    //ul buttons container
    var ul_buttons_container = document.createElement('div');
    ul_buttons_container.append(ul_buttons);
    var div_br = document.createElement('br');
    ul_buttons_container.append(div_br);

    //on-delete container
    var on_delete_container = document.createElement('div');
    on_delete_container.setAttribute('id', comment_id+'-on-delete');
    on_delete_container.append(comment_content);
    on_delete_container.append(edit_form);
    on_delete_container.append(ul_buttons_container);

    //media body
    var media_body_container = document.createElement('div');
    media_body_container.setAttribute('class', 'media-body');
    media_body_container.setAttribute('id', comment_id+"-media-body")

    media_body_container.appendChild(em_container);
    media_body_container.appendChild(document.createElement('br'));
    media_body_container.appendChild(document.createElement('br'));
    media_body_container.appendChild(on_delete_container);

    var comment_container = document.createElement('li');
    comment_container.setAttribute('class', 'media');
    comment_container.setAttribute('id', comment_id+"-media");
    comment_container.appendChild(media_left_container);
    //2 spaces for formatting
    comment_container.appendChild( document.createTextNode( '\u00A0' ) );
    comment_container.appendChild( document.createTextNode( '\u00A0' ) );
    comment_container.appendChild(media_body_container);

    return comment_container;
}

function handle_vote(id, type) {

    if ((type != 'up' && type != 'down') || !Number.isInteger(id)) {
        alert("Oops, an error was encountered.");
        return;
    }

    var csrftoken = getCookie('csrftoken');
    var comment = $('#' + id + "-media");

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    if (type == "up") {
        vote_value = 1;
    }
    else if (type == "down") {
        vote_value = -1;
    }
    upvote_selector = "#" + id + "-up"
    upvote_item = $(upvote_selector);
    downvote_selector = "#" + id + "-down"
    downvote_item = $(downvote_selector);
    points_selector = "#" + id + "-points"
    points_item = $(points_selector);

    $.ajax({

        // The URL for the request
        url: "/forum/votecomment/" + id + "/",

        // The data to send (will be converted to a query string)
        data: {
            vote_value: vote_value
        },

        // Whether this is a POST or GET request
        type: "POST",

        // The type of data we expect back
        dataType: "json",
    })
        // Code to run if the request succeeds (is done);
        // The response is passed to the function
        .done(function (json) {
            var vote_diff = json.vote_diff;
            if (vote_value == -1) {
                if (upvote_item.attr("style") != undefined) { // remove upvote, if any.
                    upvote_item.removeAttr("style")
                }
                if (downvote_item.attr("style") != undefined) { // Canceled downvote
                    downvote_item.removeAttr("style")
                } else {                                // new downvote
                    downvote_item.attr("style", "color : orangered")
                }
            } else if (vote_value == 1) {               // remove downvote
                if (downvote_item.attr("style") != undefined) {
                    downvote_item.removeAttr("style")
                }

                if (upvote_item.attr("style") != undefined) { // remove upvote, if any.
                    upvote_item.removeAttr("style");
                } else {                                // adding new upvote
                    upvote_item.attr("style", "color : orangered");
                }
            }

            // update score element
            points = parseInt(points_item.text());
            points_item.text(points += vote_diff);
            points_suffix_selector = "#" + id + "-points-suffix";
            points_suffix = $(points_suffix_selector);
            points_suffix.text(get_points_suffix(points));
        })
        // Code to run if the request fails; the raw request and
        // status codes are passed to the function
        .fail(function (data) {
            var fail_text = document.createElement('p');
            fail_text.innerText = data.responseJSON.error;
            fail_text.setAttribute('class', 'text-danger');
            $("#"+id+"-media-body").prepend(fail_text);
            setTimeout(function () {
                fail_text.remove();
            }, 10000);
            return false;
        });
}

// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function get_points_suffix(val) {
    if (val == 1 || val == -1) {
        return "point";
    }
    else {
        return "points";
    }
}

function get_topic_name(){
    return window.location.pathname.split('/')[2];
}

function get_post_id()
{
    return window.location.pathname.split('/')[4];
}

var getUrlParameter = function getUrlParameter(sParam) {
    var sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : sParameterName[1];
        }
    }
};