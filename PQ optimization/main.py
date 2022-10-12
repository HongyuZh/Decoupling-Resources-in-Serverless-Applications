import argparse

import yaml

from docker_container import *


def PQ_optimization(images, slo):

    print("Initializing workflow...")
    DAG = Workflow(images, slo)
    print("Complete!")

    print("Configuration start!")
    while DAG.get_runtime() < slo:
        DAG.one_step_operator()
    print("Complete!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='config file', required=True)

    args = parser.parse_args()

    config_file = args.config
    with open(config_file, 'r', encoding='utf-8') as f:
        cfgs = yaml.safe_load(f)

    slo = cfgs['slo']

    image_names = []
    for ele in cfgs['images']:
        image_names.append(f'{ele["name"]}:{ele["tag"]}')

    PQ_optimization(image_names, slo)


    