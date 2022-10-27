from cProfile import label
from cmath import cos
import matplotlib.pyplot as plt
import numpy as np
import os
import yaml

parameters = {
    'axes.labelsize': 32,
    'xtick.labelsize': 32,
    'ytick.labelsize': 32,
    'legend.fontsize': 28,
    'figure.figsize': [15, 10],
    'font.sans-serif': 'Arial'
}
plt.rcParams.update(parameters)


def plot_cpu(fig_name, fun_1, fun_2, fun_3):
    fig, ax = plt.subplots()

    ax.set_xticks(np.arange(0, fun_1.size, 8))
    ax.set_xlabel('Config Steps')
    ax.set_ylabel('Allocated CPU')

    lower = min(np.min(fun_1), np.min(fun_2), np.min(fun_3))
    upper = max(np.max(fun_1), np.max(fun_2), np.max(fun_3))

    ax.set_ylim(lower//10*10, upper+1)

    ax.plot(np.arange(fun_1.size), fun_1,
            linewidth=9, ms=24, color='orange')
    ax.plot(np.arange(fun_2.size), fun_2,
            linewidth=9, ms=24, color='green')
    ax.plot(np.arange(fun_3.size), fun_3,
            linewidth=9, ms=24, color='purple')

    ax.legend(['func 1', 'func 2', 'func 3'], loc='upper right')

    plt.grid(axis='y')
    if not os.path.exists('plot'):
        os.makedirs('plot')
    plt.savefig(f'plot/{fig_name}.pdf')


def plot_mem(fig_name, fun_1, fun_2, fun_3):
    fig, ax = plt.subplots()

    ax.set_xticks(np.arange(0, fun_1.size, 8))
    ax.set_xlabel('Config Steps')
    ax.set_ylabel('Allocated Memory (MB)')

    lower = min(np.min(fun_1), np.min(fun_2), np.min(fun_3))
    upper = max(np.max(fun_1), np.max(fun_2), np.max(fun_3))

    ax.set_ylim(lower//10*10, (upper//10+1)*10)

    ax.plot(np.arange(fun_1.size), fun_1,
            linewidth=9, ms=24, color='orange')
    ax.plot(np.arange(fun_2.size), fun_2,
            linewidth=9, ms=24, color='green')
    ax.plot(np.arange(fun_3.size), fun_3,
            linewidth=9, ms=24, color='purple')

    ax.legend(['func 1', 'func 2', 'func 3'], loc='upper right')

    plt.grid(axis='y')
    if not os.path.exists('plot'):
        os.makedirs('plot')
    plt.savefig(f'plot/{fig_name}.pdf')


def plot_runtime(fig_name, runtime):
    fig, ax = plt.subplots()

    ax.set_xticks(np.arange(0, runtime.size, 8))
    ax.set_xlabel('Config Steps')
    ax.set_ylabel('Runtime (ms)')
    ax.set_ylim(np.min(runtime)//10*10, (np.max(runtime)//10+1)*10)
    ax.axhline(y=1000, linestyle='dotted', label='SLO',
               linewidth=6, color='#d62728')

    ax.plot(np.arange(runtime.size), runtime,
            linewidth=9, ms=24, color='orange')

    ax.legend(['SLO', 'runtime'], loc='upper right')
	
    plt.grid(axis='y')
    if not os.path.exists('plot'):
        os.makedirs('plot')
    plt.savefig(f'plot/{fig_name}.pdf')


def plot_cost(fig_name, cost):
    fig, ax = plt.subplots()

    ax.set_xticks(np.arange(0, cost.size, 8))
    ax.set_xlabel('Config Steps')
    ax.set_ylabel('Cost')
    ax.set_ylim(np.min(cost)//10*10, (np.max(cost)//10+1)*10)

    ax.plot(np.arange(cost.size), cost,
            linewidth=9, ms=24, color='orange')

    ax.legend(['cost'], loc='upper right')

    plt.grid(axis='y')
    if not os.path.exists('plot'):
        os.makedirs('plot')
    plt.savefig(f'plot/{fig_name}.pdf')


if __name__ == '__main__':
    funcs = ['function-0', 'function-1', 'function-2']
    resource = ['cpu', 'mem']
    data = {'cpu': {}, 'mem': {}}

    for res in resource:
        for func in funcs:
            file_name = f'results/{func}-{res}.yaml'
            data[res][func] = np.loadtxt(file_name)[1:]

    runtime = np.loadtxt('results/runtime.yaml')[1:]
    cost = np.loadtxt('results/cost.yaml')[1:]


    plot_cpu('CPU allocation', data['cpu']['function-0'], data['cpu']
         ['function-1'], data['cpu']['function-2'])
    plot_mem('Memory allocation', data['mem']['function-0'], data['mem']
         ['function-1'], data['mem']['function-2'])
    plot_runtime('Runtime', runtime)
    plot_cost('Cost', cost)