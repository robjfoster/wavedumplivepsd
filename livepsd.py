import argparse
import sys
import os
import time
from matplotlib.animation import FuncAnimation

import numpy as np
import matplotlib.pyplot as plt

module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

from gimmedatwave.gimmedatwave import gimmedatwave as gdw  # nopep8

global shorts_arr
global ratios_arr
shorts_arr = np.array([])
ratios_arr = np.array([])


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="input file")
    parser.add_argument('--digitizer', choices=[member.name for member in gdw.DigitizerFamily],
                        help='Select a digitizer family', required=True)
    parser.add_argument(
        '--trigger', help="The sample from which the short and long windows are calculated", default=630, type=int)
    parser.add_argument(
        '--shortWindow', help="Short window length in samples", default=10, type=int)
    parser.add_argument(
        '--longWindow', help="Long window length in samples", default=1000, type=int)
    parser.add_argument(
        '--lookback', help="Number of samples before the trigger to start the windows", default=5, type=int)
    parser.add_argument(
        "--adcThreshold", help="Integrate only above this threshold", default=15, type=int)
    return parser.parse_args()


def update_plot(frame, parser, args, sc):
    error_count = 0
    shorts = []
    longs = []
    ratios = []

    start_time = time.time()
    while time.time() - start_time < 1:
        try:
            event = parser.read_next()
            if event.id % 100 == 0:
                print(f"Event {event.id}")
            event.record = event.record * -1
            event.record = event.record - np.median(event.record[:300])
            event.record[event.record < args.adcThreshold] = 0
            short_array = event.record[(
                args.trigger - args.lookback):(args.trigger + args.shortWindow)]
            long_array = event.record[(
                args.trigger - args.lookback):(args.trigger + args.longWindow)]
            if np.max(short_array) < 150:
                continue
            short_sum = np.sum(short_array)
            long_sum = np.sum(long_array)
            shorts.append(short_sum)
            longs.append(long_sum)
            ratios.append(long_sum / short_sum)
        except IndexError:
            error_count += 1
            if error_count > 10:
                print("No new events for 10 seconds, exiting.")
                sys.exit()
            time.sleep(1)
    print("Setting datapoints")
    global shorts_arr, ratios_arr
    shorts_arr = np.concatenate((shorts_arr, np.array(shorts)))
    ratios_arr = np.concatenate((ratios_arr, np.log10(np.array(ratios))))
    sc.set_offsets(np.c_[shorts_arr, ratios_arr])
    sc.set_sizes([1])
    return sc,


def main():
    args = parse_args()
    parser = parser = gdw.Parser(
        args.inputfile, gdw.DigitizerFamily[args.digitizer])
    fig, ax = plt.subplots()
    sc = ax.scatter([], [])
    ax.set_ylim(0, 2)
    ax.set_xlim(0, 10000)
    animation = FuncAnimation(
        fig, update_plot, fargs=(parser, args, sc), frames=None)
    plt.show()


if __name__ == "__main__":
    main()
