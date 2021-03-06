"""
The ``power_curves`` module contains functions apply calculations to the power
curve of a wind turbine, wind farm or wind turbine cluster.

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

import numpy as np
import pandas as pd
from windpowerlib import tools


def smooth_power_curve(power_curve_wind_speeds, power_curve_values,
                       block_width=0.5,
                       standard_deviation_method='turbulence_intensity',
                       mean_gauss=0, **kwargs):
    # TODO: All functions in this module have to work without pandas
    r"""
    Smoothes the input power curve values by using a gaussian distribution.

    Parameters
    ----------
    power_curve_wind_speeds : pandas.Series
        Wind speeds in m/s for which the power curve values are provided in
        `power_curve_values`.
    power_curve_values : pandas.Series or numpy.array
        Power curve values corresponding to wind speeds in
        `power_curve_wind_speeds`.
    block_width : Float
        Width of the moving block. Default: 0.5.
    standard_deviation_method : String
        Method for calculating the standard deviation for the gaussian
        distribution. Options: 'turbulence_intensity', 'Norgaard', 'Staffell'.
        Default: 'turbulence_intensity'.

    Other Parameters
    ----------------
    turbulence intensity : Float, optional
        Turbulence intensity at hub height of the wind turbine the power curve
        is smoothed for.

    Returns
    -------
    smoothed_power_curve_df : pd.DataFrame
        Smoothed power curve. DataFrame has 'wind_speed' and
        'power' columns with wind speeds in m/s and the corresponding power
        curve value in W.

    Notes
    -----
    The following equation is used [1]_:
        # TODO: add equation

    References
    ----------
    .. [1]  Knorr, K.: "Modellierung von raum-zeitlichen Eigenschaften der
             Windenergieeinspeisung für wetterdatenbasierte
             Windleistungssimulationen". Universität Kassel, Diss., 2016,
             p. 106

    # TODO: add references
    """
    # Specify normalized standard deviation
    if standard_deviation_method == 'turbulence_intensity':
        if 'turbulence_intensity' in kwargs:
            normalized_standard_deviation = kwargs['turbulence_intensity']
        else:
            raise ValueError("Turbulence intensity must be defined for " +
                             "using 'turbulence_intensity' as " +
                             "`standard_deviation_method`")
    elif standard_deviation_method == 'Norgaard':
        pass # TODO add
    elif standard_deviation_method == 'Staffell':
        normalized_standard_deviation = 0.2
    # Initialize list for power curve values
    smoothed_power_curve_values = []
    # Step of power curve wind speeds
    step = power_curve_wind_speeds.iloc[-5] - power_curve_wind_speeds.iloc[-6]
    # Append wind speeds to `power_curve_wind_speeds` until 40 m/s
    while (power_curve_wind_speeds.values[-1] < 40.0):
        power_curve_wind_speeds = power_curve_wind_speeds.append(
            pd.Series(power_curve_wind_speeds.iloc[-1] + step,
                      index=[power_curve_wind_speeds.index[-1] + 1]))
        power_curve_values = power_curve_values.append(
            pd.Series(0.0, index=[power_curve_values.index[-1] + 1]))
    for power_curve_wind_speed in power_curve_wind_speeds:
        # Create array of wind speeds for the moving block
        wind_speeds_block = (
            np.arange(-15.0, 15.0 + block_width, block_width) +
            power_curve_wind_speed)
        # Get standard deviation for gaussian filter
        standard_deviation = (
            (power_curve_wind_speed * normalized_standard_deviation + 0.6)
            if standard_deviation_method is 'Staffell'
            else power_curve_wind_speed * normalized_standard_deviation)
        # Get the smoothed value of the power output
        smoothed_value = sum(
            block_width * np.interp(wind_speed, power_curve_wind_speeds,
                                    power_curve_values, left=0, right=0) *
            tools.gaussian_distribution(
                power_curve_wind_speed - wind_speed,
                standard_deviation, mean_gauss)
            for wind_speed in wind_speeds_block)
        # Add value to list - add 0 if `smoothed_value` is nan. This occurs
        # because the gaussian distribution is not defined for 0.
        smoothed_power_curve_values.append(0 if np.isnan(smoothed_value)
                                           else smoothed_value)
    # Create smoothed power curve DataFrame
    smoothed_power_curve_df = pd.DataFrame(
        data=[list(power_curve_wind_speeds.values),
              smoothed_power_curve_values]).transpose()
    # Rename columns of DataFrame
    smoothed_power_curve_df.columns = ['wind_speed', 'power']
#    # Plot power curves
#    fig = plt.figure()
#    plt.plot(power_curve_wind_speeds.values, power_curve_values.values)
#    plt.plot(power_curve_wind_speeds.values, smoothed_power_curve_values)
#    fig.savefig(os.path.abspath(os.path.join(
#        os.path.dirname(__file__), '../Plots/power_curves',
#        '{0}_{1}_{2}.png'.format(kwargs['object_name'],
#                                 standard_deviation_method, block_width))))
#    plt.close() # TODO: delete plot later
    return smoothed_power_curve_df


def wake_losses_to_power_curve(power_curve_wind_speeds, power_curve_values,
                               wake_losses_method='constant_efficiency',
                               wind_farm_efficiency=None):
    r"""
    Applies wake losses depending on the method to a power curve.

    Parameters
    ----------
    power_curve_wind_speeds : pandas.Series
        Wind speeds in m/s for which the power curve values are provided in
        `power_curve_values`.
    power_curve_values : pandas.Series or numpy.array
        Power curve values corresponding to wind speeds in
        `power_curve_wind_speeds`.
    wake_losses_method : String
        Defines the method for talking wake losses within the farm into
        consideration. Default: 'constant_efficiency'.
    wind_farm_efficiency : Float or pd.DataFrame or Dictionary
        Efficiency of the wind farm. Either constant (float) or wind efficiency
        curve (pd.DataFrame or Dictionary) contianing 'wind_speed' and
        'efficiency' columns/keys with wind speeds in m/s and the
        corresponding dimensionless wind farm efficiency. Default: None.

    Returns
    -------
    power_curve_df : pd.DataFrame
        With wind farm efficiency reduced power curve. DataFrame power curve
        values in W with the corresponding wind speeds in m/s.

    Notes
    -----
    TODO add

    """
    # Create power curve DataFrame
    power_curve_df = pd.DataFrame(
        data=[list(power_curve_wind_speeds),
              list(power_curve_values)]).transpose()
    # Rename columns of DataFrame
    power_curve_df.columns = ['wind_speed', 'power']
    if wake_losses_method == 'constant_efficiency':
        if not isinstance(wind_farm_efficiency, float):
            raise TypeError("'wind_farm_efficiency' must be float if " +
                            "`wake_losses_method´ is '{0}'")
        power_curve_df['power'] = power_curve_values * wind_farm_efficiency
    elif wake_losses_method == 'wind_efficiency_curve':
        if (not isinstance(wind_farm_efficiency, dict) and
                not isinstance(wind_farm_efficiency, pd.DataFrame)):
            raise TypeError(
                "'wind_farm_efficiency' must be a dictionary or " +
                "pd.DataFrame if `wake_losses_method´ is '{0}'")
        df = pd.concat([power_curve_df.set_index('wind_speed'),
                        wind_farm_efficiency.set_index('wind_speed')], axis=1)
        # Add by efficiency reduced power column (nan values of efficiency
        # are interpolated)
        df['reduced_power'] = df['power'] * df['efficiency'].interpolate(
            method='index')
        reduced_power = df['reduced_power'].dropna()
        power_curve_df = pd.DataFrame([reduced_power.index,
                                       reduced_power.values]).transpose()
        power_curve_df.columns = ['wind_speed', 'power']
    else:
        raise ValueError(
            "`wake_losses_method` is {0} but should be None, ".format(
                wake_losses_method) +
            "'constant_efficiency' or 'wind_efficiency_curve'")
    return power_curve_df
