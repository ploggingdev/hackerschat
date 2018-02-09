from django.conf.urls import url
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from mainapp.consumers import ChatConsumer, ScrollbackConsumer

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            url("^topics/(?P<topic_name>[a-z]+)/chat/ws/$", ChatConsumer),
            url("^topics/(?P<topic_name>[a-z]+)/chat/scrollback/$", ScrollbackConsumer),
        ])
    ),
})