# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2015 Gluu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import json
import os.path
import tempfile
import shutil

import docker.errors
import requests
from docker import Client

from api.log import create_file_logger


class DockerHelper(object):
    def __init__(self, logger=None):
        self.logger = logger or create_file_logger()
        self.docker = Client(base_url="unix://var/run/docker.sock")

    def image_exists(self, name):
        """Checks whether a docker image exists.

        :param name: Image name
        :returns: ``True`` if image exists, otherwise ``False``
        """
        images = self.docker.images(name)
        return True if images else False

    def build_image(self, path, tag):
        """Builds a docker image.

        :param path: Path to a directory where ``Dockerfile`` is located.
        :param tag: Desired tag name.
        :returns: ``True`` if image successfully built, otherwise ``False``
        """
        resp = self.docker.build(path, tag=tag, quiet=True,
                                 rm=True, forcerm=True, pull=False)

        output = ""
        while True:
            try:
                output = resp.next()
                self.logger.info(output)
            except StopIteration:
                break

        result = json.loads(output)
        if "errorDetail" in result:
            return False
        return True

    def run_container(self, name, image):
        """Runs a docker container in detached mode.

        This is a two-steps operation:

        1. Creates container
        2. Starts container

        :param name: Desired container name.
        :param image: Existing image name.
        :returns: A string of container ID in long format if container
                is running successfully, otherwise an empty string.
        """
        container_id = ""

        try:
            self.logger.info("creating container named {!r}".format(name))
            container = self.docker.create_container(image=image, name=name,
                                                     detach=True, command=[])
            container_id = container["Id"]
            self.logger.info("container named {!r} has been created".format(name))
        except docker.errors.APIError as exc:
            err_code = exc.response.status_code
            if err_code == 409:
                self.logger.warn("container named {!r} is exist".format(name))
            elif err_code == 404:
                self.logger.warn("container named {!r} does not exist".format(name))

        if container_id:
            self.docker.start(container=container_id, publish_all_ports=True)
            self.logger.info("container named {!r} with ID {!r} "
                             "has been started".format(name, container_id))
        return container_id

    def get_remote_files(self, *files):
        """Retrieves files from remote paths.

        All retrieved files will be stored under a same temporary directory.

        :param files: List of files.
        :returns: Absolute path to temporary directory where all files
                were downloaded to.
        """
        local_dir = tempfile.mkdtemp()

        for file_ in files:
            local_path = os.path.join(local_dir, os.path.basename(file_))
            self.logger.info("downloading {!r}".format(file_))

            resp = requests.get(file_)
            if resp.status_code == 200:
                with open(local_path, "w") as fp:
                    fp.write(resp.text)
        return local_dir

    def _build_saltminion(self, salt_master_ipaddr):
        """Builds saltminion image.

        :param salt_master_ipaddr: IP address of salt-master.
        :returns: ``True`` if image successfully built, otherwise ``False``
        """
        build_succeed = True

        if not self.image_exists("saltminion"):
            self.logger.info("building saltminion image")
            # There must be a better way than to hard code every file one by one
            minion_file = "https://raw.githubusercontent.com/GluuFederation" \
                          "/gluu-docker/master/ubuntu/14.04/saltminion/minion"
            minion_file_stub = "https://raw.githubusercontent.com/GluuFederation" \
                          "/gluu-docker/master/ubuntu/14.04/saltminion/minion-stub"
            docker_entrypoint = "https://raw.githubusercontent.com/GluuFederation" \
                          "/gluu-docker/master/ubuntu/14.04/saltminion/docker-entrypoint.sh"
            dockerfile = "https://raw.githubusercontent.com/GluuFederation" \
                         "/gluu-docker/master/ubuntu/14.04/saltminion/Dockerfile"
            files = [minion_file, minion_file_stub, docker_entrypoint, dockerfile]
            build_dir = self.get_remote_files(*files)
            saved_minion = os.path.join(build_dir, os.path.basename(minion_file))

            # There's a line in minion file that says ``master: xxx.xxx.xxx.xxx``
            # technically we need to replace the ``xxx.xxx.xxx.xxx`` part
            # with salt-master IP address, so any salt-minion can connect to it
            # properly.
            content = ""
            with open(saved_minion, "r") as fp:
                content = fp.read()

            new_content = content.format(SALT_MASTER_IPADDR=salt_master_ipaddr)
            with open(saved_minion, "w") as fp:
                fp.write(new_content)

            build_succeed = self.build_image(build_dir, "saltminion")
            shutil.rmtree(build_dir)
        return build_succeed

    def setup_container(self, name, image, dockerfile, salt_master_ipaddr):
        """Builds and runs a container.

        :param name: Container name.
        :param image: Image name.
        :param dockerfile: Path to remote Dockerfile. Used to build the image
                        if image is not exist.
        :returns: Container ID in long format if container running successfully,
                otherwise an empty string.
        """
        if not self._build_saltminion(salt_master_ipaddr):
            return ""

        # a flag to determine whether build image process is succeed
        build_succeed = True

        if not self.image_exists(image):
            build_dir = self.get_remote_files(dockerfile)
            build_succeed = self.build_image(build_dir, image)
            shutil.rmtree(build_dir)

        if build_succeed:
            return self.run_container(name, image)
        return ""

    def get_container_ip(self, container_id):
        """Gets container IP.

        :param container_id: Container ID; ideally the short format.
        :returns: Container's IP address.
        """
        return self.docker.inspect_container(container_id)["NetworkSettings"]["IPAddress"]

    def remove_container(self, container_id):
        """Removes container.
        """
        try:
            return self.docker.remove_container(container_id, force=True)
        except docker.errors.APIError as exc:
            err_code = exc.response.status_code
            if err_code == 404:
                self.logger.warn("container {!r} does not exist".format(container_id))
