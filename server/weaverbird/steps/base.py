from abc import ABC, abstractmethod

from pandas import DataFrame
from pydantic.main import BaseModel

from weaverbird.types import DomainRetriever


class BaseStep(BaseModel, ABC):
    name: str

    @abstractmethod
    def execute(self, df: DataFrame, domain_retriever: DomainRetriever) -> DataFrame:
        ...