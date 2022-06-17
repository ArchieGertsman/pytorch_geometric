from abc import abstractmethod
from collections.abc import MutableMapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Union

from torch import LongTensor

from torch_geometric.typing import EdgeTensorType, EdgeType
from torch_geometric.utils.mixin import CastMixin


class EdgeLayout(Enum):
    COO = 'COO'
    CSC = 'CSC'
    CSR = 'CSR'
    LIL = 'LIL'


@dataclass
class EdgeAttr(CastMixin):
    r"""Defines the attributes of an :obj:`MaterializedGraph` edge."""

    # The layout of the edge representation
    layout: Optional[EdgeLayout] = None

    # The type of the edge
    edge_type: Optional[Any] = None


class MaterializedGraph(MutableMapping):
    def __init__(self, edge_attr_cls: Any = EdgeAttr):
        r"""Initializes the materialized graph. Implementor classes can
        customize the ordering and required nature of their :class:`EdgeAttr`
        edge attributes by subclassing :class:`EdgeAttr` and passing the
        subclass as :obj:`attr_cls`."""
        super().__init__()
        self.__dict__['_edge_attr_cls'] = edge_attr_cls

    # Core ####################################################################

    @abstractmethod
    def _put_edge_index(self, edge_index: EdgeTensorType,
                        edge_attr: EdgeAttr) -> bool:
        return None

    def put_edge_index(self, edge_index: EdgeTensorType, *args,
                       **kwargs) -> bool:
        r"""Synchronously adds an edge_index tensor to the materialized graph.

        Args:
            tensor(EdgeTensorType): an edge_index in a format specified in
            attr.
            **attr(EdgeAttr): the edge attributes.
        """
        edge_attr = self._edge_attr_cls.cast(*args, **kwargs)
        if not edge_attr.layout:
            raise AttributeError(
                "An edge layout is required to store an edge index, but one "
                "was not provided.")

        # NOTE implementations should take care to ensure that `SparseTensor`
        # objects are treated properly here.
        return self._put_edge_index(edge_index,
                                    self._edge_attr_cls.cast(*args, **kwargs))

    @abstractmethod
    def _get_edge_index(self, edge_attr: EdgeAttr) -> EdgeTensorType:
        return None

    def get_edge_index(self, *args, **kwargs) -> EdgeTensorType:
        r"""Synchronously gets an edge_index tensor from the materialized
        graph, **returning it in COO format**.

        Args:
            **attr(EdgeAttr): the edge attributes.

        Returns:
            EdgeTensorType: an edge_index tensor corresonding to the provided
            attributes, or None if there is no such tensor.
        """
        return self._get_edge_index(self._edge_attr_cls.cast(*args, **kwargs))

    def sample(
        self,
        input_nodes: Union[LongTensor, Dict[EdgeType, LongTensor]],
        *args,
        **kwargs,
    ) -> None:
        r"""Samples the materialized graph to obtain a sampled subgraph,
        utilizing sampling routines provided by `torch_sparse`.

        Args:
            input_nodes: the input nodes to sample from, either provided as a
                :class:`torch.LongTensor` or a dictionary mapping node type to
                a list of input nodes.

        Notes:
            Most sampling methods operate efficiently on sorted edge indices.
            This class makes no guarantees on the formats of the edge indices
            that are passed as input. Implementations should account for this
            (e.g. by converting all edge indices to CSC) before sampling.
        """
        # NOTE for the future: this is expected to call a C++ implementation
        # in pyg-lib.
        return None

    # Python built-ins ########################################################

    def __setitem__(self, key: EdgeAttr, value: EdgeTensorType):
        key = self._edge_attr_cls.cast(key)
        self.put_edge_index(value, key)

    def __getitem__(self, key: EdgeAttr) -> EdgeTensorType:
        key = self._edge_attr_cls.cast(key)
        return self.get_edge_index(key)

    def __delitem__(self, key):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError