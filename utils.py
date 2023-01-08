import time
import statistics
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from pathlib import Path
from typing import Optional
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.common.by import By


def fetch_data_from_url(url: str):
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(4)
    card_name = driver.find_element(By.XPATH, "//* [@id='__next']/main/div[2]/div[2]/div[1]/div[1]").text
    table_text = driver.find_element(By.XPATH, "//* [@id='__next']/main/div[3]").text
    return card_name, table_text


def process_table_text(table_text):
    t = list(table_text.split('\n')[7:])
    d = defaultdict(list)
    for i in range(0, len(t)-4, 5):
        buyer, seller, date, serial_number, price = t[i], t[i+1], t[i+2], t[i+3], t[i+4]
        p = float(price[:-1])
        sn = int(serial_number[1:])
        d['buyer'].append(buyer)
        d['seller'].append(seller)
        d['date'].append(date)
        d['serial_number'].append(sn)
        d['price'].append(p)
    df = pd.DataFrame.from_dict(d)
    return df


def update_data(card_type, season, name, output_dir):
    url = f"https://rules.art/card/{name}-season-{season}-{card_type}"
    _, table_text = fetch_data_from_url(url)
    df = process_table_text(table_text)
    fp = Path(output_dir, f'{card_type}', f'{season}', f'{name}.csv')
    if not fp.is_file():
        fp.parent.mkdir(exist_ok=True, parents=True)
        df.to_csv(fp, index=False)
    else:
        df_old = pd.read_csv(fp)
        df = pd.concat([df, df_old], ignore_index=True)
        df = df.drop_duplicates([])
        df.to_csv(fp, index=False)


def update_db(card_types, seasons, names, output_dir):
    for ct in card_types:
        for s in seasons:
            for n in names:
                update_data(ct, s, n, output_dir)


def plot_data_plt(card_type, season, name, db_dir, last_n: Optional[int] = None):
    fp = Path(db_dir, f'{card_type}', f'{season}', f'{name}.csv')
    df = pd.read_csv(fp)

    if last_n:
        df = df.head(last_n)

    prices = df.price.values
    avg_price = np.mean(prices)
    std_price = statistics.stdev(prices)
    serial_numbers = df.serial_number.values

    p = np.poly1d(np.polyfit(range(len(df)), prices, 2))

    fig, ax = plt.subplots(1,2, figsize=(10,5), sharey=True)
    fig.suptitle(f'{name.title()} {card_type.title()} (last {len(df)} sales)')

    ax[0].plot(range(len(df)), prices, marker='+')
    ax[0].plot(range(len(df)), p(range(len(df))), color='#28DED8', linestyle=':')
    ax[0].axhline(y=avg_price, color='r', linestyle='-', label=f'$\mathrm{{p}}_{{avg}}$={round(avg_price,2)}€ ± {round(std_price,2)}')
    ax[0].set_xticks([],[])
    yticks = [float(y.get_position()[1]) for y in ax[0].get_yticklabels()]
    yticks_labs = [f'{y.get_text()}€' for y in ax[0].get_yticklabels()]
    ax[0].set_yticks(yticks, labels=yticks_labs)
    ax[0].set_ylabel('price')
    ax[0].legend()

    ax[1].scatter(serial_numbers, prices, alpha=0.5)
    ax[1].set_xlabel('card number')

    plt.show()


def plot_data_plotly(card_type, season, name, db_dir, img_dir, last_n: Optional[int] = None):
    fp = Path(db_dir, f'{card_type}', f'{season}', f'{name}.csv')
    df = pd.read_csv(fp)

    if last_n:
        df = df.head(last_n)

    prices = df.price.values
    avg_price = np.mean(prices)
    std_price = statistics.stdev(prices)
    serial_numbers = df.serial_number.values

    hovertext = [f'{round(price,2)}€<br>#{serial_number}' for price, serial_number in zip(prices, serial_numbers)]

    p = np.poly1d(np.polyfit(range(len(df)), prices, 2))

    fig = go.Figure(
        data=[
            go.Scatter(
                x=list(range(len(df))),
                y=prices,
                mode="lines+markers",
                marker=dict(
                    symbol="x",
                ),
                hovertext=hovertext,
                hoverinfo="text",
            ),
            go.Scatter(
                x=list(range(len(df))),
                y=p(range(len(df))),
                line=dict(
                    color="#28DED8",
                    dash="dot")
            ),
        ]
    )

    fig.update_layout(
        title=f'{name.title()} {card_type.title()} (last {len(df)} sales)',
        xaxis = dict(
            tickvals=[],
        ),
        yaxis = dict(
            ticksuffix="€",
        ),
    )

    img_fp = Path(img_dir, f'{card_type}', f'{season}', f'{name}.html')
    if not img_fp.parent.exists():
        img_fp.parent.mkdir(parents=True)
    fig.write_html(img_fp)
    return fig