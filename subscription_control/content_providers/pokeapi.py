import asyncio
import os
import re
from typing import Optional

import httpx

from subscription_control.content_providers.content_providers import list_content_provider
from subscription_control.schemas import ContentProviderSystem, SchemaProductBase


class ApiProvider(ContentProviderSystem):
    """
    Class that implements the ContentProviderSystem interface for the PokeApi, one of the content providers that the system can use.
    """

    def __init__(self, **kwargs):
        self.client = httpx.AsyncClient()
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def get_content(self, limit: Optional[int] = None) -> list[dict]:
        """
        Async function that fetches the content from the PokeApi and stores it in the results attribute.
        The limit parameter is used to limit the number of results fetched, if it is not provided all the results will be fetched.
        The results attribute will be a list of dictionaries, each dictionary will have the keys 'name' and 'url', kept under the results key.
        """

        self.results = []
        url = 'https://pokeapi.co/api/v2/pokemon/'
        while url:
            response = await self.client.get(url)
            data = response.json()
            self.results.extend(data['results'])
            if limit is not None and len(self.results) >= limit:
                self.results = self.results[:limit]
                break
            url = data['next']
        return self.results

    @staticmethod
    async def __get_pokemon_image(client, pokemon_name) -> str | None:
        url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}/'
        try:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                image_url = data['sprites']['front_default']
                return image_url
            else:
                return None
        except:
            return None

    @staticmethod
    def __extract_id_from_url(url) -> str | None:
        match = re.search(r'/(\d+)/$', url)
        if match:
            return match.group(1)
        return None

    @staticmethod
    async def __get_pokemon_hp(client, pokemon_name) -> int | None:
        url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}/'
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()['stats'][0]['base_stat']
            return None
        except:
            return None

    @staticmethod
    async def __get_pokemon_description(client, pokemon_name) -> str | None:
        url = f'https://pokeapi.co/api/v2/pokemon-species/{pokemon_name.lower()}/'
        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                for entry in data['flavor_text_entries']:
                    if entry['language']['name'] == 'en':
                        description = entry['flavor_text'].replace('\n', ' ').replace('\f', ' ').replace('\\', '')
                        return description
            return None
        except:
            return None

    async def __get_pokemon_data(self, name: str) -> dict:
        hp_task = self.__get_pokemon_hp(self.client, name)
        description_task = self.__get_pokemon_description(self.client, name)
        image_task = self.__get_pokemon_image(self.client, name)

        hp, description, image_url = await asyncio.gather(hp_task, description_task, image_task)
        return {'value': hp, 'description': description, 'image': image_url}

    async def standardize_content(self, limit: int = None) -> list[dict]:
        await self.get_content(limit)
        tasks = [self.__get_pokemon_data(item['name']) for item in self.results]
        results = await asyncio.gather(*tasks)
        filename = os.path.basename(__file__).replace('.py', '')
        seller_db = await list_content_provider(api_engine_module_name=filename)
        seller_id = seller_db[0].id

        content_list = []
        for item, result in zip(self.results, results):
            ext_id = self.__extract_id_from_url(item['url'])
            name = item['name']
            product = SchemaProductBase(content_provider_id=seller_id, ext_id=ext_id, name=name, **result)
            content_list.append(product)
        return content_list
