import pandas as pd
import matplotlib.pyplot as plt
import os

# ====== CONFIGURE PATHS =======
LOG_FILE_PATH = r"C:\Users\Aiswarya\Downloads\key off-vehiclewent to sleep.log"
EXCEL_OUTPUT_PATH = r"C:\Users\Aiswarya\Downloads\Results.xlsx"
PLOTS_OUTPUT_DIR = r"C:\Users\Aiswarya\Downloads\Plots"

os.makedirs(PLOTS_OUTPUT_DIR, exist_ok=True)

# ====== FAULT DICTIONARY =======
fault_dict = {
    (0, 0): "SYS_CHARGING_IN_PROGRESS",
    (0, 1): "PWR_AC_OVP_FAULT",
    (0, 2): "PWR_AC_UVP_RMS_FAULT",
    (0, 3): "PWR_AC_OVP_RMS_FAULT",
    (0, 4): "PWR_AC_OCP_FAULT",
    (0, 5): "PWR_AC_OCP_RMS_FAULT",
    (0, 6): "PWR_DCBUS_OVP_FAULT",
    (0, 7): "PWR_DCBUS_UVP_FAULT",
    (1, 0): "PWR_IOUT_OCP_FAULT",
    (1, 1): "PWR_VOUT_OVP_FAULT",
    (1, 2): "PWR_VAC_PLL_FAULT",
    (1, 3): "PWR_LLC_FJP_FAULT",
    (1, 4): "PWR_LLC_UFP_FAULT",
    (1, 5): "PWR_PFC_PCHG_FAULT",
    (1, 6): "PWR_CPU_FAULT_TZ",
    (1, 7): "PWR_CLA_TASK_OL_FAULT",
    (2, 0): "PWR_NO_LOAD_FAULT",
    (2, 1): "SYS_PLL_LOCK_STAT_FAULT",
    (2, 2): "SYS_PFC_STATE_FAULT",
    (2, 3): "SYS_LLC_STATE_FAULT",
    (2, 4): "SYS_AC_OVP_FAULT",
    (2, 5): "SYS_AC_OCP_FAULT",
    (2, 6): "SYS_DC_UVP_FAULT",
    (2, 7): "SYS_DC_OVP_FAULT",
    (3, 0): "SYS_OUT_OVP_FAULT",
    (3, 1): "SYS_OUT_OCP_FAULT",
    (3, 2): "SYS_ADC3V3_UV_FAULT",
    (3, 3): "SYS_ADC3V3_OV_FAULT",
    (3, 4): "SYS_TEMP1_OTP_FAULT",
    (3, 5): "SYS_TEMP2_OTP_FAULT",
    (3, 6): "SYS_TEMP3_OTP_FAULT",
    (3, 7): "SYS_TEMP4_OTP_FAULT",
    (4, 0): "SYS_TEMP1_SENSOR_FAIL",
    (4, 1): "SYS_TEMP2_SENSOR_FAIL",
    (4, 2): "SYS_TEMP3_SENSOR_FAIL",
    (4, 3): "SYS_TEMP4_SENSOR_FAIL",
    (4, 4): "SYS_HW_DISABLE_FAULT",
    (4, 5): "SYS_HEARTBEAT_FAULT",
    (4, 6): "WATCHDOG_RESET_FAULT",
    (4, 7): "SYS_VCU_WAKEUP_FAIL",
    (5, 0): "SYS_DIA_TEMP_FAULT",
    (5, 1): "SYS_CHRG_TIMEOUT",
    (5, 2): "SYS_OVER_CHRG_FAULT",
    (5, 3): "SYS_TEMP_DERATING_STAT",
    (5, 4): "SYS_FAN_DERATING_STAT",
    (5, 5): "SYS_ACV_DERATING_STAT",
    (5, 6): "SYS_PWR_DERATING_STAT",
    (5, 7): "SYS_VMCC_STAT",
}

# ====== FUNCTIONS =======

def read_log_to_df(log_path):
    cols = list("ABCDEFGHIJKLMN")
    print("Reading log file...")
    df = pd.read_csv(log_path, sep=r'\s+', header=None, names=cols, engine='python')
    print(f"Loaded {len(df)} rows from log")
    return df

