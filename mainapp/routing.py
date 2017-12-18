from channels.routing import route
from channels import include
from mainapp.consumers import chat_connect, chat_disconnect, chat_receive, scrollback_connect, scrollback_disconnect, scrollback_receive

chat_routing = [
    route("websocket.connect", chat_connect),
    route("websocket.receive", chat_receive),
    route("websocket.disconnect", chat_disconnect)
]

scrollback_routing = [
    route("websocket.connect", scrollback_connect),
    route("websocket.receive", scrollback_receive),
    route("websocket.disconnect", scrollback_disconnect)
]

channel_routing = [
    include(chat_routing, path=r"^/topics/(?P<topic_name>[a-z]+)/chat/ws/$"),
    include(scrollback_routing, path=r"^/topics/(?P<topic_name>[a-z]+)/chat/scrollback/$"),
]