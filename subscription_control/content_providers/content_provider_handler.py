import importlib
from pathlib import Path
from typing import Any, Optional, Type

from subscription_control.logger import logger
from subscription_control.schemas import ContentProviderSystem, SchemaProductBase


class ContentHandler:
    def __init__(self):
        self.providers: dict[str, Type[ContentProviderSystem]] = {}
        self._load_providers()

    def _load_providers(self) -> None:
        """
        Loads all content provider classes from the content_providers directory
        """
        # Lista de arquivos a serem ignorados (arquivos de infraestrutura, não provedores)
        excluded_files = [
            'content_handler',
            'content_provider_handler', 
            'content_providers', 
            'products_handler',
            '__init__',
            'utils',  # excluindo arquivos comuns antecipadamente
            'helpers',
            'constants',
            'exceptions'
        ]
        
        current_dir = Path(__file__).parent
        for file_path in current_dir.glob('*.py'):
            if file_path.stem not in excluded_files:
                module_name = f'{current_dir.parent.name}.{current_dir.name}.{file_path.stem}'
                module = importlib.import_module(module_name)
                self._register_provider_classes(module, file_path.stem)

    def _register_provider_classes(self, module, module_name: str) -> None:
        """
        Registers provider classes found in the module
        """
        found_provider = False
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, ContentProviderSystem) and attr != ContentProviderSystem:
                self.providers[module_name] = attr
                logger.info(f'Registered provider: {module_name}')
                found_provider = True
                break
        
        if not found_provider:
            logger.warning(f"No ContentProviderSystem implementation found in {module_name}")

    async def get_content(self, provider_name: str, limit: Optional[int] = None, **kwargs) -> Any:
        """
        Dynamically calls the get_content method from the specified provider

        Args:
            provider_name (str): Name of the provider file (without .py extension)
            limit (int, optional): Limit of items to fetch. Defaults to None.
            **kwargs: Additional arguments to pass to the provider's get_content method

        Returns:
            Any: Content from the provider

        Raises:
            ValueError: If provider_name is not found
        """
        provider_instance = self._get_provider_instance(provider_name)
        return await provider_instance.get_content(limit, **kwargs)

    async def standardize_content(self, provider_name: str, limit: Optional[int] = None, **kwargs) -> list[SchemaProductBase]:
        """
        Dynamically calls the standardize_content method from the specified provider

        Args:
            provider_name (str): Name of the provider file (without .py extension)
            limit (int, optional): Limit of items to fetch. Defaults to None.
            **kwargs: Additional arguments to pass to the provider's standardize_content method

        Returns:
            list[SchemaProductBase]: Standardized content from the provider

        Raises:
            ValueError: If provider_name is not found
        """
        provider_instance = self._get_provider_instance(provider_name)
        content_dicts = await provider_instance.standardize_content(limit, **kwargs)
        return content_dicts

    def _get_provider_instance(self, provider_name: str) -> ContentProviderSystem:
        """
        Retrieves an instance of the specified provider

        Args:
            provider_name (str): Name of the provider file (without .py extension)

        Returns:
            ContentProviderSystem: Instance of the provider

        Raises:
            ValueError: If provider_name is not found
        """
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")
        provider_class = self.providers[provider_name]
        return provider_class()
