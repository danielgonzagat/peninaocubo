from penin.engine.caos_plus import compute_caos_plus
from penin.engine.fibonacci import alpha_fib
from penin.engine.master_equation import MasterState, step_master
from penin.math.linf import linf_score


def main():
    state = MasterState(I=0.0)
    for t in range(5):
        metrics = {"acc": 0.7 + 0.05 * t, "robust": 0.6 + 0.04 * t, "calib": 0.8}
        weights = {"acc": 2.0, "robust": 1.5, "calib": 1.0}
        cost = 0.1 * t

        L_inf = linf_score(metrics, weights, cost)
        c_val, a_val, o_val, s_val = 0.6, 0.5 + 0.1 * t, 1.0, 1.0  # noqa: E741
        caos = compute_caos_plus(c_val, a_val, o_val, s_val)

        alpha = alpha_fib(t, alpha0=0.1, boost=max(0.1, caos / 1.0))
        state = step_master(state, delta_linf=L_inf, alpha_omega=alpha)

        print(f"t={t} | L∞={L_inf:.4f} | CAOS+={caos:.4f} | α={alpha:.5f} | I={state.I:.5f}")


if __name__ == "__main__":
    main()
