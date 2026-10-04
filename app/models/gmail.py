from pydantic import BaseModel, ConfigDict, Field


class GmailMessageListParams(BaseModel):
    user_id: str = Field(default="me", alias="userId")
    max_results: int = Field(alias="maxResults")
    query: str = Field(alias="q")
    page_token: str | None = Field(default=None, alias="pageToken")

    model_config = ConfigDict(populate_by_name=True)

    def as_params(self) -> dict[str, str | int]:
        return self.model_dump(by_alias=True, exclude_none=True)


class GmailMessageGetParams(BaseModel):
    user_id: str = Field(default="me", alias="userId")
    message_id: str = Field(alias="id")
    format: str = "full"

    model_config = ConfigDict(populate_by_name=True)

    def as_params(self) -> dict[str, str]:
        return self.model_dump(by_alias=True)


class GmailMessageReference(BaseModel):
    message_id: str = Field(alias="id")

    model_config = ConfigDict(populate_by_name=True)


class GmailMessageListResponse(BaseModel):
    messages: list[GmailMessageReference] = Field(default_factory=list)
    next_page_token: str | None = Field(default=None, alias="nextPageToken")

    model_config = ConfigDict(populate_by_name=True)
