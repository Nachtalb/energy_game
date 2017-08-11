class EventHandler:
    _event_handlers = []

    def add_handler(self, handler):
        self._event_handlers.append(handler)

    def notify(self, event):
        for handler in self._event_handlers:
            handler.notify(event)
