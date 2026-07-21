"""
Noise Model — Measurement Noise for Zirconia Oxygen Sensor.

Simulates realistic electrical noise sources:
    - White noise (Gaussian): Random thermal fluctuations
    - 1/f (Flicker) noise: Low-frequency noise, increases with aging
    - Quantization noise: ADC digitization error
    - EMI spikes: Electromagnetic interference from aircraft systems
"""

import numpy as np
from app.config import (
    NOISE_WHITE_SIGMA, NOISE_FLICKER_BASE,
    NOISE_QUANTIZATION, NOISE_EMI_PROBABILITY,
    NOISE_EMI_AMPLITUDE
)


def white_noise(sigma: float = NOISE_WHITE_SIGMA) -> float:
    """
    Generate Gaussian white noise.

    Represents random thermal and shot noise in the sensor electronics.

    Args:
        sigma: Standard deviation of noise

    Returns:
        Noise value
    """
    return float(np.random.normal(0.0, sigma))


def flicker_noise(aging_factor: float = 0.0,
                  base_amplitude: float = NOISE_FLICKER_BASE) -> float:
    """
    Generate 1/f (flicker) noise.

    Amplitude increases with sensor aging due to degrading contacts
    and electrode interfaces.

    Uses a simple approximation: colored noise from filtered white noise.

    Args:
        aging_factor: Sensor aging (0 = new, 1 = end of life)
        base_amplitude: Base noise amplitude

    Returns:
        Flicker noise value
    """
    # Amplitude increases with aging
    amplitude = base_amplitude * (1.0 + 3.0 * aging_factor)
    # Simple 1/f approximation using heavy-tailed distribution
    return float(amplitude * np.random.standard_cauchy() * 0.1)


def quantization_noise(step_size: float = NOISE_QUANTIZATION) -> float:
    """
    Generate quantization noise from ADC digitization.

    Uniform distribution within ±step_size/2.

    Args:
        step_size: ADC quantization step size

    Returns:
        Quantization noise value
    """
    return float(np.random.uniform(-step_size / 2, step_size / 2))


def emi_spike(probability: float = NOISE_EMI_PROBABILITY,
              amplitude: float = NOISE_EMI_AMPLITUDE) -> float:
    """
    Generate electromagnetic interference spike.

    Occasional large spikes from aircraft electrical systems.

    Args:
        probability: Probability of spike occurring per reading
        amplitude: Maximum spike amplitude

    Returns:
        EMI spike value (0 if no spike)
    """
    if np.random.random() < probability:
        return float(np.random.choice([-1, 1]) * amplitude * np.random.random())
    return 0.0


def total_noise(aging_factor: float = 0.0) -> dict:
    """
    Calculate combined noise from all sources.

    Args:
        aging_factor: Current aging factor (0-1)

    Returns:
        Dictionary with noise components and total
    """
    n_white = white_noise()
    n_flicker = flicker_noise(aging_factor)
    n_quant = quantization_noise()
    n_emi = emi_spike()

    # Clip flicker noise to prevent extreme outliers
    n_flicker = float(np.clip(n_flicker, -0.5, 0.5))

    n_total = n_white + n_flicker + n_quant + n_emi

    return {
        "white_noise": round(n_white, 6),
        "flicker_noise": round(n_flicker, 6),
        "quantization_noise": round(n_quant, 6),
        "emi_spike": round(n_emi, 6),
        "total_noise": round(n_total, 6),
        "noise_rms": round(float(np.sqrt(
            n_white**2 + n_flicker**2 + n_quant**2 + n_emi**2
        )), 6)
    }


def apply_noise(clean_value: float, noise_amount: float) -> float:
    """
    Add noise to a clean measurement value.

    measured = clean + noise

    Args:
        clean_value: Clean (noiseless) value
        noise_amount: Noise amount in same units

    Returns:
        Noisy measurement
    """
    return clean_value + noise_amount


def signal_to_noise_ratio(signal: float, noise_rms: float) -> float:
    """
    Calculate signal-to-noise ratio in dB.

    SNR = 20 × log10(|signal| / noise_rms)

    Args:
        signal: Signal amplitude
        noise_rms: RMS noise amplitude

    Returns:
        SNR in dB
    """
    if noise_rms < 1e-10:
        return 100.0  # Effectively infinite SNR
    return float(20.0 * np.log10(abs(signal) / noise_rms))


def calculate_noise(aging_factor: float = 0.0, signal_level: float = 0.82) -> dict:
    """
    Run the complete noise model.

    Args:
        aging_factor: Current aging factor
        signal_level: Current signal level for SNR calculation

    Returns:
        Dictionary with noise analysis
    """
    result = total_noise(aging_factor)
    result["snr_db"] = round(
        signal_to_noise_ratio(signal_level, result["noise_rms"]), 2
    )
    return result
