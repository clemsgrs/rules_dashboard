
from utils import update_db, plot_offers_data, plot_sales_data

names = ['jmks', '8ruki', 'skuna', 'thahomey', 'sheldon', 'spider-zed', 'doums', 'benjamin-epps', 'lycos', 'bigflo', 'jwles', 'jewel-usain', 'slimka', 'di-meh', 'livai', 'rowjay', 'azur', 'moji-x-sboy', 'kerchak', 'mahdi-ba', 'deen-burbigo', 'zinee']
seasons = [1]
card_types = ['common', 'halloween', 'platinium']


if __name__ == '__main__':

    name = "zinee"
    season = 1
    card_type = "platinium"

    # update_db([card_type], [season], [name], output_dir='output')

    f1 = plot_sales_data(card_type, season, name, db_dir='output', img_dir='dashboards')
    f2 = plot_offers_data(card_type, season, name, db_dir='output', img_dir='dashboards')
    f1.show()
    f2.show()
