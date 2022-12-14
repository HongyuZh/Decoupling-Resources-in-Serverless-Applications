import matplotlib.pyplot as plt
import numpy as np
import os

import argparse
import yaml

parameters = {
    'axes.labelsize': 25,
    'xtick.labelsize': 25,
    'ytick.labelsize': 25,
    'legend.fontsize': 22,
    'figure.figsize': [15, 10],
}
plt.rcParams.update(parameters)
mcolor = ['orange', 'green', 'purple', 'violet',
          'chocolate', 'cyan', 'grey', 'blue']


def plot_cpu(fig_name, cpu_alloction):
    fig, ax = plt.subplots()

    ax.set_xticks(
        np.arange(0, cpu_alloction[0].size-exe_times, (cpu_alloction[0].size-exe_times)//8))
    ax.set_xlabel('Config Steps')
    ax.set_ylabel('Allocated CPU')

    lower = np.min(cpu_alloction[0])
    upper = np.max(cpu_alloction[0])
    for i in range(1, len(cpu_alloction)):
        if np.min(cpu_alloction[i]) < lower:
            lower = np.min(cpu_alloction[i])
        if np.max(cpu_alloction[i]) > upper:
            upper = np.max(cpu_alloction[i])

    ax.set_ylim(lower//10*10, upper+1)

    legends = []
    for i in range(0, len(cpu_alloction)):
        ax.plot(np.arange(cpu_alloction[i].size-exe_times), cpu_alloction[i][0:cpu_alloction[i].size-exe_times],
                linewidth=5, ms=24, color=mcolor[i])
        legends.append(f'func {i+1}')

    ax.legend(legends, loc='upper right')

    plt.grid(axis='y')
    if not os.path.exists('plots'):
        os.makedirs('plots')
    plt.savefig(f'plots/{fig_name}.pdf')


def plot_mem(fig_name, mem_alloction):
    fig, ax = plt.subplots()

    ax.set_xticks(
        np.arange(0, mem_alloction[0].size-exe_times, (mem_alloction[0].size-exe_times)//8))
    ax.set_xlabel('Config Steps')
    ax.set_ylabel('Allocated Memory (MB)')

    lower = np.min(mem_alloction[0])
    upper = np.max(mem_alloction[0])
    for i in range(1, len(mem_alloction)):
        if np.min(mem_alloction[i]) < lower:
            lower = np.min(mem_alloction[i])
        if np.max(mem_alloction[i]) > upper:
            upper = np.max(mem_alloction[i])

    ax.set_ylim((lower//10-1)*10, (upper//20+2)*20)

    legends = []
    for i in range(0, len(mem_alloction)):
        ax.plot(np.arange(mem_alloction[i].size-exe_times), mem_alloction[i][0:cpu_alloction[i].size-exe_times],
                linewidth=5, ms=24, color=mcolor[i])
        legends.append(f'func {i+1}')

    ax.legend(legends, loc='upper right')

    plt.grid(axis='y')
    if not os.path.exists('plots'):
        os.makedirs('plots')
    plt.savefig(f'plots/{fig_name}.pdf')


def plot_runtime_and_cost(fig_name, runtime, cost, slo):
    fig, ax1 = plt.subplots()

    ax1.set_xticks(np.arange(0, runtime.size, runtime.size//8))
    ax1.set_xlabel('Steps')
    ax1.set_ylabel('Runtime (ms)')
    ax1.set_ylim((np.min(runtime)//100-6)*100, (np.max(runtime)//100+6)*100)
    ax1.axvline(x=runtime.size-exe_times-1, linestyle='dashed',
                label='completed', linewidth=3, color='#d62728')
    ax1.axhline(y=slo, linestyle='dotted', label='SLO',
                linewidth=4, color='#d62728')

    ax1.plot(np.arange(runtime.size-exe_times), runtime[0:runtime.size-exe_times],
             linewidth=5, ms=24, color='gold')
    ax1.plot(np.arange(runtime.size-exe_times-1, runtime.size), runtime[runtime.size-exe_times-1:runtime.size],
             linewidth=5, ms=24, color='orange')

    ax1.legend(['slo', 'cfg', 'cfg runtime',
               'exe runtime'], loc='upper right')

    ax2 = ax1.twinx()

    ax2.set_ylabel('Cost')
    ax2.set_ylim((np.min(cost)//10-2)*10, (np.max(cost)//10+3)*10)
    ax2.plot(np.arange(cost.size-exe_times), cost[0:runtime.size-exe_times],
             linewidth=5, ms=24, color='lightseagreen')
    ax2.plot(np.arange(cost.size-exe_times-1, cost.size), cost[runtime.size-exe_times-1:cost.size],
             linewidth=5, ms=24, color='green')

    ax2.legend(['cfg cost', 'exe cost'], loc='upper center')

    plt.grid(axis='y')
    if not os.path.exists('plots'):
        os.makedirs('plots')
    plt.savefig(f'plots/{fig_name}.pdf')


def plot_comparison(runtime_1, runtime_2, cost_1, cost_2):
    fig, (ax1, ax2) = plt.subplots(1, 2)
    x_label = ['3-function', '5-function']
    x_ticks = [0.35, 0.65]
    bar_width = 0.05

    x_1 = [i-bar_width/2 for i in x_ticks]
    x_2 = [i+bar_width/2 for i in x_ticks]

    ax1.set_xticks(x_ticks, x_label)
    ax1.set_ylabel('Runtime (ms)')
    ax1.bar(x_1, runtime_1, width=bar_width,
            label='fix_prop', color='orange')
    ax1.bar(x_2, runtime_2, width=bar_width, label='ARCSA', color='green')
    ax1.legend(loc='upper left')

    ax2.set_xticks(x_ticks, x_label)
    ax2.set_ylabel('Cost')
    ax2.bar(x_1, cost_1, width=bar_width,
            label='fix_prop', color='orange')
    ax2.bar(x_2, cost_2, width=bar_width, label='ARCSA', color='green')
    ax2.legend(loc='upper left')

    plt.subplots_adjust(wspace=0.4)

    if not os.path.exists('plots'):
        os.makedirs('plots')
    plt.savefig('plots/comp_cost_and_runtime.pdf')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='config file', required=True)

    args = parser.parse_args()

    config_file = args.config
    with open(config_file, 'r', encoding='utf-8') as f:
        cfgs = yaml.safe_load(f)

    slo = cfgs['slo']
    nums = len(cfgs['images'])
    global exe_times
    exe_times = cfgs['exe_times']

    functions = []
    for i in range(0, nums):
        functions.append(f'function-{i}')
    cpu_alloction = []
    mem_alloction = []

    for func in functions:
        file_name = f'results/{func}-cpu.txt'
        alloc = np.loadtxt(file_name)[1:]
        cpu_alloction.append(alloc)
        file_name = f'results/{func}-mem.txt'
        alloc = np.loadtxt(file_name)[1:]
        mem_alloction.append(alloc)

    runtime = np.loadtxt('results/runtime.txt')[1:]
    cost = np.loadtxt('results/cost.txt')[1:]

    plot_cpu('CPU Allocation', cpu_alloction)
    plot_mem('Memory Allocation', mem_alloction)
    plot_runtime_and_cost('Runtime And Cost', runtime, cost, slo)

    plot_comparison(np.array([747, 1739.67]), np.array(
        [680.33, 1721.67]), np.array([335.75, 1033.60]), np.array([124.04, 279.92]))
