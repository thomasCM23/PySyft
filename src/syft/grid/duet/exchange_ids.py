# stdlib
import json
from pathlib import Path
import tempfile
import time
from typing import Any as TypeAny
from typing import Optional as TypeOptional
from typing import Tuple as TypeTuple

# syft relative
from .bcolors import bcolors


class DuetCredentialExchanger:
    def __init__(self, *args: TypeTuple[TypeAny, ...], **kwargs: TypeAny) -> None:
        pass

    def run(self, *args: TypeTuple[TypeAny, ...], **kwargs: TypeAny) -> TypeAny:
        raise NotImplementedError


class OpenGridTokenManualInputExchanger(DuetCredentialExchanger):
    def __init__(self, credential: str, join: bool = False, **kwargs: TypeAny) -> None:
        self.credential = credential
        self.join = join

    def run(self, *args: TypeTuple[TypeAny, ...], **kwargs: TypeAny) -> str:
        if self.join:
            self._client_exchange(credential=self.credential)
            return str(kwargs["server_id"])
        else:
            return self._server_exchange(credential=self.credential)

    def _server_exchange(self, credential: str) -> str:
        # send Server ID
        print("♫♫♫ > Duet Server ID: " + bcolors.BOLD + credential + bcolors.ENDC)

        print()
        print(
            "♫♫♫ > "
            + bcolors.HEADER
            + "STEP 1:"
            + bcolors.ENDC
            + " Send the following code to your Duet Partner!"
        )
        print("\nimport syft as sy")
        print('duet = sy.duet("' + bcolors.BOLD + credential + bcolors.ENDC + '")')

        # get Client ID
        print(
            "\n♫♫♫ > "
            + bcolors.HEADER
            + "STEP 2:"
            + bcolors.ENDC
            + " Have your duet partner send their Client ID to you and enter it below!"
        )
        while True:
            client_id = input("♫♫♫ > Duet Partner's Client ID: ")  # nosec
            if len(client_id) == 32:
                break
            else:
                print("    > Error: Invalid Client ID. Please try again.")
        print()
        return client_id

    def _client_exchange(self, credential: str) -> None:
        # send client ID
        print(
            "♫♫♫ > "
            + bcolors.HEADER
            + "STEP 1:"
            + bcolors.ENDC
            + " Send the following Duet Client ID to your duet partner!"
        )
        print("♫♫♫ > Duet Client ID: " + bcolors.BOLD + credential + bcolors.ENDC)
        print()
        print("♫♫♫ > ...waiting for partner to connect...")


class OpenGridTokenFileExchanger(DuetCredentialExchanger):
    def __init__(
        self,
        credential: str,
        join: bool = False,
        file_path: TypeOptional[str] = None,
        **kwargs: TypeAny
    ):
        self.credential = credential
        self.join = join
        if file_path is not None:
            self.file_path = file_path
        else:
            self.file_path = OpenGridTokenFileExchanger.get_loopback_path()

    def run(self, *args: TypeTuple[TypeAny, ...], **kwargs: TypeAny) -> str:
        if self.join:
            return self._client_exchange(credential=self.credential)
        else:
            return self._server_exchange(credential=self.credential)

    # for local debugging
    @staticmethod
    def get_loopback_path() -> str:
        loopback_file = "duet_loopback.json"
        return str(Path(tempfile.gettempdir()) / loopback_file)

    def _server_exchange(self, credential: str) -> str:
        print()
        print(
            "♫♫♫ > "
            + bcolors.HEADER
            + "STEP 1:"
            + bcolors.ENDC
            + " Send the following code to your Duet Partner!"
        )
        print("\nimport syft as sy")
        print("duet = sy.join_duet(loopback=True)")
        print()

        # send Server ID
        loopback_config = {}
        loopback_config["server_id"] = credential
        with open(self.file_path, "w") as f:
            f.write(json.dumps(loopback_config))

        # get Client ID
        client_id = ""
        while client_id == "":
            try:
                with open(self.file_path, "r") as f:
                    loopback_config = json.loads(f.read())
                    if "client_id" in loopback_config:
                        client_id = str(loopback_config["client_id"])
                    else:
                        time.sleep(0.01)
            except Exception as e:
                print(e)
                break
        return client_id

    def _client_exchange(self, credential: str) -> str:
        loopback_config = {}
        server_id = ""
        while server_id == "":
            try:
                with open(self.file_path, "r") as f:
                    loopback_config = json.loads(f.read())
                    # only continue once the server has overwritten the file
                    # with only its new server_id
                    if (
                        "server_id" in loopback_config
                        and "client_id" not in loopback_config
                    ):
                        server_id = str(loopback_config["server_id"])
                    else:
                        time.sleep(0.01)
            except Exception as e:
                print(e)
                break

        loopback_config["client_id"] = credential

        with open(self.file_path, "w") as f:
            f.write(json.dumps(loopback_config))

        return server_id