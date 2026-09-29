from pydantic import BaseModel, ConfigDict, Field
class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
class PageMeta(SchemaBase):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)
