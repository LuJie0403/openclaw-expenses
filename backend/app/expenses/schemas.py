

class StardustNode(BaseModel):
    id: str
    name: str
    symbolSize: float
    value: float
    category: str

class StardustLink(BaseModel):
    source: str
    target: str

class StardustCategory(BaseModel):
    trans_type_name: str

class StardustData(BaseModel):
    nodes: List[StardustNode]
    links: List[StardustLink]
    categories: List[StardustCategory]
