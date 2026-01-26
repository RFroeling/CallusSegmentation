import os
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="whitegrid")


def choose_file(initialdir=None):
    root = tk.Tk()
    root.withdraw()
    filepath = filedialog.askopenfilename(
        title="Select metric_log.csv",
        initialdir=initialdir or os.getcwd(),
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    root.destroy()
    return filepath


def load_and_prepare(path):
    df = pd.read_csv(path, dtype=str)
    # Normalize expected columns
    for c in ["Age", "CellCount", "State"]:
        if c not in df.columns:
            raise KeyError(f"Required column '{c}' not found in {path}")
    # convert numeric columns
    df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
    df["CellCount"] = pd.to_numeric(df["CellCount"], errors="coerce")
    df["State"] = df["State"].astype("category")
    # optional: drop rows without both metrics
    return df


def plot_overview(df, title_suffix=""):
    # Create a multi-panel figure describing Age, CellCount and State
    plt.close("all")
    fig = plt.figure(constrained_layout=True, figsize=(12, 10))
    gs = fig.add_gridspec(3, 2)

    # 1. Distribution of CellCount
    ax1 = fig.add_subplot(gs[0, 0])
    sns.histplot(df["CellCount"].dropna(), kde=True, ax=ax1, color="C0")
    ax1.set_title("CellCount distribution" + title_suffix)
    ax1.set_xlabel("CellCount")
    ax1.set_ylabel("Frequency")

    # 2. Distribution of Age
    ax2 = fig.add_subplot(gs[0, 1])
    sns.histplot(df["Age"].dropna(), kde=True, ax=ax2, color="C1")
    ax2.set_title("Age distribution" + title_suffix)
    ax2.set_xlabel("Age")
    ax2.set_ylabel("Frequency")

    # 3. Boxplot CellCount by State
    ax3 = fig.add_subplot(gs[1, 0])
    sns.boxplot(x="State", y="CellCount", data=df, ax=ax3, palette="pastel")
    sns.stripplot(x="State", y="CellCount", data=df, ax=ax3, color="k", size=3, jitter=True, alpha=0.6)
    ax3.set_title("CellCount by State" + title_suffix)
    ax3.set_xlabel("State")
    ax3.set_ylabel("CellCount")

    # 4. Boxplot Age by State
    ax4 = fig.add_subplot(gs[1, 1])
    sns.boxplot(x="State", y="Age", data=df, ax=ax4, palette="muted")
    sns.stripplot(x="State", y="Age", data=df, ax=ax4, color="k", size=3, jitter=True, alpha=0.6)
    ax4.set_title("Age by State" + title_suffix)
    ax4.set_xlabel("State")
    ax4.set_ylabel("Age")

    # 5. Scatter Age vs CellCount colored by State with regression per state (where enough points)
    ax5 = fig.add_subplot(gs[2, :])
    states = df["State"].cat.categories if hasattr(df["State"], "cat") else df["State"].unique()
    palette = sns.color_palette(n_colors=len(states))
    sns.scatterplot(x="Age", y="CellCount", hue="State", data=df, ax=ax5, palette=palette, alpha=0.8, s=40)
    # add simple linear regression per state if enough points
    for i, st in enumerate(states):
        sub = df[df["State"] == st].dropna(subset=["Age", "CellCount"])
        if len(sub) >= 3:
            # fit linear model
            m, b = np.polyfit(sub["Age"], sub["CellCount"], 1)
            xs = np.linspace(sub["Age"].min(), sub["Age"].max(), 50)
            ax5.plot(xs, m * xs + b, color=palette[i], linestyle="--", linewidth=1)
    ax5.set_title("Age vs CellCount (colored by State)" + title_suffix)
    ax5.set_xlabel("Age")
    ax5.set_ylabel("CellCount")
    ax5.legend(title="State", bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.suptitle("Metric overview", fontsize=16)
    # plt.show()
    plt.tight_layout()
    plt.savefig("Metric_Overview.png", dpi=300)


def plot_summary_by_agebin(df, n_bins=4):
    # Bin Age and show mean CellCount per age bin and state
    tmp = df.dropna(subset=["Age", "CellCount", "State"]).copy()
    if tmp.empty:
        messagebox.showwarning("No data", "No rows with valid Age, CellCount and State to plot.")
        return
    tmp["AgeBin"] = pd.qcut(tmp["Age"], q=min(n_bins, len(tmp)), duplicates="drop")
    plt.figure(figsize=(10, 5))
    sns.barplot(x="AgeBin", y="CellCount", hue="State", data=tmp, ci="sd", palette="tab10")
    plt.xticks(rotation=30)
    plt.title("Mean CellCount per Age bin and State")
    plt.xlabel("Age bin (quantiles)")
    plt.ylabel("Mean CellCount ± SD")
    plt.tight_layout()
    plt.savefig("Mean_CellCount_per_AgeBin.png", dpi=300)


def main(path=None):
    if path is None:
        path = choose_file()
        if not path:
            return
    try:
        df = load_and_prepare(path)
    except Exception as e:
        messagebox.showerror("Load error", f"Could not load/prepare CSV:\n{e}")
        return

    # Basic checks and short summary in console
    print(f"Loaded {len(df)} rows from {os.path.basename(path)}")
    print(df[["Age", "CellCount", "State"]].describe(include="all"))

    # Produce primary overview plots
    plot_overview(df, title_suffix=f" — {os.path.basename(path)}")

    # Produce summary by age bins
    plot_summary_by_agebin(df, n_bins=4)


if __name__ == "__main__":
    main()