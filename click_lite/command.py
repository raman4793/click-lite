import sys
from typing import Any

from .argument_parser import ArgumentParser
from .signature_reader import SignatureReader


class CommandStore:
    def __init__(self) -> None:
        self.store: dict[str, Any] = {}

    def add(self, name: str, reference: Any) -> None:
        """
        Add a command to the command store
        Args:
            name: The name of the command.
            reference: The reference of the command.

        Returns:
        """

        self.store[name] = reference

    def get_command(self, command_name: str, subcommand_name: str | None = None) -> Any:
        """
        Returns the reference of the command.

        Args:
            command_name:
            subcommand_name:

        Returns:

        """
        command = self.store[command_name]
        if subcommand_name is not None:
            command = command.__getattribute__(subcommand_name)
        return command


class CommandNameParser:
    @staticmethod
    def parse() -> tuple[str, str | None]:
        """

        Returns:

        """
        # TODO : The logic here is flawed.
        args = sys.argv[1:]
        commands = tuple(filter(lambda x: not x.startswith("--"), args[:2]))
        if len(commands) == 0:
            raise ValueError("No command specified")
        elif len(commands) == 1:
            commands = commands[0], None
            sys.argv.pop(1)
        elif len(commands) == 2:
            sys.argv.pop(1)
            sys.argv.pop(1)
        else:
            raise ValueError("Too many commands specified")
        commands = commands if len(commands) == 2 else (commands[0], "")
        return commands


class Command:
    """
    The interface used to decorate methods/classes, which in-turn makes them be invoked using CLI
    """

    def __init__(
        self,
        command_store: CommandStore | None = None,
        command_name_parser: CommandNameParser | None = None,
        argument_parser: ArgumentParser | None = None,
        signature_reader: SignatureReader | None = None,
    ) -> None:
        """
        Args:
            command_store: A key value pair to keep track of all the decorated methods/classes.
            command_name_parser: An upper layer component to get which function is being invoked from CLI
            argument_parser: An object of the click_lite.ArgumentParser object.
                            It's meant as a wrapper over the argparse.ArgumentParser class.
            signature_reader: An instance of the `click_lite.SignatureReader` class.
        """
        self.command_store = command_store if command_store else CommandStore()
        self.command_name_parser = command_name_parser if command_name_parser else CommandNameParser()
        self.argument_parser = argument_parser if argument_parser else ArgumentParser()
        self.signature_reader = signature_reader if signature_reader else SignatureReader()

    def execute(self) -> None:
        command_name, subcommand_name = self.command_name_parser.parse()
        command_reference = self.command_store.get_command(command_name, subcommand_name)
        signature = self.signature_reader.read(command_reference)
        arguments = self.argument_parser.parse(signature)
        command_reference(**arguments)

    def __call__(self, reference: Any) -> None:
        self.command_store.add(name=self._command_name_from_reference(reference), reference=reference)

    @staticmethod
    def _command_name_from_reference(reference: Any) -> str:
        return str(reference.__name__.lower())
