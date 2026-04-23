import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt


SPEED_OF_LIGHT = 3e8


def photon_lifetime(cavity_length, reflectivity_1, reflectivity_2, internal_loss=0.0):
    round_trip_loss = -np.log(reflectivity_1 * reflectivity_2) / (2 * cavity_length) + internal_loss
    return 1.0 / (SPEED_OF_LIGHT * round_trip_loss)


def stimulated_transition_rate(cross_section, refractive_index):
    return cross_section * SPEED_OF_LIGHT / refractive_index


def statz_de_mars(t, y, n0, tau_c, tau_r, B):
    n, q = y
    dn_dt = (n0 - n) / tau_r - 2.0 * B * q * n
    dq_dt = (B * n - 1.0 / tau_c) * q
    return [dn_dt, dq_dt]


def threshold_inversion(tau_c, B):
    return 1.0 / (B * tau_c)


def cw_steady_state(n0, tau_c, tau_r, B):
    n_th = threshold_inversion(tau_c, B)
    q_ss = (n0 - n_th) / (2.0 * B * tau_r * n_th)
    return n_th, max(q_ss, 0.0)


def relaxation_frequency(n0, tau_c, tau_r, B):
    n_th = threshold_inversion(tau_c, B)
    r = n0 / n_th
    if r <= 1.0:
        return 0.0
    return np.sqrt((r - 1.0) / (tau_c * tau_r)) / (2.0 * np.pi)


def simulate_transient(n0, tau_c, tau_r, B, t_span, n_init=None, q_init=1.0):
    if n_init is None:
        n_init = n0
    sol = solve_ivp(
        statz_de_mars,
        t_span,
        [n_init, q_init],
        args=(n0, tau_c, tau_r, B),
        method="Radau",
        rtol=1e-8,
        atol=1e-10,
        dense_output=True,
    )
    return sol.t, sol.y[0], sol.y[1]


def simulate_q_switch(n0, tau_c_low, tau_c_high, tau_r, B, pump_time, pulse_window):
    n_pump = n0 * (1.0 - np.exp(-pump_time / tau_r))

    t1, n1, q1 = simulate_transient(
        n0, tau_c_low, tau_r, B,
        (0, pump_time),
        n_init=0.0,
        q_init=1.0,
    )

    t2, n2, q2 = simulate_transient(
        n0, tau_c_high, tau_r, B,
        (0, pulse_window),
        n_init=n1[-1],
        q_init=q1[-1] if q1[-1] > 1.0 else 1.0,
    )

    t_total = np.concatenate([t1, t1[-1] + t2])
    n_total = np.concatenate([n1, n2])
    q_total = np.concatenate([q1, q2])
    return t_total, n_total, q_total


def ndyag_params():
    cross_section = 2.8e-19 * 1e-4
    refractive_index = 1.82
    tau_r = 230e-6
    cavity_length = 0.1
    R1 = 1.0
    R2 = 0.8

    tau_c = photon_lifetime(cavity_length, R1, R2)
    B = stimulated_transition_rate(cross_section, refractive_index)
    n_th = threshold_inversion(tau_c, B)
    n0 = 2.0 * n_th

    return {
        "n0": n0,
        "tau_c": tau_c,
        "tau_r": tau_r,
        "B": B,
        "cavity_length": cavity_length,
        "R1": R1,
        "R2": R2,
        "cross_section": cross_section,
        "refractive_index": refractive_index,
    }


def ruby_params():
    cross_section = 2.5e-20 * 1e-4
    refractive_index = 1.76
    tau_r = 3e-3
    cavity_length = 0.15
    R1 = 1.0
    R2 = 0.7

    tau_c = photon_lifetime(cavity_length, R1, R2)
    B = stimulated_transition_rate(cross_section, refractive_index)
    n_th = threshold_inversion(tau_c, B)
    n0 = 1.5 * n_th

    return {
        "n0": n0,
        "tau_c": tau_c,
        "tau_r": tau_r,
        "B": B,
        "cavity_length": cavity_length,
        "R1": R1,
        "R2": R2,
        "cross_section": cross_section,
        "refractive_index": refractive_index,
    }


