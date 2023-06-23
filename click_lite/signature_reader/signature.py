import inspect
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Optional

import docstring_parser
from docstring_parser import parse

from click_lite.exceptions import InvalidParameterException, InvalidSignatureException


@dataclass(slots=True)
class ParameterDescription:
    """
    A class representation of a parameter description in the docstring of a callable.
        Args:
            name: The name of the parameter
            description: The description of the parameter.
    """

    name: str = ""
    description: Optional[str] = None

    @classmethod
    def from_docstring_parsed_parameter(cls, parameter: docstring_parser.DocstringParam) -> "ParameterDescription":
        """
        A builder method to create a `ParameterDescription` object from a `docstring_parser.DocstringParam` object
        Args:
            parameter: The `docstring_parser.DocstringParam` from a parsed docstring

        Returns:
            A new `ParameterDescription` object
        """
        return cls(name=parameter.arg_name, description=parameter.description)


@dataclass(slots=True)
class Description:
    """
    A class representation of a docstring of a callable.
        Args:
            short_description: The first line of a docstring
            long_description: The second to n number of lines in a docstring
            parameter_descriptions: A sequence of `ParameterDescription` objects for each parameter mentioned in a docstring.
            raises_description: TBD
            result_description: TBD
    """

    short_description: Optional[str] = None
    long_description: Optional[str] = None
    parameter_descriptions: Sequence[ParameterDescription] = field(default_factory=list)
    raises_description: Optional[str] = None
    result_description: Optional[str] = None

    @classmethod
    def from_docstring_parsed(cls, parsed: docstring_parser.Docstring) -> "Description":
        """
        A builder method to create a `Description` object from a `docstring_parser.Docstring` object
        Args:
            parsed: A reference to the `docstring_parser.Docstring` object
        Returns:
            A new `Description` object
        """
        parameter_descriptions = [
            ParameterDescription.from_docstring_parsed_parameter(parameter=parameter) for parameter in parsed.params
        ]
        return cls(
            short_description=cls._convert_literal_none_to_none(parsed.short_description),
            long_description=parsed.long_description,
            parameter_descriptions=parameter_descriptions,
            raises_description=None,
            result_description=None,
        )

    @staticmethod
    def _convert_literal_none_to_none(value: Optional[str]) -> Optional[str]:
        if type(value) is str:
            return None if value.lower() == "none" else value
        return value


class DocStringParser:
    """
    An interface to parse the docstring of a callable method and create a `Description` object from the docstring.
    """

    @staticmethod
    def parse(method: Callable) -> Description:
        """
        The parse method uses the `docstring_parser.parse` method to parse the docstring and generate a `Description` object.
        Args:
            method: The callable object which has the docstring you need parsed

        Returns:
            The `Description` objection
        """
        parsed = parse(str(method.__doc__))
        description = Description.from_docstring_parsed(parsed=parsed)
        return description


@dataclass(slots=True)
class Parameter:
    """
    An abstraction over the inspect.Parameter class. This class also meant to store a description parsed from the
    docstring along with the usual name, data type etc.
        Args:
        name: The name of the argument
        data_type: The data type of the argument. This is retrieved from the type hint used in the function definition.
        is_required: Weather the parameter is required or optional. If a default value is provided, its considered optional.
        default: The default value for this
        description: The description for the parameter, retrieved from the docstring.
    """

    name: str
    data_type: Any
    is_required: bool = False
    default: Optional[Any] = None
    description: str = ""

    @classmethod
    def from_inspect_parameter(cls, parameter: inspect.Parameter) -> "Parameter":
        """
        An interface to creating a click_lite.Parameter object from an inspect.Parameter object.

        Args:
            parameter: The inspect.Parameter object.

        Raises:
            InvalidParameterException: If the input parameter to the function is not of type inspect.Parameter

        Returns:
            parameter: The click_lite.Parameter object.
        """
        if type(parameter) is not inspect.Parameter:
            raise InvalidParameterException(
                f"Expected type for `parameter` is `inspect.Parameter` but got `{type(parameter)}`"
            )
        click_lite_parameter = cls(
            name=parameter.name,
            data_type=parameter.annotation,
            default=parameter.default if parameter.default is not inspect._empty else None,
            is_required=parameter.default is inspect._empty,
        )
        return click_lite_parameter


