from __future__ import annotations

import os

from textual.app import App

from app.tui.api_client import BackendApiClient
from app.tui.screens import MainScreen


class BookingTuiApp(App[None]):
    TITLE = "Booking TUI"
    CSS = """
    Screen {
        layout: vertical;
        padding: 1;
    }

    VerticalScroll {
        height: 1fr;
    }

    .section {
        border: solid $panel;
        padding: 1;
        margin: 0 0 1 0;
    }

    Vertical {
        height: auto;
    }

    Horizontal {
        height: auto;
    }

    Label {
        margin: 0 0 1 0;
    }

    Input, Button {
        margin: 0 0 1 0;
    }

    #output {
        height: 1fr;
        min-height: 12;
        border: solid $success;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        base_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
        self.api_client = BackendApiClient(base_url=base_url)

    def on_mount(self) -> None:
        self.push_screen(MainScreen(api_client=self.api_client))

    def exit(self, result: None = None, return_code: int = 0, message: object = None) -> None:
        self.api_client.close()
        super().exit(result=result, return_code=return_code, message=message)


def main() -> None:
    BookingTuiApp().run()


if __name__ == "__main__":
    main()

