import argparse
import yaml

from docker_container import *


def PQ_optimization(images, slo):

    print("Initializing workflow...\n")
    DAG = Workflow(images, slo)
    print("\nComplete!\n")

    print("Configuration start!\n")
    DAG.min_cost()
    print("\nComplete!")

if __name__ == '__main__':
    # Get configuration
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


    