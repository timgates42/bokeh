# -----------------------------------------------------------------------------
# Copyright (c) 2012 - 2022, Anaconda, Inc., and Bokeh Contributors.
# All rights reserved.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import annotations

# Bokeh imports
from .action import FAILED, PASSED, ActionReturn
from .config import Config
from .system import System

__all__ = (
    "publish_conda_package",
    "publish_documentation",
    "publish_npm_package",
    "publish_pip_packages",
    "unpack_deployment_tarball",
)

CLOUDFRONT_ID = "E2OC6Q27H5UQ63"
REGION = "--region us-east-1"

def publish_npm_package(config: Config, system: System) -> ActionReturn:
    tarball = f"bokeh-bokehjs-{config.js_version}.tgz"
    tags = "--tag=dev" if config.prerelease else ""
    try:
        system.cd(f"deployment-{config.version}")
        system.run(f"npm publish --access=public {tags} {tarball}")
        system.cd("..")
        return PASSED("Publish to npmjs.com succeeded")
    except RuntimeError as e:
        return FAILED("Could NOT publish to npmjs.com", details=e.args)


def publish_conda_package(config: Config, system: System) -> ActionReturn:
    version = config.version
    path = f"deployment-{version}/bokeh-{version}-py_0.tar.bz2"
    token = config.secrets["ANACONDA_TOKEN"]
    main_channel = "" if config.prerelease else "-l main"
    try:
        system.run(f"anaconda -t {token} upload -u bokeh {path} {main_channel} -l dev --force --no-progress")
        return PASSED("Publish to anaconda.org succeeded")
    except RuntimeError as e:
        return FAILED("Could NOT publish to anaconda.org", details=e.args)


def publish_documentation(config: Config, system: System) -> ActionReturn:
    version, release_level = config.version, config.release_level
    path = f"deployment-{version}/sphinx/build/html"
    flags = "--acl bucket-owner-full-control --cache-control max-age=31536000,public"
    try:
        if config.prerelease:
            system.run(f"aws s3 sync {path} s3://docs.bokeh.org/en/dev-{release_level}/ {flags} {REGION}")
            system.run(f'aws cloudfront create-invalidation --distribution-id {CLOUDFRONT_ID} --paths "/en/dev-{release_level}*" {REGION}')
        else:
            system.run(f"aws s3 sync {path} s3://docs.bokeh.org/en/latest/ {flags} {REGION}")
            system.run(f"aws s3 sync {path} s3://docs.bokeh.org/en/{version}/ {flags} {REGION}")
            system.run(f'aws cloudfront create-invalidation --distribution-id {CLOUDFRONT_ID} --paths "/en/latest*" "/en/{version}*" {REGION}')
        return PASSED("Publish to documentation site succeeded")
    except RuntimeError as e:
        return FAILED("Could NOT publish to documentation site", details=e.args)


def publish_pip_packages(config: Config, system: System) -> ActionReturn:
    # NOTE: using pep440_version below because sdists already uses this syntax
    # This will eventually be the standard dev/rc version syntax for all packages
    sdist_path = f"deployment-{config.version}/bokeh-{config.pep440_version}.tar.gz"
    wheel_path = f"deployment-{config.version}/bokeh-{config.pep440_version}-py3-none-any.whl"
    try:
        system.run(f"twine upload -u __token__ -p $PYPI_TOKEN {sdist_path} {wheel_path}")
        return PASSED("Publish to pypi.org succeeded")
    except RuntimeError as e:
        return FAILED("Could NOT publish to pypi.org", details=e.args)


def unpack_deployment_tarball(config: Config, system: System) -> ActionReturn:
    try:
        filename = f"deployment-{config.version}.tgz"
        system.run(f"tar xvf {filename}")
        return PASSED(f"Unpacked deployment tarball {filename!r}")
    except RuntimeError as e:
        return FAILED("Could NOT unpack deployment tarball", details=e.args)
