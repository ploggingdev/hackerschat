var base_url = "https://www.hackerschat.net/";

function subscription(topic_name) {

    var csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    var subscription_url = base_url + 'chatsubscription/';

    $.ajax({

        url: subscription_url,

        data: {
            topic_name: topic_name
        },

        type: "POST",

        dataType: "json",
    })

        .done(function (json) {
            var button_text = json.button_text;
            var message_text = json.message;
            var button_id = topic_name + "-subscription";
            $("#"+button_id).html(button_text);
            var message = document.createElement('p');
            message.innerText = message_text;
            message.setAttribute('class', 'text-success');
            $('#server_messages').prepend(message);
            setTimeout(function () {
                message.remove();
            }, 10000);
            return false;
        })
        
        .fail(function (data) {
            var fail_text = document.createElement('p');
            fail_text.innerText = data.responseJSON.error;
            fail_text.setAttribute('class', 'text-danger');
            $('#server_messages').prepend(fail_text);
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