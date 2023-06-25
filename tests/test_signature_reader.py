import inspect

import pytest

from click_lite.exceptions import InvalidParameterException, InvalidSignatureException
from click_lite.signature_reader.signature import Description, DocStringParser, Parameter, Signature, SignatureReader


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


@pytest.fixture
def sample_click_lite_signature(sample_signature):
    return Signature.from_inspect_signature(sample_signature)


@pytest.fixture
def sample_click_lite_parameter(sample_param):
    return Parameter.from_inspect_parameter(parameter=sample_param)


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


def test_valid_signature_add_parameter(sample_param, sample_click_lite_signature):
    sample_click_lite_signature.add_parameter(parameter=Parameter.from_inspect_parameter(sample_param))
    assert sample_click_lite_signature.has_parameter(parameter_name=sample_param.name)


def test_invalid_signature_add_parameter(sample_click_lite_signature):
    with pytest.raises(TypeError) as er:
        sample_click_lite_signature.add_parameter(parameter=1)
    assert str(er.value).startswith("Only accept values of type `Parameter`")


def test_invalid_signature_set_parameter(sample_click_lite_signature):
    with pytest.raises(TypeError) as er:
        sample_click_lite_signature["test_param"] = 1
    assert str(er.value).startswith("Only accept values of type `Parameter`")


def test_signature_parameters(sample_click_lite_parameter):
    signature = Signature()
    signature.add_parameter(parameter=sample_click_lite_parameter)
    assert len(signature.parameters) == 1
    assert signature.parameters[0] == sample_click_lite_parameter


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


def test_invalid_signature_reader(sample_signature_reader):
    with pytest.raises(TypeError) as er:
        sample_signature_reader.read(1)
    assert str(er.value).startswith(
        "The object int is not callable, the SignatureReader only supports reading signature of callables."
    )


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


def test_valid__convert_literal_none_to_none():
    assert Description._convert_literal_none_to_none("none") is None
    assert Description._convert_literal_none_to_none("None") is None
    assert Description._convert_literal_none_to_none("NONE") is None
    assert Description._convert_literal_none_to_none("null") is None
    assert Description._convert_literal_none_to_none("Null") is None
    assert Description._convert_literal_none_to_none("NULL") is None
    assert Description._convert_literal_none_to_none("1") == "1"
    assert Description._convert_literal_none_to_none(1) == 1
    assert Description._convert_literal_none_to_none(1.1) == 1.1
    assert Description._convert_literal_none_to_none([1.1, 1]) == [1.1, 1]
    assert Description._convert_literal_none_to_none({"a": 1}) == {"a": 1}
