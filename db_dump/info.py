import platform
import sysconfig
from dataclasses import dataclass, field
from datetime import datetime
from typing import AnyStr, Sequence, MutableSequence, Tuple, Dict, NewType

from dataclasses_json import DataClassJsonMixin
from sqlalchemy import Table
from sqlalchemy.orm import Mapper

DateTime = NewType('DateTime', datetime)


@dataclass
class InfoBase:
    doc: AnyStr=None


@dataclass
class SchemaItemInfo(InfoBase):
    __visit_name__: str=None


class Mixin:
    pass


@dataclass
class GenerationInfo(DataClassJsonMixin):
    created: DateTime = field(default_factory=lambda: datetime.now())
    system_alias: Tuple[AnyStr, AnyStr, AnyStr] = field(
        default_factory=lambda: platform.system_alias(platform.system(), platform.release(), platform.version()))
    python_version: AnyStr = field(default_factory=lambda: platform.python_version())
    config_vars: Dict[AnyStr, object] = field(default_factory=sysconfig.get_config_vars)
    # environ: Dict=field(default_factory=lambda: os.environ)


@dataclass
class KeyMixin:
    key: str=None


@dataclass
class CompiledMixin:
    compiled: str=None


@dataclass
class PairInfo(Mixin, InfoBase):
    table: AnyStr=None
    column: AnyStr=None


@dataclass
class LocalRemotePairInfo(Mixin, InfoBase):
    local: PairInfo=None
    remote: PairInfo=None


@dataclass
class InspectionAttrInfo(InfoBase):
    is_mapper: bool=None
    is_property: bool=None
    is_attribute: bool=None


@dataclass
class StrategizedPropertyInfo(InspectionAttrInfo):
    pass



@dataclass
class RelationshipInfo(KeyMixin, Mixin, StrategizedPropertyInfo):
    argument: object=None
    #mapper_key: AnyStr=None
    secondary: object=None
    #backref: AnyStr=None
    local_remote_pairs: object=None
    direction: AnyStr=None


@dataclass
class ColumnInfo(KeyMixin, CompiledMixin, Mixin, SchemaItemInfo):
    type: 'TypeInfo'=None
    table: AnyStr=None
    name: AnyStr=None


@dataclass
class MapperInfo(Mixin):
    primary_key: object=None
    columns: object=None
    relationships: object=None
    local_table: object=None
    entity: object=None


@dataclass
class TypeInfo(CompiledMixin, Mixin, InfoBase):
    pass


@dataclass
class TableInfo(KeyMixin, Mixin, SchemaItemInfo):
    name: AnyStr=None
    primary_key: Sequence[AnyStr]=None
    columns: Sequence[ColumnInfo]=None


class MapperInfosMixin:
    @property
    def mapper_infos(self) -> dict:
        return self._mapper_infos

    def get_mapper_info(self, mapper_key: AnyStr) -> MapperInfo:
        assert mapper_key in self.mapper_infos
        return self.mapper_infos[mapper_key]

    def set_mapper_info(self, mapper_key: AnyStr, mapper_info: MapperInfo) -> None:
        self.mapper_infos[mapper_key] = mapper_info


@dataclass
class ProcessInfo():
    generation: object=None
    mappers: MutableSequence[MapperInfo]=field(default_factory=lambda: [])
    tables: MutableSequence[TableInfo]=field(default_factory=lambda: {})


@dataclass
class GenerationMixin:
    generation: GenerationInfo=field(default_factory=GenerationInfo)


@dataclass
class ProcessStruct(GenerationMixin):
    mappers: MutableSequence[Mapper]=field(default_factory=lambda: [])
    tables: MutableSequence[Table]=field(default_factory=lambda: [])


def get_process_struct():
    ps = ProcessStruct()
    return ps


