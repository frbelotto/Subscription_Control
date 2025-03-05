import asyncio
import os
import re
from typing import Optional

import httpx

from subscription_control.content_providers.content_providers import list_content_provider
from subscription_control.schemas import (
    ContentProviderSystem,
    SchemaProductBase,
)
from subscription_control.settings import Settings

class ApiProvider(ContentProviderSystem):
    """
    Class that implements the ContentProviderSystem interface for the TMDB API, one of the content providers that the system can use.
    """

    def __init__(self, **kwargs):
        self.client = httpx.AsyncClient()
        self.api_key = Settings().TMDB_API_KEY
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def get_content(self, limit: Optional[int] = None) -> list[dict]:
        """
        Async function that fetches the content from the TMDB API and stores it in the results attribute.
        The limit parameter is used to limit the number of results fetched, if it is not provided all the results will be fetched.
        The results attribute will be a list of dictionaries, each dictionary will have the keys 'title' and 'id', kept under the results key.
        """
        if limit is not None:
            if limit <= 0:
                raise ValueError('Limit must be positive')
            if limit > 100:
                raise ValueError('Limit cannot exceed 100')

        self.results = []
        url = f'https://api.themoviedb.org/3/movie/popular?api_key={self.api_key}'
        while url:
            response = await self.client.get(url)
            data = response.json()
            self.results.extend(data['results'])
            if limit is not None and len(self.results) >= limit:
                self.results = self.results[:limit]
                break
            url = data.get('next')  # Use .get() to avoid KeyError
        return self.results

    @staticmethod
    async def __get_movie_image(client, movie_id, api_key) -> str | None:
        url = f'https://api.themoviedb.org/3/movie/{movie_id}/images?api_key={api_key}'
        try:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                if data['posters']:
                    image_url = f'https://image.tmdb.org/t/p/w500{data["posters"][0]["file_path"]}'
                    return image_url
                return None
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
    async def __get_movie_rating(client, movie_id, api_key) -> float | None:
        url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}'
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()['vote_average']
            return None
        except:
            return None

    @staticmethod
    async def __get_movie_description(client, movie_id, api_key) -> str | None:
        url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}'
        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                description = data['overview']
                return description
            return None
        except:
            return None

    async def __get_movie_data(self, movie_id: str) -> dict:
        rating_task = self.__get_movie_rating(self.client, movie_id, self.api_key)
        description_task = self.__get_movie_description(self.client, movie_id, self.api_key)
        image_task = self.__get_movie_image(self.client, movie_id, self.api_key)

        rating, description, image_url = await asyncio.gather(rating_task, description_task, image_task)
        return {
            'value': rating,
            'description': description,
            'image': image_url,
        }

    async def standardize_content(self, limit: int = None) -> list[dict]:
        await self.get_content(limit)
        tasks = [self.__get_movie_data(item['id']) for item in self.results]
        results = await asyncio.gather(*tasks)
        filename = os.path.basename(__file__).replace('.py', '')
        seller_db = await list_content_provider(api_engine_module_name=filename)
        seller_id = seller_db[0].id

        content_list = []
        for item, result in zip(self.results, results):
            ext_id = str(item['id'])  # Convert id to string
            name = item['title']
            product = SchemaProductBase(content_provider_id=seller_id, ext_id=ext_id, name=name, **result)
            content_list.append(product)
        return content_list