class Signature:
    """
    An abstraction over the inspect.Signature class. This class also provides some utility function to check if the
    signature of a callable has a particular parameter.
    """

    def __init__(self) -> None:
        self._parameters: dict = {}
        self._description: Optional[Description] = None

    def add_parameter(self, parameter: Parameter) -> "Signature":
        """
        A utility function that adds a parameter to the signature

        Args:
            parameter: The parameter object that is to be added to the signature.

        Returns:
            signature: The reference to the signature object itself, so you can chain adding parameters.
        """
        if type(parameter) is not Parameter:
            raise TypeError("Only accept values of type `Parameter`")
        self[parameter.name] = parameter
        return self

    def __getitem__(self, item: str) -> Any:
        return self._parameters[item]

    def __setitem__(self, key: str, value: Parameter) -> Any:
        if type(value) is not Parameter:
            raise TypeError("Only accept values of type `Parameter`")
        self._parameters[key] = value

    @property
    def parameters(self) -> Sequence[Parameter]:
        return list(self._parameters.values())

    @property
    def description(self) -> Optional[Description]:
        return self._description

    def has_parameter(self, parameter_name: str) -> bool:
        """
        Checks if the signature has a parameter with the provided name

        Args:
            parameter_name: The name of the parameter.

        Returns:
            has_parameter: A bool representing if the parameter is present in the signature
        """
        return self.get_parameter(parameter_name=parameter_name) is not None

    def get_parameter(self, parameter_name: str) -> Optional[Parameter]:
        """
        Returns the reference to the parameter with the name provided.

        Args:
            parameter_name: The name of the parameter.

        Returns:
            parameter: A reference to the parameter if it exists, `None` otherwise
        """
        return self._parameters.get(parameter_name)

    @classmethod
    def from_inspect_signature(cls, signature: inspect.Signature) -> "Signature":
        """
        An interface to creating a click_lite.Signature object from an inspect.Signature object.

        Args:
            signature: The inspect.Signature object.

        Raises:
            InvalidSignatureException: If the input signature to the function is not of type inspect.Signature

        Returns:
            signature: The click_lite.Signature object.
        """
        if type(signature) is not inspect.Signature:
            raise InvalidSignatureException(
                f"Expected type for `signature` is `inspect.Signature` but got `{type(signature)}`"
            )
        signature_reference = cls()
        for _parameter_name, parameter in signature.parameters.items():
            signature_reference.add_parameter(parameter=Parameter.from_inspect_parameter(parameter=parameter))
        return signature_reference

    def add_description(self, description: Description) -> "Signature":
        self._description = description
        for parameter_description in description.parameter_descriptions:
            self[parameter_description.name].description = parameter_description.description
        return self


class SignatureReader:
    """
    The `SignatureReader` class provides an easy interface to read the signature of a `callable` object.
    """

    def __init__(self, custom_docstring_parser: Optional[DocStringParser] = None):
        self.custom_docstring_parser = custom_docstring_parser if custom_docstring_parser else DocStringParser()

    def read(self, method: Callable) -> Signature:
        """
        Returns a reference of `click_lite.Signature` object for the signature of the method.

        Args:
            method: A reference to the callable to which you need the signature to

        Returns:
            signature: The click_lite.Signature  reference
        """
        if not callable(method):
            raise TypeError(
                f"The object {method.__name__} is not callable, the SignatureReader only supports reading signature of"
                " callables."
            )
        inspect_signature = inspect.signature(method)
        signature = Signature.from_inspect_signature(signature=inspect_signature)
        description = self.custom_docstring_parser.parse(method=method)
        signature.add_description(description=description)
        return signature
