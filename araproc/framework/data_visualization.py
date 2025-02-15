import numpy as np
import matplotlib.pyplot as plt
from araproc.framework import waveform_utilities as wu
from araproc.framework import map_utilities as mu
import ROOT
ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch(True) # tell root not to open gui windows

"""
It's important to use a non-GUI backend!
Otherwise using matplotlib functions in a loop can memory leak.
See this thread for an interesting discussion:
https://github.com/matplotlib/matplotlib/issues/20300.
"""
import matplotlib # noqa : E402
matplotlib.use("agg")
__mplver = matplotlib.__version__ # this seems to fix a rare segfault (don't ask me...)

def plot_waveform_bundle(
    waveform_dict = None,
    time_or_freq = "time",
    ouput_file_path = None
    ):
    """
    Code to plot a bundle of waveforms.
    Please be aware that because this is matplotlib,
    this function is very slow (about 2.5 s per event).
    As a result, you probably shouldn't use it to draw many events.
    It's meant for debugging and visualization.
    """
    
    ####################
    # sanitize inputs
    ####################

    # make sure they have requested something valid (time vs freq domain)
    time_or_freq_options = ["time", "freq"]
    if time_or_freq not in time_or_freq_options:
        raise KeyError(f"Requested option ({time_or_freq}) is not in approved list: {time_or_freq_options}")

    xlabel_options = {
        "time" : "Time (ns)",
        "freq" : "Frequency (GHz)"
    }
    ylabel_options = {
        "time" : "Voltage (V)",
        "freq" : "log10 Spectrum (au)"
    }    

    if not isinstance(ouput_file_path, str):
        raise TypeError("Path to output file must be a string")
        
    ####################
    # actually make plots
    ####################

    # get the waves to plot
    tgraphs_to_plot = waveform_dict

    # set up fig and axes
    fig, axd = plt.subplot_mosaic(
                            [["ch0", "ch1", "ch2", "ch3"],
                             ["ch4", "ch5", "ch6", "ch7"],
                             ["ch8", "ch9", "ch10", "ch11"],
                             ["ch12", "ch13", "ch14", "ch15"]],
                              figsize=(10, 7), 
                              sharex=True,
                              sharey=True,
                              layout="constrained")

    # draw the graphs, label each one appropriately
    for wave_key in tgraphs_to_plot.keys():
        times, volts = wu.tgraph_to_arrays(tgraphs_to_plot[wave_key])
        xvals = times
        yvals = volts

        if time_or_freq == "freq":
            # if they frequested frequency domain, do the FFT
            freqs, spectrum = wu.time2freq(times, volts)
            xvals = freqs
            yvals = np.log10(np.abs(spectrum))

        axd[f"ch{wave_key}"].plot(xvals, yvals) # make the plot
        axd[f"ch{wave_key}"].set_title(f"Channel {wave_key}")

    # label axes  
    for ax in [axd["ch12"], axd["ch13"], axd["ch14"], axd["ch15"]]:
        ax.set_xlabel(xlabel_options[time_or_freq])
    for ax in [axd["ch0"], axd["ch4"], axd["ch8"], axd["ch12"]]:
        ax.set_ylabel(ylabel_options[time_or_freq])
    
    # make limits look nice
    if time_or_freq == "freq":
        ax.set_ylim([1,4])

    # save figure
    fig.savefig(ouput_file_path)

    # careful cleanup
    plt.close(fig)
    del fig, axd

def plot_skymap(the_map = None,
                ouput_file_path = None
                ):
    
    if the_map is None:
        raise Exception("the_map is None")

    if not isinstance(ouput_file_path, str):
        raise TypeError("Path to output file must be a string")

    corr_peak, peak_phi, peak_theta = mu.get_corr_map_peak(the_map)
    the_map.SetTitle(f"Peak Phi/Theta = {peak_phi:.1f}, {peak_theta:.1f}")
    the_map.GetXaxis().SetTitle("Phi (deg)")
    the_map.GetYaxis().SetTitle("Theta (deg)")
    the_map.GetZaxis().SetTitle("Correlation")

    c = ROOT.TCanvas("c", "c", 700, 500)
    c.cd()
    the_map.Draw("z aitoff")
    ROOT.gPad.SetRightMargin(0.15) # make space for the z axis
    c.SaveAs(ouput_file_path)
    ROOT.gPad.SetRightMargin(0) # reset, so we don't affect settings globally
    c.Close()

    del c
