# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

import abc
from os import PathLike
from pathlib import Path
from typing import Any, Mapping, Union

from promptflow._constants import DEFAULT_ENCODING
from promptflow._utils.flow_utils import is_flex_flow, resolve_flow_path
from promptflow._utils.yaml_utils import load_yaml_string
from promptflow.core._serving.flow_invoker import AsyncFlowInvoker, FlowInvoker
from promptflow.core._utils import init_executable
from promptflow.exceptions import UserErrorException


class FlowBase(abc.ABC):
    def __init__(self, *, data: dict, code: Path, path: Path, **kwargs):
        # flow.dag.yaml's content if provided
        self._data = data
        # working directory of the flow
        self._code = Path(code).resolve()
        # flow file path, can be script file or flow definition YAML file
        self._path = Path(path).resolve()

    @property
    def code(self) -> Path:
        """Working directory of the flow."""
        return self._code

    @property
    def path(self) -> Path:
        """Flow file path. Can be script file or flow definition YAML file."""
        return self._path

    @classmethod
    def load(
        cls,
        source: Union[str, PathLike],
        **kwargs,
    ) -> "Flow":
        """
        Load flow from YAML file.

        :param source: The local yaml source of a flow. Must be a path to a local file.
            If the source is a path, it will be open and read.
            An exception is raised if the file does not exist.
        :type source: Union[PathLike, str]
        :return: A Flow object
        :rtype: Flow
        """
        flow_dir, flow_filename = resolve_flow_path(source)
        flow_path = flow_dir / flow_filename
        with open(flow_path, "r", encoding=DEFAULT_ENCODING) as f:
            flow_content = f.read()
            data = load_yaml_string(flow_content)
        if is_flex_flow(yaml_dict=data, working_dir=flow_dir):
            raise UserErrorException("Please call entry directly for flex flow.")
        return cls._create(code=flow_dir, path=flow_path, data=data)

    @classmethod
    def _create(cls, data, code, path, **kwargs):
        raise NotImplementedError()


class Flow(FlowBase):
    """A Flow in the context of PromptFlow is a sequence of steps that define a task.
    Each step in the flow could be a prompt that is sent to a language model, or simply a function task,
    and the output of one step can be used as the input to the next.
    Flows can be used to build complex applications with language models.

    Simple Example:

    .. code-block:: python

        from promptflow.core import Flow
        flow = Flow.load(source="path/to/flow.dag.yaml")
        result = flow(input_a=1, input_b=2)

    """

    def __call__(self, *args, **kwargs) -> Mapping[str, Any]:
        """Calling flow as a function, the inputs should be provided with key word arguments.
        Returns the output of the flow.
        The function call throws UserErrorException: if the flow is not valid or the inputs are not valid.
        SystemErrorException: if the flow execution failed due to unexpected executor error.

        :param args: positional arguments are not supported.
        :param kwargs: flow inputs with key word arguments.
        :return:
        """

        if args:
            raise UserErrorException("Flow can only be called with keyword arguments.")

        result = self.invoke(inputs=kwargs)
        return result.output

    def invoke(self, inputs: dict, connections: dict = None, **kwargs) -> "LineResult":
        """Invoke a flow and get a LineResult object."""
        # candidate parameters: connections, variant, overrides, streaming

        invoker = FlowInvoker(
            flow=init_executable(flow_dag=self._data, working_dir=self.code),
            # TODO (3027983): resolve the connections before passing to invoker
            connections=connections,
            streaming=True,
            flow_path=self.path,
            working_dir=self.code,
        )
        result = invoker._invoke(
            data=inputs,
        )
        return result

    @classmethod
    def _create(cls, data, code, path, **kwargs):
        return cls(code=code, path=path, data=data, **kwargs)


class AsyncFlow(FlowBase):
    """Async flow is based on Flow, which is used to invoke flow in async mode.

    Simple Example:

    .. code-block:: python

        from promptflow.core import class AsyncFlow
        flow = AsyncFlow.load(source="path/to/flow.dag.yaml")
        result = await flow(input_a=1, input_b=2)

    """

    async def __call__(self, *args, **kwargs) -> Mapping[str, Any]:
        """Calling flow as a function in async, the inputs should be provided with key word arguments.
        Returns the output of the flow.
        The function call throws UserErrorException: if the flow is not valid or the inputs are not valid.
        SystemErrorException: if the flow execution failed due to unexpected executor error.

        :param args: positional arguments are not supported.
        :param kwargs: flow inputs with key word arguments.
        :return:
        """
        if args:
            raise UserErrorException("Flow can only be called with keyword arguments.")

        result = await self.invoke(inputs=kwargs)
        return result.output

    async def invoke(self, inputs: dict, *, connections: dict = None, **kwargs) -> "LineResult":
        """Invoke a flow and get a LineResult object."""

        invoker = AsyncFlowInvoker(
            flow=init_executable(flow_dag=self._data, working_dir=self.code),
            # TODO (3027983): resolve the connections before passing to invoker
            connections=connections,
            streaming=True,
            flow_path=self.path,
            working_dir=self.code,
        )
        result = await invoker._invoke_async(
            data=inputs,
        )
        return result

    @classmethod
    def _create(cls, data, code, path, **kwargs):
        return cls(code=code, path=path, data=data, **kwargs)
