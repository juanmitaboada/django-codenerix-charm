#!/usr/bin/env python3
# Copyright 2023 Juanmi Taboada
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

https://discourse.charmhub.io/t/4208
"""

import os
import logging
import types
import functools
import shutil
from contextlib import contextmanager

from ops.charm import CharmBase
from ops.main import main
from ops.model import (
    ActiveStatus,
    # BlockedStatus,
    # WaitingStatus,
    MaintenanceStatus,
)

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)

# Icons
EMOJI_CORE_HOOK_EVENT = "\U0001F4CC"
EMOJI_CHECK_MARK_BUTTON = "\U00002705"
EMOJI_CROSS_MARK_BUTTON = "\U0000274E"
EMOJI_COMPUTER_DISK = "\U0001F4BD"

EMOJI_CORE_HOOK_EVENT = "\U0001F4CC"  # 📌
EMOJI_CHECK_MARK_BUTTON = "\U00002705"  # ✅
EMOJI_CROSS_MARK_BUTTON = "\U0000274E"  # ❎
EMOJI_COMPUTER_DISK = "\U0001F4BD"  # 💽
EMOJI_ROCKET = "\U0001F680"  # 🚀


@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


@contextmanager
def virtualenv(path="/code"):
    with cd(path):
        activate_this_file = f"{path}/venv/bin/activate_this.py"
        exec(
            compile(
                open(activate_this_file, "rb").read(),
                activate_this_file,
                "exec",
            ),
            dict(__file__=activate_this_file),
        )
        yield


def logdecorate(prefix):
    """
    Adds output with a prefix string to any function.
     # W: blank line contains whitespace
    """

    def decorate(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            logger.debug(
                f"{prefix} {f.__name__} Args: {args} Kwargs: {kwargs}"
            )
            cr = f(*args, **kwargs)
            logger.debug(f"{prefix} {f.__name__} Result: {cr}")
            return cr

        return wrapper

    return decorate


class CharmAutoBase(CharmBase):
    """
    Auto link local _on_ methods with their twin observer
    """

    def __init__(self, *args, **kwargs):

        # Initialize like always
        super().__init__(*args)

        # Check for methods declared in the charm by the user
        for name, item in DjangoCodenerixCharm.__dict__.items():
            if isinstance(item, types.FunctionType) and (
                name.startswith("_on_")
            ):
                base_method = getattr(self.on, name[4:])
                local_method = getattr(self, name)
                self.framework.observe(base_method, local_method)


class DjangoCodenerixCharm(CharmAutoBase):
    """Charm the service."""

    URL = "https://github.com/codenerix/codenerix-erp"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @logdecorate(EMOJI_COMPUTER_DISK)
    def _on_media_storage_attached(self, event):
        # The event carries information of the storage for the unit
        logger.debug(
            f"MEDIA: Mounted {event.storage.location} "
            f"with {event.storage.name}:{event.storage.index}"
        )

        self.unit.status = ActiveStatus(
            f"{EMOJI_CHECK_MARK_BUTTON} "
            f"MEDIA: Attached {event.storage.name}/"
            f"{event.storage.index}"
            f" at {event.storage.location} bind mount."
        )

    @logdecorate(EMOJI_CORE_HOOK_EVENT)
    def _on_install(self, event):

        logger.info("INSTALL: git")
        self.unit.status = MaintenanceStatus("Git")

        # Install basic dependencies
        os.system("apt -y install git")

        logger.info("INSTALL: Clonning Codenerix ERP")
        self.unit.status = MaintenanceStatus("Clonning Codenerix ERP")

        # Clone ERP
        os.system(f"git clone {self.URL} /erp")

        logger.info("INSTALL: System packages")
        self.unit.status = MaintenanceStatus("System packages")

        # Install system dependencies
        osdeps = [
            "libmariadb-dev",
            "python3",
            "python3-fabric",
            "python3-mysqldb",
            "python3-pip",
            "python3-uwsgidecorators",
            "python3-virtualenv",
            "uwsgi",
            "uwsgi-plugin-python3",
            "uwsgi-extra",
            "uwsgi-plugins-all",
        ]
        os.system("apt -y install {}".format(" ".join(osdeps)))

        logger.info("INSTALL: Python packages")
        self.unit.status = MaintenanceStatus("Python packages")

        # Install python dependencies
        os.system("virtualenv -p python3 /code/venv")
        with virtualenv():
            os.system("pip install --upgrade pip")
            os.system("pip install -r /erp/erp/requirements.txt")

        logger.info("INSTALL: Copy ERP")
        self.unit.status = MaintenanceStatus("Copy ERP")

        # Copy usefull code
        shutil.move("/erp/erp/start.sh", "/code")
        shutil.move("/erp/erp/erp", "/code")
        shutil.move("/erp/erp/manage.py", "/code")
        shutil.move("/erp/erp/conf", "/code")
        os.mkdir("/code/static")

        logger.info("Ready (installed)")
        self.unit.status = MaintenanceStatus("Ready (installed)")

    @logdecorate(EMOJI_CHECK_MARK_BUTTON)
    def _on_config_changed(self, event):
        """Handle changed configuration.
        Learn more about config at https://juju.is/docs/sdk/config
        """

        logger.info("CONFIG CHANGED")
        self.unit.status = MaintenanceStatus("Config changed")

        with virtualenv():
            os.system("./manage.py migrate")
            os.system("./manage.py touch")

        logger.info("Ready (config changed")
        self.unit.status = MaintenanceStatus("Ready (config changed)")

    @logdecorate(EMOJI_ROCKET)
    def _on_start(self, event):
        logger.info("START")
        self.unit.status = ActiveStatus("Start")

    @logdecorate(EMOJI_COMPUTER_DISK)
    def _on_media_storage_detaching(self, event):
        # os.system('systemctl disable var-log-mylogs.mount --now')
        # os.remove('/etc/systemd/system/var-log-mylogs.mount')
        self.unit.status = ActiveStatus(
            f"{EMOJI_CROSS_MARK_BUTTON} Detached MEDIA storage."
        )


if __name__ == "__main__":  # pragma: nocover
    main(DjangoCodenerixCharm)
