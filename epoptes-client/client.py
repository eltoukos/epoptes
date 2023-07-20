#!/usr/bin/python3
# This file is part of Epoptes, https://epoptes.org
# Copyright 2023 the Epoptes team, see AUTHORS.
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Epoptes client class.
"""

import os
import socket
import ssl
import subprocess
import sys


def die(msg, code=1):
    """Print msg to stderr and exit."""
    print(msg, file=sys.stderr)
    sys.exit(code)


def require_root():
    """Exit if not root."""
    if os.getuid() != 0:
        die("Root access is required")


def run(cmd, shell=False):
    """Run a command and return its output as text."""
    if type(cmd).__name__ == "str":
        cmd = cmd.split(" ")
    if shell:
        cmd = ["sh", "-c"] + cmd
    return subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].decode().rstrip("\n")


class Client():
    """Epoptes client class."""

    def __init__(self):
        self.server = "server"
        self.port = 789
        self.ssock = None

    def fetch_certificate(self):
        """Save server certificate to /etc/epoptes-new/server.crt"""
        require_root()
        cert = ssl.get_server_certificate((self.server, self.port))
        if not os.path.isdir("/etc/epoptes-new"):
            os.mkdir("/etc/epoptes-new", 0o755)
        with open("/etc/epoptes-new/server.crt", "w", encoding="utf-8") as file:
            file.write(cert)
        print(
            f"Saved {self.server}:{self.port} certificate to /etc/epoptes-new/server.crt")

    def echo(self, msg):
        """Echo the message."""
        print("*", msg)
        self.ssock.sendall(msg + b"\n")

    def connect(self):
        """Connect and do the main loop."""
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.load_verify_locations("/etc/epoptes-new/server.crt")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
            with context.wrap_socket(sock, server_hostname=self.server) as ssock:
                self.ssock = ssock
                ssock.connect((self.server, self.port))
                done_client_functions = False
                data = ssock.recv(1024)
                while data:
                    for line in data.split(b"\n"):
                        if not done_client_functions:
                            if line.startswith(b"echo __delimiter__"):
                                done_client_functions = True
                            else:
                                pass
                        words = line.split(b" ", 1)
                        if words[0] == b"echo":
                            self.echo(words[1])
                        elif words[0] == b"info":
                            self.info()
                        else:
                            print(line)
                    data = ssock.recv(1024)
                print("End of data, closing socket")
                ssock.close()


def main():
    """Usage: epoptes-client [--version]."""
    if len(sys.argv) > 1:
        if sys.argv[1] in ("--version", "-version"):
            version = 0.1
            print(f"epoptes-client {version}")
            sys.exit(0)
        elif sys.argv[1] in ("-c"):
            client = Client()
            client.fetch_certificate()
            sys.exit(0)
    client = Client()
    client.connect()
    input("Press [Enter] to finish")


if __name__ == "__main__":
    main()
