import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

plt.rcParams["font.size"] = 14


def plot_run(
    data,
    average_epoch_interval=5,
    title="",
    finish=True,
    legend="Mean",
    std_dev="Standard deviation",
    log=False,
    ext="pdf",
    ylabel=None,
):
    # for name, series in data.to_dict("list").items():
    #     plt.plot(series, color="#0002", linewidth=0.1)

    #     # plt.plot(data, c=)
    column_count = len(data.columns)

    data = data.dropna().to_numpy()
    mean = data.mean(axis=1)
    # Smooth the mean data, get the STD and plot the result as a line with a confidence interval (use fill_between)
    data_len = len(mean) // average_epoch_interval * average_epoch_interval
    smoothed = np.reshape(mean[:data_len], [-1, average_epoch_interval]).mean(axis=1)

    if std_dev:
        smoothed_std = np.sqrt(
            np.sum(
                (
                    np.reshape(
                        data[:data_len], [-1, average_epoch_interval * column_count]
                    )
                    - np.expand_dims(smoothed, [1])
                )
                ** 2,
                axis=1,
            )
            / 14
        )

        plt.fill_between(
            np.arange(0, data_len, average_epoch_interval),
            smoothed - smoothed_std,
            smoothed + smoothed_std,
            alpha=0.3,
            label=std_dev,
        )

    plt.plot(
        np.arange(0, data_len, average_epoch_interval),
        smoothed,
        label=legend,
    )

    # data_len = len(mean) // average_epoch_interval * average_epoch_interval
    # smoothed = np.reshape(mean[:data_len], [-1, average_epoch_interval]).mean(axis=1)
    # plt.plot(np.arange(0, data_len, average_epoch_interval), smoothed, label=legend)

    if finish:
        # plt.title(title)
        if legend:
            plt.legend()
        plt.xlabel("Epoch")
        if ylabel:
            plt.ylabel(ylabel=ylabel)
        if log:
            plt.yscale("log")
        plt.tight_layout()
        plt.savefig(title.replace(" ", "_").lower() + "." + ext, transparent=True)
        plt.close()


data = pd.read_csv("metrics/final_metrics.csv", delimiter=",", index_col="Step")

for c in data.columns:
    if "MIN" in c or "MAX" in c:
        del data[c]

test_data = data[[c for c in data.columns if "test" in c]]
train_data = data[[c for c in data.columns if "test" not in c]]

plot_run(
    test_data[[c for c in test_data.columns if "accuracy" in c]],
    average_epoch_interval=5,
    legend="Validation accuracy",
    std_dev="Validation accuracy Std. Dev.",
    finish=False,
)
plot_run(
    train_data[[c for c in train_data.columns if "accuracy" in c]],
    average_epoch_interval=5,
    legend="Train accuracy",
    std_dev=False,
    ylabel="Accuracy",
    title="Accuracy",
)

plot_run(
    test_data[[c for c in test_data.columns if "err1" in c]],
    average_epoch_interval=5,
    finish=False,
    legend="Type 1: false positives",
)
plot_run(
    test_data[[c for c in test_data.columns if "err2" in c]],
    average_epoch_interval=5,
    title="Error rates",
    std_dev=False,
    ylabel="Error",
    legend="Type 2: false negatives",
)

plot_run(
    train_data[[c for c in train_data.columns if "loss" in c]],
    average_epoch_interval=1,
    title="Loss",
    ylabel="Loss",
    legend=False,
    log=True,
    std_dev=False,
)

ho_data = pd.read_csv("metrics/final_held_out_metrics.csv", delimiter=",")

ho_err1 = ho_data["err1"].to_numpy()
ho_err2 = ho_data["err2"].to_numpy()
ho_same = ho_data["same"].to_numpy()
ho_acc = 1 - ho_err1 - ho_err2
ho_f1 = 2 * ho_same / (2 * ho_same + ho_err1 + ho_err2)

print("held-out err1:", ho_err1.mean(), "SD:", ho_err1.std())
print("held-out err2:", ho_err2.mean(), "SD:", ho_err2.std())
print("held-out acc:", ho_acc.mean(), "SD:", ho_acc.std())
print("held-out f1:", ho_f1.mean(), "SD:", ho_f1.std())
