from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class PluginMetadata(BaseModel):
    """Plugin metadata model."""
    name: str
    version: str
    description: str
    author: str
    website: Optional[str] = None
    dependencies: List[str] = []
    settings_schema: Optional[Dict[str, Any]] = None

class BasePlugin(ABC):
    """Base class for all Maily plugins."""

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass

    @abstractmethod
    async def initialize(self, settings: Dict[str, Any]) -> None:
        """Initialize the plugin with settings."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up plugin resources."""
        pass

    @abstractmethod
    async def validate_settings(self, settings: Dict[str, Any]) -> bool:
        """Validate plugin settings."""
        pass

class PluginManager:
    """Manages plugin lifecycle and interactions."""

    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._settings: Dict[str, Dict[str, Any]] = {}

    async def register_plugin(
        self,
        plugin: BasePlugin,
        settings: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register and initialize a plugin."""
        plugin_name = plugin.metadata.name

        if plugin_name in self._plugins:
            raise ValueError(f"Plugin {plugin_name} is already registered")

        # Validate settings if provided
        if settings and not await plugin.validate_settings(settings):
            raise ValueError(f"Invalid settings for plugin {plugin_name}")

        # Initialize plugin
        await plugin.initialize(settings or {})

        # Store plugin and settings
        self._plugins[plugin_name] = plugin
        self._settings[plugin_name] = settings or {}

    async def unregister_plugin(self, plugin_name: str) -> None:
        """Unregister and cleanup a plugin."""
        if plugin_name not in self._plugins:
            raise ValueError(f"Plugin {plugin_name} is not registered")

        plugin = self._plugins[plugin_name]
        await plugin.cleanup()

        del self._plugins[plugin_name]
        del self._settings[plugin_name]

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get a registered plugin by name."""
        return self._plugins.get(plugin_name)

    def list_plugins(self) -> List[PluginMetadata]:
        """List all registered plugins."""
        return [plugin.metadata for plugin in self._plugins.values()]

    async def update_plugin_settings(
        self,
        plugin_name: str,
        settings: Dict[str, Any]
    ) -> None:
        """Update settings for a registered plugin."""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin {plugin_name} is not registered")

        if not await plugin.validate_settings(settings):
            raise ValueError(f"Invalid settings for plugin {plugin_name}")

        # Reinitialize plugin with new settings
        await plugin.cleanup()
        await plugin.initialize(settings)

        self._settings[plugin_name] = settings

    def get_plugin_settings(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get current settings for a plugin."""
        return self._settings.get(plugin_name)

    async def cleanup_all(self) -> None:
        """Clean up all registered plugins."""
        for plugin_name in list(self._plugins.keys()):
            await self.unregister_plugin(plugin_name)
