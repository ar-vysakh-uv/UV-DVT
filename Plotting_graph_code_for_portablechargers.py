#Author - Aiswarya

import pandas as pd
import matplotlib.pyplot as plt
import pickle
import os

# --- Paths ---
input_log_path = r"C:\path\to\your\logfile.log" #change according to your path
output_folder = r"C:\path\to\your\output"       #change according to your path

os.makedirs(output_folder, exist_ok=True)

# --- Safe Reader Function ---
def safe_read_log_file(file_path, expected_cols=19):
    rows = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 8:
                parts = (parts + [''] * expected_cols)[:expected_cols]
                rows.append(parts)
    headers = ['Time', 'In/Out', 'Channel', 'ID', 'Type', 'DLC',
               'Byte1', 'Byte2', 'Byte3', 'Byte4', 'Byte5', 'Byte6',
               'Byte7', 'Byte8', 'Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5']
    df = pd.DataFrame(rows, columns=headers[:expected_cols])
    return df

# --- Custom Time Parser (supports >24 hours) ---
def parse_time_column(df, time_col):
    def to_seconds_custom(t):
        try:
            parts = t.split(":")
            if len(parts) != 4:
                return None
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            milliseconds = int(parts[3])
            return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
        except:
            return None
    df['TimeSec'] = df[time_col].astype(str).apply(to_seconds_custom)
    print("Rows with invalid or missing time format:", df['TimeSec'].isna().sum())
    return df

# --- Convert Hex to Integer ---
def hex_to_int(low, high, byte_order='big'):
    try:
        low = int(str(low), 16)
        high = int(str(high), 16)
        return (high << 8) + low if byte_order == 'little' else (low << 8) + high
    except:
        return None

# --- Detect Time Column ---
def detect_time_column(df):
    for col in df.columns:
        if 'time' in col.lower():
            return col
    raise ValueError("No time column found")

# --- Extract Charger Data ---
def extract_charger_data(df):
    df = df.copy()
    df['ID'] = df['ID'].str.lower()
    df_ch = df[df['ID'] == '0xe157863'].copy()
    df_ch['ChargerOutputVoltage'] = df_ch.apply(lambda r: hex_to_int(r['Byte1'], r['Byte2'], 'big'), axis=1)
    df_ch['ChargerOutputCurrent'] = df_ch.apply(lambda r: hex_to_int(r['Byte3'], r['Byte4'], 'big'), axis=1)
    df_ch['ACInputVoltage'] = df_ch.apply(lambda r: hex_to_int(r['Byte6'], r['Byte7'], 'big'), axis=1)
    df_ch['ChargerOutputVoltage'] = df_ch['ChargerOutputVoltage'] / 100
    df_ch['ChargerOutputCurrent'] = df_ch['ChargerOutputCurrent'] / 100
    
    return df_ch[['TimeSec', 'ChargerOutputVoltage', 'ChargerOutputCurrent', 'ACInputVoltage']]

# --- Extract Battery Data ---
def extract_battery_data(df):
    df = df.copy()
    df['ID'] = df['ID'].str.lower()
    df_batt = df[df['ID'] == '0x11c'].copy()
    df_batt['BatteryVoltage'] = df_batt.apply(lambda r: hex_to_int(r['Byte3'], r['Byte4'], 'little'), axis=1)
    df_batt['BatteryVoltage'] = df_batt['BatteryVoltage'] / 100
    return df_batt[['TimeSec', 'BatteryVoltage']]

# --- Annotate Last Point ---
def annotate_plot(ax, x, y, color='blue'):
    if len(x) > 0 and len(y) > 0:
        ax.annotate(f'{y.iloc[-1]:.1f}',
                    xy=(x.iloc[-1], y.iloc[-1]),
                    xytext=(10, 0),
                    textcoords='offset points',
                    ha='left', va='center',
                    fontsize=9, color=color)

# --- Plot and Save ---
def plot_all_and_save(dfs, x_col, y_cols, ylabels, titles, overall_title, fig_path_png, fig_path_pickle):
    num_plots = len(dfs)
    fig, axs = plt.subplots(num_plots, 1, figsize=(10, 4 * num_plots), sharex=True)

    if num_plots == 1:
        axs = [axs]

    for i, (df, y_col, ylabel, title) in enumerate(zip(dfs, y_cols, ylabels, titles)):
        ax = axs[i]
        ax.plot(df[x_col], df[y_col], marker='o', linestyle='-', color='blue', markersize=3)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True)
        ax.legend([ylabel])
        annotate_plot(ax, df[x_col], df[y_col], color='blue')

    axs[-1].set_xlabel("Time (seconds)")
    fig.suptitle(overall_title, fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(fig_path_png)
    with open(fig_path_pickle, 'wb') as f:
        pickle.dump(fig, f)
    plt.show()

# --- Main ---
def main():
    print("Reading log file...")

    try:
        df_raw = safe_read_log_file(input_log_path)
        print("Columns loaded:", df_raw.columns.tolist())

        print("Unique CAN IDs found:")
        print(df_raw['ID'].dropna().str.lower().unique())

        time_col = detect_time_column(df_raw)
        df = parse_time_column(df_raw, time_col)

        charger_df = extract_charger_data(df).sort_values(by='TimeSec')
        battery_df = extract_battery_data(df).sort_values(by='TimeSec')

        print("\nFirst and last time strings in raw log:")
        print("First time string:", df_raw['Time'].iloc[0])
        print("Last  time string:", df_raw['Time'].iloc[-1])

        print("\nParsed time range (in seconds):")
        print("Minimum TimeSec:", df['TimeSec'].min())
        print("Maximum TimeSec:", df['TimeSec'].max())

        print(f"\nCharger samples: {len(charger_df)}")
        print(f"Battery samples: {len(battery_df)}")

        if not charger_df.empty or not battery_df.empty:
            dfs = []
            y_cols = []
            ylabels = []
            titles = []

            if not charger_df.empty:
                dfs.append(charger_df)
                y_cols.append('ChargerOutputVoltage')
                ylabels.append('Charger Voltage (V)')
                titles.append('Charger Output Voltage vs Time')

                dfs.append(charger_df)
                y_cols.append('ChargerOutputCurrent')
                ylabels.append('Charger Current (A)')
                titles.append('Charger Output Current vs Time')

                dfs.append(charger_df)
                y_cols.append('ACInputVoltage')
                ylabels.append('AC Input Voltage (V)')
                titles.append('AC Input Voltage vs Time')

            if not battery_df.empty:
                dfs.append(battery_df)
                y_cols.append('BatteryVoltage')
                ylabels.append('Battery Voltage (V)')
                titles.append('Battery Voltage vs Time')

            plot_all_and_save(
                dfs,
                x_col='TimeSec',
                y_cols=y_cols,
                ylabels=ylabels,
                titles=titles,
                overall_title='Charger, Battery and AC Input Data Over Time',
                fig_path_png=os.path.join(output_folder, 'all_plots_combined.png'),
                fig_path_pickle=os.path.join(output_folder, 'all_plots_combined.fig')
            )
        else:
            print("No charger or battery data found in the log.")

        print("\nAll plots saved to:", os.path.abspath(output_folder))

    except Exception as e:
        print("Error occurred:", e)

if __name__ == "__main__":
    main()
