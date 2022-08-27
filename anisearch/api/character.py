from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

from .base import CoverImage, DateModel, MediaTitle, NotFound, fetch_data
from .formatters import format_description


@dataclass
class Name:
    full: Optional[str]
    native: Optional[str]
    alternative: Sequence[str] = field(default_factory=list)

    def __str__(self) -> str:
        # https://anilist.co/character/135069 - both full and native name can be null
        if not self.full and not self.native:
            return " • ".join(self.alternative) if self.alternative else "NAME MISSING ???"
        if self.full and self.native and self.full == self.native:
            return self.full

        return f"{self.full} ({self.native})" if self.native else self.full


@dataclass
class MediaNode:
    siteUrl: str
    type: str
    title: MediaTitle

    @classmethod
    def from_data(cls, data: dict) -> MediaNode:
        return cls(title=MediaTitle(**data.pop("title", {})), **data)


@dataclass
class CharacterData:
    name: Name
    image: CoverImage
    description: Optional[str]
    gender: str
    dateOfBirth: DateModel
    age: Optional[str]
    siteUrl: str
    media_nodes: Sequence[MediaNode] = field(default_factory=list)

    @property
    def character_summary(self) -> str:
        return format_description(self.description, 1800) if self.description else ""

    @property
    def appeared_in(self) -> str:
        return "\n".join(
            f"[{media.title}]({media.siteUrl}) ({media.type.title()})"
            for media in self.media_nodes
        )

    @classmethod
    def from_data(cls, data: dict) -> CharacterData:
        nodes = data.pop("media", {}).get("nodes", [])
        return cls(
            name=Name(**data.pop("name", {})),
            image=CoverImage(**data.pop("image", {})),
            dateOfBirth=DateModel(**data.pop("dateOfBirth", {})),
            media_nodes=[MediaNode.from_data(node) for node in nodes],
            **data,
        )

    @classmethod
    async def request(cls, session, query: str, **kwargs) -> NotFound | Sequence[CharacterData]:
        result = await fetch_data(session, query, **kwargs)
        if result.get("message"):
            return NotFound(**result)

        all_items = result.get("data", {}).get("Page", {}).get("characters", [])
        return (
            [cls.from_data(item) for item in all_items]
            if all_items
            else NotFound("Sad trombone. No results!")
        )
