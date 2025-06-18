##
## This code is directly taken/adapted from code shared by Tim Repke, PIK
##

from enum import Enum
from typing import Annotated

class Attribute():
    AttributeId: int = 0
    AttributeName: str
    AttributeSetDescription: str = ''
    #AttributeType: AttrType = AttrType.NOT_SELECTABLE
    ParentAttributeId: int = 0
    SetId: int = 0

    #AttributeSetId: int = 0
    AttributeSetDescription: str = ''
    HasChildren: bool = False

    #ExtURL: str = ''
    #ExtType: str = ''
    #OriginalAttributeID: int = 0
    #Attributes: AttrList | None = None