"""
Compile colors and variants into single YAML theme file.
Created by Segilmez06
"""

from os import mkdir, listdir
from os.path import exists
from shutil import rmtree
from itertools import combinations
import yaml



# Load configuration
CONFIG = yaml.safe_load(open('config.yml', 'r', encoding='utf-8'))

OUTPUT_DIR = CONFIG['output_dir']
OUTPUT_FILE = CONFIG['output_file']

BASE_FILE = CONFIG['base_file']
COLORS_FILE = CONFIG['colors_file']

FEATURES_DIR = CONFIG['features_dir']
FEATURES_EXTENSION = CONFIG['features_extension']



# Create a fresh output directory
if exists(OUTPUT_DIR):
    rmtree(OUTPUT_DIR)
mkdir(OUTPUT_DIR)



# Read base, colors and features from files
BASE = yaml.safe_load(open(BASE_FILE, 'r', encoding='utf-8'))

COLORS: list = yaml.safe_load(open(COLORS_FILE, 'r', encoding='utf-8'))
FEATURES: list = [
    yaml.safe_load(
        open(f'{FEATURES_DIR}/{variant_file}', 'r', encoding='utf-8')
        )
    for variant_file in listdir(FEATURES_DIR)
    if variant_file.endswith(f".{FEATURES_EXTENSION}")
    ]



# Create top level stores
DOCUMENT: dict[str, dict] = {}

FEATURE_COMBINATIONS: list = []



# Generate all possible combinations of features
for i in range(len(FEATURES) + 1):
    FEATURE_COMBINATIONS.extend(list(combinations(FEATURES, i)))



# Generate all possible variants
# Iterate through color schemes
for color in COLORS:
    # Iterate through feature combinations
    for combination_ in FEATURE_COMBINATIONS:
        # Calculate variant id
        VARIANT_ID = sum(pow(2, j['id']) for j in combination_)



        # Generate variant name: <Emoji> <Scheme Name> - <ID> <Desc Letters>
        VARIANT_NAME = ' '.join([
            color['icon'],
            color['name'],
            f"- {VARIANT_ID:02d}",
            f"({'Vanilla' if VARIANT_ID == 0 else ''.join([j['desc'] for j in combination_])})"
        ])



        # Generate card-mod vars data store
        card_mod_vars_data: dict[str, dict] = {}
        # Iterate through features
        for feature in combination_:
            # Iterate through data inside feature file
            for fkey, fvalue in feature.items():
                # If the key is card_mod
                if fkey == 'card_mod':
                    # Iterate through data inside card_mod (view - root - more-info)
                    for ckey, cvalue in fvalue.items():
                        # Iterate through data inside spec (abc$ shadow root)
                        for key, value in cvalue.items():
                            k = f"card-mod-{ckey}"
                            if k not in card_mod_vars_data:
                                card_mod_vars_data[k] = {}
                            card_mod_vars_data[k][key] = card_mod_vars_data[k].get(key, '') + value

        # Generate variant data store
        VARIANT: dict = {
            VARIANT_NAME: {
                # Colors
                **{
                    f"c-rgb-{key}": ', '.join(str(c) for c in value)
                    for key, value in color['colors'].items()
                },

                # Base style assignments
                **BASE,

                # Light/Dark theme and identifier vars
                **{
                    "modes": {
                        mode: {
                            "sarp-theme-variant": '-'.join([
                                str(color['name']).lower(),
                                str(VARIANT_ID).lower(),
                                mode
                            ])
                        }
                        for mode in ["light", "dark"]
                    }
                },

                # Styles from features
                **{
                    key: value
                    for c in combination_
                    if 'vars' in c
                    for key, value in c['vars'].items()
                },

                # Init card-mod theme
                "card-mod-theme": VARIANT_NAME,

                # Card-mod styles from features
                **{
                    key: yaml.dump(value, sort_keys=False).strip()
                    for key, value in card_mod_vars_data.items()
                }
            }
        }



        # Add variant to master document
        DOCUMENT.update(VARIANT)



# Write the compiled theme to a file
yaml.dump(
    DOCUMENT,
    sort_keys=False,
    stream=open(
        f'{OUTPUT_DIR}/{OUTPUT_FILE}',
        'w',
        encoding='utf-8'
    )
)
