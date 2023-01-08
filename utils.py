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


def fetch_sales_from_url(url: str):
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(4)
    card_name = driver.find_element(By.XPATH, "//* [@id='__next']/main/div[2]/div[2]/div[1]/div[1]").text
    table_text = driver.find_element(By.XPATH, "//* [@id='__next']/main/div[3]").text
    return card_name, table_text


def fetch_offers_from_url(url: str):
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(4)
    table_text = driver.find_element(By.XPATH, "//* [@id='__next']/main/div[2]").text
    return table_text


def process_sales_table(table_text):
    t = list(table_text.split('\n')[7:])
    d = defaultdict(list)
    for i in range(0, len(t), 5):
        buyer, seller, date, serial_number, price = t[len(t)-i-5], t[len(t)-i-4], t[len(t)-i-3], t[len(t)-i-2], t[len(t)-i-1]
        p = float(price[:-1])
        sn = int(serial_number[1:])
        d['buyer'].append(buyer)
        d['seller'].append(seller)
        d['date'].append(date)
        d['serial_number'].append(sn)
        d['price'].append(p)
    df = pd.DataFrame.from_dict(d)
    # df['date'] = pd.to_datetime(df.date)
    return df


def process_offers_table(table_text):
    t = list(table_text.split('\n')[5:-4])
    d = defaultdict(list)
    for i in range(0, len(t), 4):
        eth, eur, serial_number, seller = t[len(t)-i-4], t[len(t)-i-3], t[len(t)-i-2], t[len(t)-i-1]
        price = float(eur[:-1])
        sn = int(serial_number[1:])
        d['seller'].append(seller)
        d['serial_number'].append(sn)
        d['price'].append(price)
    df = pd.DataFrame.from_dict(d)
    df = df.sort_values(by='serial_number')
    return df


def update_data(card_type, season, name, output_dir):
    url = f"https://rules.art/card/{name}-season-{season}-{card_type}"
    offers_url = f"{url}/buy"
    _, sales_text = fetch_sales_from_url(url)
    offers_text = fetch_offers_from_url(offers_url)
    sales_df = process_sales_table(sales_text)
    offers_df = process_offers_table(offers_text)
    sales_fp = Path(output_dir, 'sales', f'{card_type}', f'{season}', f'{name}.csv')
    offers_fp = Path(output_dir, 'offers', f'{card_type}', f'{season}', f'{name}.csv')
    if not sales_fp.is_file():
        sales_fp.parent.mkdir(exist_ok=True, parents=True)
        sales_df.to_csv(sales_fp, index=False)
    else:
        sales_df_old = pd.read_csv(sales_fp)
        sales_df = pd.concat([sales_df, sales_df_old], ignore_index=True)
        sales_df = sales_df.drop_duplicates()
        sales_df.to_csv(sales_fp, index=False)
    if not offers_fp.is_file():
        offers_fp.parent.mkdir(exist_ok=True, parents=True)
        offers_df.to_csv(offers_fp, index=False)
    else:
        offers_df_old = pd.read_csv(offers_fp)
        offers_df = pd.concat([offers_df, offers_df_old], ignore_index=True)
        offers_df = offers_df.drop_duplicates()
        offers_df.to_csv(offers_fp, index=False)


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


def plot_sales_data(card_type, season, name, db_dir, img_dir, last_n_sales: Optional[int] = None):
    sales_fp = Path(db_dir, 'sales', f'{card_type}', f'{season}', f'{name}.csv')
    sales_df = pd.read_csv(sales_fp)

    if last_n_sales:
        sales_df = sales_df.head(last_n_sales)

    prices = sales_df.price.values
    avg_price = np.mean(prices)
    std_price = statistics.stdev(prices)
    buyers, sellers = sales_df.buyer.values, sales_df.seller.values
    serial_numbers = sales_df.serial_number.values

    xtext = [f'#{serial_number}' for serial_number in serial_numbers]
    hovertext = [f'{round(price,2)}€<br>#{serial_number}<br>buyer: {buyer}<br>seller: {seller}' for price, serial_number, buyer, seller in zip(prices, serial_numbers, buyers, sellers)]

    p = np.poly1d(np.polyfit(range(len(sales_df)), prices, 2))

    fig = go.Figure(
        data=[
            go.Scatter(
                x=list(range(len(sales_df))),
                y=prices,
                mode="lines+markers",
                marker=dict(
                    symbol="x",
                ),
                hovertext=hovertext,
                hoverinfo="text",
                name='price'
            ),
            go.Scatter(
                x=list(range(len(sales_df))),
                y=p(range(len(sales_df))),
                line=dict(
                    color="#28DED8",
                    dash="dot",
                ),
                name='trend'
            ),
        ]
    )

    fig.update_layout(
        title=f'{name.title()} {card_type.title()} (last {len(sales_df)} sales)',
        xaxis = dict(
            tickvals=list(range(len(sales_df))),
            ticktext=xtext,
        ),
        yaxis = dict(
            ticksuffix="€",
        ),
    )

    img_fp = Path(img_dir, 'sales', f'{card_type}', f'{season}', f'{name}.html')
    if not img_fp.parent.exists():
        img_fp.parent.mkdir(parents=True)
    fig.write_html(img_fp)
    return fig


def plot_offers_data(card_type, season, name, db_dir, img_dir):
    offers_fp = Path(db_dir, 'offers', f'{card_type}', f'{season}', f'{name}.csv')
    offers_df = pd.read_csv(offers_fp)

    prices = offers_df.price.values
    sellers = offers_df.seller.values
    serial_numbers = offers_df.serial_number.values

    xtext = [f'#{serial_number}' for serial_number in serial_numbers]
    hovertext = [f'{round(price,2)}€<br>#{serial_number}<br>seller: {seller}' for price, serial_number, seller in zip(prices, serial_numbers, sellers)]

    fig = go.Figure(
        data=[
            go.Scatter(
                x=list(range(len(offers_df))),
                y=prices,
                mode="markers",
                marker=dict(
                    symbol="circle",
                    size=10,
                ),
                hovertext=hovertext,
                hoverinfo="text",
                name='offers'
            ),
        ]
    )

    fig.update_layout(
        title=f'{name.title()} {card_type.title()} Offers',
        xaxis = dict(
            tickvals=list(range(len(offers_df))),
            ticktext=xtext,
        ),
        yaxis = dict(
            ticksuffix="€",
        ),
    )

    img_fp = Path(img_dir, 'offers', f'{card_type}', f'{season}', f'{name}.html')
    if not img_fp.parent.exists():
        img_fp.parent.mkdir(parents=True)
    fig.write_html(img_fp)
    return fig