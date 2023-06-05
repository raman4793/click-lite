import inspect

import pytest

from click_lite.exceptions import InvalidParameterException, InvalidSignatureException
from click_lite.signature_reader import Description, DocStringParser, Parameter, Signature, SignatureReader


@pytest.fixture
def sample_param():
    parameter = inspect.Parameter(name="a", default=1, annotation=int, kind=inspect.Parameter.POSITIONAL_OR_KEYWORD)
    return parameter


@pytest.fixture
def sample_signature(sample_param):
    signature = inspect.Signature(parameters=[sample_param])
    return signature


@pytest.fixture
def sample_signature_reader():
    return SignatureReader()


def foo(a: int, b: int = 5) -> int:
    """
    A sample function to test signature reader and for the sake of functionality adding two integers.
    Adding more description to observe behavior.
    Adding more description lines.
    Args:
        a: The first integer
        b: The second integer

    Returns:
        The sum of a & b.
    """
    result = a + b
    return result


def test_valid_parameter(sample_param):
    parameter = Parameter.from_inspect_parameter(parameter=sample_param)
    assert parameter.name == sample_param.name
    assert parameter.default == sample_param.default
    assert parameter.data_type == sample_param.annotation


def test_invalid_parameter():
    with pytest.raises(InvalidParameterException) as er:
        Parameter.from_inspect_parameter(parameter=1)
    assert str(er.value).startswith("Expected type for `parameter` is `inspect.Parameter` but got")


def test_invalid_signature():
    with pytest.raises(InvalidSignatureException) as er:
        Signature.from_inspect_signature(signature=1)
    assert str(er.value).startswith("Expected type for `signature` is `inspect.Signature` but got")


def test_valid_signature(sample_signature, sample_param):
    signature = Signature.from_inspect_signature(signature=sample_signature)
    assert signature.has_parameter(parameter_name=sample_param.name)
    parameter = signature.get_parameter(parameter_name=sample_param.name)
    assert parameter.name == sample_param.name
    assert parameter.default == sample_param.default
    assert parameter.data_type == sample_param.annotation


def test_valid_signature_add_parameter(sample_param):
    signature = Signature()
    signature.add_parameter(parameter=Parameter.from_inspect_parameter(sample_param))
    assert signature.has_parameter(parameter_name=sample_param.name)


def test_invalid_signature_add_parameter():
    signature = Signature()
    with pytest.raises(TypeError) as er:
        signature.add_parameter(parameter=1)
    assert str(er.value).startswith("Only accept values of type `Parameter`")


def test_docstring_parse():
    result = DocStringParser.parse(foo)
    assert type(result) is Description


def test_has_parameter(sample_signature, sample_param):
    signature = Signature.from_inspect_signature(signature=sample_signature)
    assert signature.has_parameter(parameter_name=sample_param.name)
    assert not signature.has_parameter(parameter_name="test")


def test_get_parameter(sample_signature, sample_param):
    signature = Signature.from_inspect_signature(signature=sample_signature)
    assert signature.get_parameter(parameter_name=sample_param.name) is not None
    assert signature.get_parameter(parameter_name="test") is None


def test_signature_reader(sample_signature_reader):
    signature = sample_signature_reader.read(foo)
    expected_signature = inspect.signature(foo)
    for _, parameter in expected_signature.parameters.items():
        assert signature.has_parameter(parameter_name=parameter.name)
    description = signature._description
    assert description is not None
    assert (
        description.short_description
        == "A sample function to test signature reader and for the sake of functionality adding two integers."
    )
    assert (
        description.long_description == "Adding more description to observe behavior.\nAdding more description lines."
    )
    assert len(description.parameter_descriptions) == 2
    assert description.parameter_descriptions[0].description == "The first integer"
    assert description.parameter_descriptions[0].name == "a"
    assert description.parameter_descriptions[1].description == "The second integer"
    assert description.parameter_descriptions[1].name == "b"


def test_description_parser():
    description = DocStringParser.parse(method=foo)
    assert (
        description.short_description
        == "A sample function to test signature reader and for the sake of functionality adding two integers."
    )
    assert (
        description.long_description == "Adding more description to observe behavior.\nAdding more description lines."
    )
    assert len(description.parameter_descriptions) == 2
    assert description.parameter_descriptions[0].description == "The first integer"
    assert description.parameter_descriptions[0].name == "a"
    assert description.parameter_descriptions[1].description == "The second integer"
    assert description.parameter_descriptions[1].name == "b"


def test_invalid_description_parser():
    def bar(a, b):
        return a + b

    description = DocStringParser.parse(method=bar)
    assert description.short_description is None
    assert description.long_description is None
    assert len(description.parameter_descriptions) == 0
