from .logging import debug
from .logging import exception_log
from .types import ClientConfig
from .typing import Generator, List, Optional, Set, Dict
from .workspace import enable_in_project, disable_in_project
import sublime
import urllib.parse


class WindowConfigManager(object):
    def __init__(self, window: sublime.Window, global_configs: Dict[str, ClientConfig]) -> None:
        self._window = window
        self._global_configs = global_configs
        self._disabled_for_session = set()  # type: Set[str]
        self.all = {}  # type: Dict[str, ClientConfig]
        self.update()

    def get_configs(self) -> List[ClientConfig]:
        return sorted(self.all.values(), key=lambda config: config.name)

    def match_view(self, view: sublime.View, include_disabled: bool = False) -> Generator[ClientConfig, None, None]:
        """
        Yields configurations where:

        - the configuration's "selector" matches with the view's base scope, and
        - the view's URI scheme is an element of the configuration's "schemes".
        """
        try:
            uri = view.settings().get("lsp_uri")
            if not isinstance(uri, str):
                return
            scheme = urllib.parse.urlparse(uri).scheme
            for config in self.all.values():
                if config.match_view(view, scheme) and (config.enabled or include_disabled):
                    yield config
        except (IndexError, RuntimeError):
            pass

    def update(self, updated_config_name: Optional[str] = None) -> None:
        project_settings = (self._window.project_data() or {}).get("settings", {}).get("LSP", {})
        if updated_config_name is None:
            self.all.clear()
        for name, config in self._global_configs.items():
            if updated_config_name and updated_config_name != name:
                continue
            overrides = project_settings.pop(name, None)
            if isinstance(overrides, dict):
                debug("applying .sublime-project override for", name)
            else:
                overrides = {}
            if name in self._disabled_for_session:
                overrides["enabled"] = False
            self.all[name] = ClientConfig.from_config(config, overrides)
        for name, c in project_settings.items():
            if updated_config_name and updated_config_name != name:
                continue
            debug("loading project-only configuration", name)
            try:
                self.all[name] = ClientConfig.from_dict(name, c)
            except Exception as ex:
                exception_log("failed to load project-only configuration {}".format(name), ex)
        self._window.run_command("lsp_recheck_sessions", {'config_name': updated_config_name})

    def enable_config(self, config_name: str) -> None:
        if not self._reenable_disabled_for_session(config_name):
            enable_in_project(self._window, config_name)
        self.update(config_name)

    def disable_config(self, config_name: str, only_for_session: bool = False) -> None:
        if only_for_session:
            self._disable_for_session(config_name)
        else:
            disable_in_project(self._window, config_name)
        self.update(config_name)

    def _disable_for_session(self, config_name: str) -> None:
        self._disabled_for_session.add(config_name)

    def _reenable_disabled_for_session(self, config_name: str) -> bool:
        try:
            self._disabled_for_session.remove(config_name)
            return True
        except KeyError:
            return False
