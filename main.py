
from utils import update_db, plot_data_plt, plot_data_plotly

names = ['jmks', '8ruki', 'skuna', 'thahomey', 'sheldon', 'spider-zed', 'doums', 'benjamin-epps', 'lycos', 'bigflo', 'jwles', 'jewel-usain', 'slimka', 'di-meh', 'livai', 'rowjay', 'azur', 'moji-x-sboy', 'kerchak', 'mahdi-ba', 'deen-burbigo', 'zinee']
seasons = [1]
card_types = ['common', 'halloween', 'platinium']

name = "zinee"
season = 1
card_type = "common"

update_db([card_type], [season], [name], output_dir='output')

f = plot_data_plotly(card_type, season, name, db_dir='output', img_dir='dashboards')
f.show()