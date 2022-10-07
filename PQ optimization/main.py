from docker_container import *

def PQ_optimization(images:List[str], slo):
    DAG = Workflow(images, slo)
    