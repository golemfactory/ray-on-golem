from unittest import mock

import factory


class ResourceFactory(factory.Factory):
    node = factory.LazyFunction(mock.AsyncMock)
    id_ = factory.Faker("pystr")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        def _mock_call(cls, *args, **_kwargs):
            obj = cls.__new__(cls)
            obj.__init__(*args, **kwargs)
            return obj

        with mock.patch("golem.resources.base.ResourceMeta.__call__", new=_mock_call):
            return model_class(*args, **kwargs)
