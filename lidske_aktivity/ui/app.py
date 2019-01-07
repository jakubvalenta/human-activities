import logging
from typing import Callable, Optional

from PIL import Image

from lidske_aktivity import (
    __authors__, __copyright__, __title__, __uri__, __version__,
)
from lidske_aktivity.bitmap import draw_pie_chart, gen_random_slices
from lidske_aktivity.config import save_config
from lidske_aktivity.store import Store, TFractions
from lidske_aktivity.ui.lib import Application, StatusIcon, show_about
from lidske_aktivity.ui.settings import Settings
from lidske_aktivity.ui.setup import Setup

logger = logging.getLogger(__name__)


class Application(Application):
    title = __title__

    store: Store
    on_quit: Callable
    status_icon: StatusIcon
    last_percents: Optional[TFractions] = None

    def __init__(self, store: Store, on_quit: Callable, *args, **kwargs):
        self.store = store
        self.on_quit = on_quit  # type: ignore
        super().__init__(*args, **kwargs)

    def on_init(self):
        self.status_icon = StatusIcon(
            on_setup=self.show_setup,
            on_settings=self.show_settings,
            on_about=self.show_about,
            on_quit=self.quit
        )
        if self.store.config.show_setup:
            self.store.config.show_setup = False
            self.show_setup()

    def show_setup(self):
        Setup(
            self.store.config,
            on_finish=self.on_setup_finish,
            parent=self.frame
        )

    def on_setup_finish(self, setup: Setup):
        self.store.config = setup.config
        self.status_icon.refresh_menu()
        save_config(self.store.config)

    def show_settings(self):
        Settings(
            self.store.config,
            self.on_settings_accept,
            parent=self.frame
        )

    def on_settings_accept(self, settings: Settings):
        self.store.config = settings.config
        self.status_icon.refresh_menu()
        save_config(self.store.config)

    def show_about(self):
        image = draw_pie_chart(148, list(gen_random_slices(3, 8)))
        show_about(
            image=image,
            title=__title__,
            version=__version__,
            copyright=__copyright__,
            uri=__uri__,
            authors=__authors__
        )

    def _should_update(self) -> bool:
        if self.store.percents == self.last_percents:
            return False
        self.last_percents = self.store.percents
        return True

    def _create_icon_image(self) -> Image:
        slices_frac = list(self.store.percents.values())
        logger.info('Updating icon with slices %s', slices_frac)
        return draw_pie_chart(self.calc_icon_size(), slices_frac)

    def _create_tooltip(self) -> str:
        return '\n'.join(
            '{text}: {fraction:.2%}'.format(
                text=self.store.get_text(path),
                fraction=fraction
            )
            for path, fraction in self.store.percents.items()
        )

    def on_tick(self, pulse: bool = True):
        if self._should_update():
            image = self._create_icon_image()
            tooltip = self._create_tooltip()
            self.update_icon(image, tooltip)
            self.update_menu()

    def quit(self):
        super().quit()
        self.status_icon.destroy()

    def on_exit(self):
        self.on_quit()


def run_app(store: Store, on_quit: Callable):
    app = Application(store, on_quit)
    app.run()
