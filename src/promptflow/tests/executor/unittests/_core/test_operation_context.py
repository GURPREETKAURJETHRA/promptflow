import threading

import pytest

from promptflow._version import VERSION
from promptflow.contracts.run_mode import RunMode
from promptflow.tracing._operation_context import OperationContext
from promptflow.tracing._version import VERSION as TRACING_VERSION


def set_run_mode(context: OperationContext, run_mode: RunMode):
    """This method simulates the runtime.execute_request()

    It is aimed to set the run_mode into operation context.
    """
    context.run_mode = run_mode.name if run_mode is not None else ""


@pytest.mark.unittest
class TestOperationContext:
    def test_get_user_agent(self):
        OperationContext.get_instance().append_user_agent(f"promptflow/{VERSION}")
        operation_context = OperationContext.get_instance()
        assert operation_context.get_user_agent() == f"promptflow/{VERSION} promptflow-tracing/{TRACING_VERSION}"

        operation_context.user_agent = "test_agent/0.0.2"
        assert operation_context.get_user_agent() == f"test_agent/0.0.2 promptflow-tracing/{TRACING_VERSION}"

    @pytest.mark.parametrize(
        "run_mode, expected",
        [
            (RunMode.Test, "Test"),
            (RunMode.SingleNode, "SingleNode"),
            (RunMode.Batch, "Batch"),
        ],
    )
    def test_run_mode(self, run_mode, expected):
        context = OperationContext()
        set_run_mode(context, run_mode)
        assert context.run_mode == expected

    def test_context_dict(self):
        context = OperationContext()

        context.run_mode = "Flow"
        context.user_agent = "test_agent/0.0.2"
        context.none_value = None

        context_dict = context.get_context_dict()

        assert context_dict["run_mode"] == "Flow"
        assert context_dict["user_agent"] == "test_agent/0.0.2"
        assert context_dict["none_value"] is None

    def test_setattr(self):
        context = OperationContext()

        context.run_mode = "Flow"
        assert context["run_mode"] == "Flow"

    def test_setattr_non_primitive(self):
        # Test set non-primitive type
        context = OperationContext()
        context.foo = [1, 2, 3]

        assert [1, 2, 3] == context.foo

    def test_getattr(self):
        context = OperationContext()

        context["run_mode"] = "Flow"
        assert context.run_mode == "Flow"

    def test_getattr_missing(self):
        context = OperationContext()

        with pytest.raises(AttributeError):
            context.foo

    def test_delattr(self):
        # test that delattr works as expected
        context = OperationContext()
        context.foo = "bar"
        del context.foo
        assert "foo" not in context

        # test that delattr raises AttributeError for non-existent name
        with pytest.raises(AttributeError):
            del context.baz

    def test_append_user_agent(self):
        context = OperationContext()
        user_agent = " " + context.user_agent if "user_agent" in context else ""

        context.append_user_agent("test_agent/0.0.2")
        assert context.user_agent == "test_agent/0.0.2" + user_agent

        context.append_user_agent("test_agent/0.0.3")
        assert context.user_agent == "test_agent/0.0.2 test_agent/0.0.3" + user_agent

    def test_get_instance(self):
        context1 = OperationContext.get_instance()
        context2 = OperationContext.get_instance()
        assert context1 is context2

    def test_different_thread_have_different_instance(self):
        # create a list to store the OperationContext instances from each thread
        instances = []

        # define a function that gets the OperationContext instance and appends it to the list
        def get_instance():
            instance = OperationContext.get_instance()
            instances.append(instance)

        # create two threads and run the function in each thread
        thread1 = threading.Thread(target=get_instance)
        thread2 = threading.Thread(target=get_instance)
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        # assert that the list has two elements and they are different objects
        assert len(instances) == 2
        assert instances[0] is not instances[1]
