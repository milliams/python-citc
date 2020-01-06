#! /usr/bin/env python

import pathlib
import subprocess
from typing import Iterator, Type


def node_list(slurm_conf: pathlib.Path) -> Iterator[str]:
    """
    Given a config file, gives all the nodes listed within
    """
    with slurm_conf.open() as conf:
        for line in conf:
            if line.startswith("NodeName="):
                nodelist = line.split()[0][9:]
                if "[" in nodelist:
                    # TODO use pyslurm.hostlist().create()/get_list()
                    pass
                yield from nodelist.split(",")


NODE_STATE_FLAGS = {
    "*": "not_responding",
    "~": "power_save",
    "#": "powering_up",
    "%": "powering_down",
    "$": "main_reservation",
    "@": "pending_reboot",
}


class Node:
    def __init__(self):
        pass

    SINFO_FIELDS = [
        "nodelist",
        "statelong",
        "reason",
        "cpus",
        "socketcorethread",
        "memory",
        "features",
        "gres",
        "nodeaddr",
        "timestamp",
    ]

    state: str
    state_flag: str
    features: dict

    @classmethod
    def from_name(cls: Type["Node"], nodename: str) -> "Node":
        field_width = 40
        sinfo_format = ",".join(f"{f}:{field_width}" for f in cls.SINFO_FIELDS)
        out = subprocess.run(
            ["sinfo", "--nodes", nodename, "--Format", sinfo_format, "--noheader"]
        ).stdout.decode()
        fields = [
            out[start : start + field_width].strip()
            for start in range(0, len(out), field_width)
        ]
        data = {k: v for k, v in zip(cls.SINFO_FIELDS, fields)}
        n = cls()

        if data["statelong"][-1] in NODE_STATE_FLAGS:
            n.state = data["statelong"][:-1]
            n.state_flag = data["statelong"][-1]
        else:
            n.state = data["statelong"]

        n.features = parse_features(data["features"])

        return n


def parse_features(feature_string: str) -> dict:
    feature_dict = {}
    for pair in feature_string.split(","):
        k, v = pair.split("=")
        feature_dict[k] = v
    return feature_dict
