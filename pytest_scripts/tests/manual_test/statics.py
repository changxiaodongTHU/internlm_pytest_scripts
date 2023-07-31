import pandas as pd

pd.options.display.float_format = "{:.3f}".format


def get_statics_num(file):
    df = pd.read_csv(file)
    pd.set_option("display.width", None)
    # get ip class
    df_group = df.groupby(by="ip")
    ip_list = list(df_group.groups.keys())
    # get the max metrics
    for ip_address in ip_list:
        ip_df = df[df["ip"].str.contains(ip_address)]
        # print(ip_address, ip_df.describe())
        print(ip_address)
        if "cpu" in ip_df.columns:
            print(f'cpu max is: {round(ip_df["cpu"].max(),3)}%')
        print(f'mem used max is:{round(ip_df["mem_3"].max()/1024/1024/1024,3)}GB')
        print(f'diskIo_1 max is:{round(ip_df["diskIo_1"].max(),3)},diskIo_3 max is:{round(ip_df["diskIo_3"].max(),3)}')
        print(f'network_speed max is:{round(ip_df["networkSpeed_1"].max()/1024/1024,3)}MB/s')


if __name__ == "__main__":
    get_statics_num("./node_status_1672364905646.csv")
