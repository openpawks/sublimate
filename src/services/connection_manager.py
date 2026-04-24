from __future__ import annotations

import asyncio

from fastapi import WebSocket


class WebSocketConnection:
    def __init__(
        self,
        websocket: WebSocket,
        connection_manager: ConnectionManager,
        id: int = None,
    ):
        """
        Object to keep track of which chats the websocket has connected to
        """
        self.websocket = websocket
        self.connection_manager = connection_manager
        self.id = id
        self.chat_connections = {}

    def disconnect_chat(self, chat_id: int):
        return self.connection_manager.disconnect_chat_websocket(
            chat_id, self.chats_by_id[chat_id]
        )


class ConnectionManager:
    def __init__(self):
        """
        Manage websocket connections between different chats
        Allow one websocket per client, with client having
        multiple chats being able to be viewed
        """
        self.active_connections = {}
        self.chat_connections = {
            # store ids chat id : chat id for this websocket, avoid O(n) removal time
        }

    def connect(self, websocket: WebSocket):
        new_id = max(len(list(self.active_connections.keys())), 0) + 1

        new_connection = WebSocketConnection(
            websocket=websocket, connection_manager=self
        )

        self.active_connections[new_id] = new_connection

        return new_connection

    def get_websocket_by_id(self, id: int) -> WebSocketConnection:
        return self.active_connections.get(id)

    def connect_chat_chat_id(
        self, websocket_connection: WebSocketConnection, chat_id: int
    ):
        chat = self.chat_connections.get(chat_id)

        if not chat:
            self.chat_connections[chat_id] = {}

        chat_websocket_id = max(len(list(self.chat_connections[chat_id].keys())), 0) + 1
        self.chat_connections[chat_id][chat_websocket_id] = websocket_connection
        websocket_connection.chat_connections[chat_id][chat_websocket_id]

        return chat_websocket_id

    def disconnect_chat_websocket(self, chat_id: int, websocket_connection_id: int):
        """
        Store each connection in WebSocketConnection in order to avoid O(n^2)
        deletions
        """
        del self.chat_connections[chat_id][websocket_connection_id].chat_connections[
            chat_id
        ]
        del self.chat_connections[chat_id][websocket_connection_id]

    def disconnect(self, websocket_connection: WebSocketConnection):
        """
        Disconnect websocket connection
        """
        for chat_id, websocket_connection_id in websocket_connection:
            self.disconnect_chat_websocket(chat_id, websocket_connection_id)
        del self.active_connections[websocket_connection.id]

    def broadcast_message_chat(self, message_json: dict, chat_id: int):
        """
        Broadcast (full) message to chat
        """
        await asyncio.gather(
            *[
                asyncio.create_task(ws_conn.websocket.send_json(message_json))
                for ws_conn in self.chat_connections.get(chat_id, {}).values()
            ]
        )

    async def broadcast_stream_to_chat(self, message_chunk: dict, chat_id: int):
        """
        Broadcast chunk to chat (like if the AI is streaming its message)
        """
        await asyncio.gather(
            *[
                asyncio.create_task(ws_conn.websocket.send_json(message_chunk))
                for ws_conn in self.chat_connections.get(chat_id, {}).values()
            ]
        )


connection_manager = ConnectionManager()