def plot_cw_analysis(params, title_prefix=""):
    n0 = params["n0"]
    tau_c = params["tau_c"]
    tau_r = params["tau_r"]
    B = params["B"]

    n_th = threshold_inversion(tau_c, B)
    pump_ratios = np.linspace(1.01, 5.0, 200)
    n0_values = pump_ratios * n_th

    q_ss_values = []
    freq_values = []
    for n0_val in n0_values:
        _, q_ss = cw_steady_state(n0_val, tau_c, tau_r, B)
        q_ss_values.append(q_ss)
        freq_values.append(relaxation_frequency(n0_val, tau_c, tau_r, B))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(pump_ratios, q_ss_values, "b-", linewidth=2)
    ax1.set_xlabel("Pump Ratio (n0 / n_th)")
    ax1.set_ylabel("Steady-State Photon Density (m^-3)")
    ax1.set_title(f"{title_prefix}CW Photon Density vs Pump Ratio")
    ax1.grid(True, alpha=0.3)
    ax1.ticklabel_format(axis="y", style="scientific", scilimits=(0, 0))

    ax2.plot(pump_ratios, np.array(freq_values) * 1e-3, "r-", linewidth=2)
    ax2.set_xlabel("Pump Ratio (n0 / n_th)")
    ax2.set_ylabel("Relaxation Frequency (kHz)")
    ax2.set_title(f"{title_prefix}Relaxation Oscillation Frequency")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_relaxation_oscillations(params, title_prefix=""):
    n0 = params["n0"]
    tau_c = params["tau_c"]
    tau_r = params["tau_r"]
    B = params["B"]

    t_end = 10.0 * tau_r
    t, n, q = simulate_transient(n0, tau_c, tau_r, B, (0, t_end))

    n_th = threshold_inversion(tau_c, B)
    _, q_ss = cw_steady_state(n0, tau_c, tau_r, B)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    t_us = t * 1e6

    ax1.plot(t_us, n, "b-", linewidth=1.5)
    ax1.axhline(y=n_th, color="r", linestyle="--", linewidth=1, label="n_th")
    ax1.set_ylabel("Population Inversion (m^-3)")
    ax1.set_title(f"{title_prefix}Relaxation Oscillations")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.ticklabel_format(axis="y", style="scientific", scilimits=(0, 0))

    ax2.plot(t_us, q, "r-", linewidth=1.5)
    ax2.axhline(y=q_ss, color="b", linestyle="--", linewidth=1, label="q_ss")
    ax2.set_xlabel("Time (us)")
    ax2.set_ylabel("Photon Density (m^-3)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.ticklabel_format(axis="y", style="scientific", scilimits=(0, 0))

    plt.tight_layout()
    return fig


def plot_q_switching(params, title_prefix=""):
    n0 = params["n0"] * 3.0
    tau_c_high = params["tau_c"]
    tau_r = params["tau_r"]
    B = params["B"]

    tau_c_low = tau_c_high / 100.0
    pump_time = 2.0 * tau_r
    pulse_window = 50.0 * tau_c_high

    t, n, q = simulate_q_switch(n0, tau_c_low, tau_c_high, tau_r, B, pump_time, pulse_window)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    t_us = t * 1e6

    ax1.plot(t_us, n, "b-", linewidth=1.5)
    n_th = threshold_inversion(tau_c_high, B)
    ax1.axhline(y=n_th, color="r", linestyle="--", linewidth=1, label="n_th (high Q)")
    ax1.set_ylabel("Population Inversion (m^-3)")
    ax1.set_title(f"{title_prefix}Q-Switched Giant Pulse")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.ticklabel_format(axis="y", style="scientific", scilimits=(0, 0))

    ax2.plot(t_us, q, "r-", linewidth=1.5)
    ax2.set_xlabel("Time (us)")
    ax2.set_ylabel("Photon Density (m^-3)")
    ax2.grid(True, alpha=0.3)
    ax2.ticklabel_format(axis="y", style="scientific", scilimits=(0, 0))

    switch_time = pump_time * 1e6
    for ax in (ax1, ax2):
        ax.axvline(x=switch_time, color="g", linestyle=":", linewidth=1.5, label="Q-switch")
    ax1.legend()
    ax2.legend()

    plt.tight_layout()
    return fig


def plot_phase_portrait(params, title_prefix=""):
    n0 = params["n0"]
    tau_c = params["tau_c"]
    tau_r = params["tau_r"]
    B = params["B"]

    n_th = threshold_inversion(tau_c, B)
    _, q_ss = cw_steady_state(n0, tau_c, tau_r, B)

    fig, ax = plt.subplots(figsize=(8, 8))

    initial_conditions = [
        (0.5 * n0, 1.0),
        (n0, 1.0),
        (1.5 * n0, 1.0),
        (2.0 * n0, 1.0),
        (n0, 0.1 * q_ss),
        (n0, 10.0 * q_ss),
    ]

    colors = plt.cm.viridis(np.linspace(0, 1, len(initial_conditions)))
    t_end = 10.0 * tau_r

    for i, (n_init, q_init) in enumerate(initial_conditions):
        t, n_traj, q_traj = simulate_transient(
            n0, tau_c, tau_r, B, (0, t_end), n_init=n_init, q_init=q_init
        )
        ax.plot(n_traj, q_traj, color=colors[i], linewidth=1.2, alpha=0.8)
        ax.plot(n_traj[0], q_traj[0], "o", color=colors[i], markersize=6)
        ax.plot(n_traj[-1], q_traj[-1], "s", color=colors[i], markersize=6)

    ax.plot(n_th, q_ss, "k*", markersize=15, zorder=5, label="Steady State")
    ax.set_xlabel("Population Inversion n (m^-3)")
    ax.set_ylabel("Photon Density q (m^-3)")
    ax.set_title(f"{title_prefix}Phase Portrait (n vs q)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.ticklabel_format(style="scientific", scilimits=(0, 0))

    plt.tight_layout()
    return fig


def plot_pump_threshold_scan(params, title_prefix=""):
    tau_c = params["tau_c"]
    tau_r = params["tau_r"]
    B = params["B"]
    n_th = threshold_inversion(tau_c, B)

    pump_ratios = [0.8, 1.0, 1.5, 2.0, 3.0]
    fig, axes = plt.subplots(len(pump_ratios), 1, figsize=(12, 3 * len(pump_ratios)), sharex=True)

    t_end = 5.0 * tau_r

    for idx, r in enumerate(pump_ratios):
        n0_val = r * n_th
        t, n, q = simulate_transient(n0_val, tau_c, tau_r, B, (0, t_end))
        t_us = t * 1e6
        axes[idx].plot(t_us, q, "r-", linewidth=1.5)
        axes[idx].set_ylabel("q (m^-3)")
        axes[idx].set_title(f"r = n0/n_th = {r:.1f}")
        axes[idx].grid(True, alpha=0.3)
        axes[idx].ticklabel_format(axis="y", style="scientific", scilimits=(0, 0))

    axes[-1].set_xlabel("Time (us)")
    fig.suptitle(f"{title_prefix}Photon Density for Different Pump Ratios", fontsize=14, y=1.01)
    plt.tight_layout()
    return fig


def main():
    print("=" * 60)
    print("LASER RESONATOR PULSE DYNAMICS MODEL")
    print("Statz-de Mars Rate Equations")
    print("=" * 60)

    params_ndyag = ndyag_params()
    params_ruby = ruby_params()

    print("\n--- Nd:YAG Laser Parameters ---")
    print(f"  tau_c  = {params_ndyag['tau_c']:.4e} s")
    print(f"  tau_r  = {params_ndyag['tau_r']:.4e} s")
    print(f"  B      = {params_ndyag['B']:.4e} m^3/s")
    print(f"  n_th   = {threshold_inversion(params_ndyag['tau_c'], params_ndyag['B']):.4e} m^-3")
    print(f"  n0     = {params_ndyag['n0']:.4e} m^-3")
    print(f"  f_rel  = {relaxation_frequency(params_ndyag['n0'], params_ndyag['tau_c'], params_ndyag['tau_r'], params_ndyag['B']):.2f} Hz")

    n_th_nd, q_ss_nd = cw_steady_state(
        params_ndyag["n0"], params_ndyag["tau_c"], params_ndyag["tau_r"], params_ndyag["B"]
    )
    print(f"  q_ss   = {q_ss_nd:.4e} m^-3")

    print("\n--- Ruby Laser Parameters ---")
    print(f"  tau_c  = {params_ruby['tau_c']:.4e} s")
    print(f"  tau_r  = {params_ruby['tau_r']:.4e} s")
    print(f"  B      = {params_ruby['B']:.4e} m^3/s")
    print(f"  n_th   = {threshold_inversion(params_ruby['tau_c'], params_ruby['B']):.4e} m^-3")
    print(f"  n0     = {params_ruby['n0']:.4e} m^-3")
    print(f"  f_rel  = {relaxation_frequency(params_ruby['n0'], params_ruby['tau_c'], params_ruby['tau_r'], params_ruby['B']):.2f} Hz")

    n_th_rb, q_ss_rb = cw_steady_state(
        params_ruby["n0"], params_ruby["tau_c"], params_ruby["tau_r"], params_ruby["B"]
    )
    print(f"  q_ss   = {q_ss_rb:.4e} m^-3")

    print("\nGenerating plots...")

    fig1 = plot_cw_analysis(params_ndyag, title_prefix="Nd:YAG - ")
    fig1.savefig("ndyag_cw_analysis.png", dpi=150, bbox_inches="tight")

    fig2 = plot_relaxation_oscillations(params_ndyag, title_prefix="Nd:YAG - ")
    fig2.savefig("ndyag_relaxation.png", dpi=150, bbox_inches="tight")

    fig3 = plot_q_switching(params_ndyag, title_prefix="Nd:YAG - ")
    fig3.savefig("ndyag_q_switch.png", dpi=150, bbox_inches="tight")

    fig4 = plot_phase_portrait(params_ndyag, title_prefix="Nd:YAG - ")
    fig4.savefig("ndyag_phase_portrait.png", dpi=150, bbox_inches="tight")

    fig5 = plot_pump_threshold_scan(params_ndyag, title_prefix="Nd:YAG - ")
    fig5.savefig("ndyag_pump_scan.png", dpi=150, bbox_inches="tight")

    fig6 = plot_relaxation_oscillations(params_ruby, title_prefix="Ruby - ")
    fig6.savefig("ruby_relaxation.png", dpi=150, bbox_inches="tight")

    fig7 = plot_q_switching(params_ruby, title_prefix="Ruby - ")
    fig7.savefig("ruby_q_switch.png", dpi=150, bbox_inches="tight")

    plt.close("all")

    print("Saved plots:")
    print("  ndyag_cw_analysis.png")
    print("  ndyag_relaxation.png")
    print("  ndyag_q_switch.png")
    print("  ndyag_phase_portrait.png")
    print("  ndyag_pump_scan.png")
    print("  ruby_relaxation.png")
    print("  ruby_q_switch.png")
    print("\nDone.")


if __name__ == "__main__":
    main()
