import logging
from importlib import import_module
from typing import List, TypeVar, Dict, Callable
from miniTicktok_api.service_providers.service_prodiver import ServiceProvider

T = TypeVar('T')


class ServiceNotFoundException(Exception):
    def __init__(self, name: type):
        self.message = f'Service of type {name} not found!'
        super().__init__(self.message)


class Services:
    logger = logging.getLogger('app_logger')

    services: List[str] = [
        'miniTicktok_api.service_providers.mongodb.MongodbDatabaseServiceProvider',
    ]

    singletons: Dict[str, Callable] = {}

    instances: Dict[str, ServiceProvider] = {}

    def __init__(self):
        service_providers: List[ServiceProvider] = []

        for service_provider_path in self.services:
            module = service_provider_path.rpartition('.')[0]
            class_name = service_provider_path.rpartition('.')[-1]
            service_provider_class = getattr(import_module(module), class_name)
            service_provider_instance: ServiceProvider = service_provider_class(self)
            service_provider_instance.register()
            service_providers.append(service_provider_instance)

        for service_provider_instance in service_providers:
            service_provider_instance.boot()

    def singleton(self, name: str, factory: Callable):
        self.singletons[name] = factory

    def get(self, name: T) -> T:
        name_str = name.__name__

        if name_str in self.singletons:
            if name_str not in self.instances:
                self.instances[name_str] = self.singletons[name_str]()

            return self.instances[name_str]

        raise ServiceNotFoundException(name)


services = Services()