def filter_and_save_excel(df, excel_path):
    print("Filtering CAN IDs and saving to Excel sheets...")

    filtered_11B = df[df['D'] == '0x11B']
    filtered_temp = df[(df['D'] == '0x122') & (df['G'] == 'EE')]
    filtered_analog = df[(df['D'] == '0x122') & (df['G'] == 'AA')]

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Raw_Log', index=False)
        filtered_11B.to_excel(writer, sheet_name='Charging_Data', index=False)
        filtered_temp.to_excel(writer, sheet_name='Temperature_Data', index=False)
        filtered_analog.to_excel(writer, sheet_name='Analog_Measurement', index=False)

    print("Filtering and saving done.")

def hex_to_int_safe(x):
    try:
        return int(str(x), 16)
    except:
        return 0

def convert_analog_hex_to_dec(df):
    print("Converting analog hex to decimal with scaling...")
    df_conv = pd.DataFrame()
    df_conv['AC Voltage'] = df['H'].apply(hex_to_int_safe) * 2
    df_conv['AC Current'] = df['I'].apply(hex_to_int_safe)
    df_conv['DC Bus Voltage'] = df['J'].apply(hex_to_int_safe) * 2
    df_conv['Output Voltage'] = df['K'].apply(hex_to_int_safe)
    df_conv['DC Current'] = df['L'].apply(hex_to_int_safe)
    df_conv['Frequency'] = df['M'].apply(hex_to_int_safe)
    return df_conv

def decode_faults(row):
    fault_bytes = []
    for col in ['G','H','I','J','K','L','M','N']:
        try:
            fault_bytes.append(int(str(row[col]), 16))
        except:
            fault_bytes.append(0)

    faults_found = []
    for (byte_idx, bit_pos), name in fault_dict.items():
        if byte_idx < len(fault_bytes):
            if (fault_bytes[byte_idx] >> bit_pos) & 1:
                faults_found.append(name)
    return "; ".join(faults_found) if faults_found else "No Fault"

def add_fault_column(df):
    print("Decoding faults...")
    df['Faults'] = df.apply(decode_faults, axis=1)
    return df

def filter_fault_rows(df):
    fault_df = df[df['Faults'] != "No Fault"].copy()
    print(f"Found {len(fault_df)} rows with faults")
    return fault_df

def save_converted_analog(df, excel_path):
    print("Saving converted analog data to Excel...")
    with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a') as writer:
        df.to_excel(writer, sheet_name='Converted_Analog', index=False)

def save_converted_charging(df, excel_path):
    print("Saving charging data with faults to Excel...")
    with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a') as writer:
        df.to_excel(writer, sheet_name='Converted_Charging_Data', index=False)

def save_faults_only(df, excel_path):
    print("Saving only fault rows to Excel...")
    with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a') as writer:
        df.to_excel(writer, sheet_name='Charging_Faults', index=False)

def plot_analog_data(df):
    print("Plotting analog data...")
    plots = {
        'DC Current': 'DC_Current.jpg',
        'DC Bus Voltage': 'DC_Bus_Voltage.jpg',
        'AC Current': 'AC_Current.jpg',
        'Output Voltage': 'Output_Voltage.jpg',
        'AC Voltage': 'AC_Voltage.jpg',
        'Frequency': 'Frequency.jpg',
    }

    for col, filename in plots.items():
        if col in df.columns:
            plt.figure(figsize=(10,5))
            plt.plot(df.index, df[col])
            plt.title(col)
            plt.xlabel("Time (s)")
            plt.ylabel(col)
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(PLOTS_OUTPUT_DIR, filename))
            plt.close()
            print(f"Saved plot: {filename}")
        else:
            print(f"Column {col} missing in analog data, skipping plot.")

# ====== MAIN =======

def main():
    df_log = read_log_to_df(LOG_FILE_PATH)

    filter_and_save_excel(df_log, EXCEL_OUTPUT_PATH)

    df_analog_raw = pd.read_excel(EXCEL_OUTPUT_PATH, sheet_name='Analog_Measurement')
    df_analog_converted = convert_analog_hex_to_dec(df_analog_raw)
    save_converted_analog(df_analog_converted, EXCEL_OUTPUT_PATH)

    df_charging_raw = pd.read_excel(EXCEL_OUTPUT_PATH, sheet_name='Charging_Data')
    df_charging_with_faults = add_fault_column(df_charging_raw)
    save_converted_charging(df_charging_with_faults, EXCEL_OUTPUT_PATH)

    df_faults = filter_fault_rows(df_charging_with_faults)
    save_faults_only(df_faults, EXCEL_OUTPUT_PATH)

    plot_analog_data(df_analog_converted)

    print("Processing complete!")

if __name__ == "__main__":
    main()
