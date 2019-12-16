from .partition import split_into_header_table
from .table import decode_rows


def detect_cli(args):
    detect_file_encoding(args.filepath)


def detect_file_encoding(filepath):
    with open(filepath, "rb") as file:
        trf_contents = file.read()

    _, trf_table_contents = split_into_header_table(trf_contents)
    possible_groupings = search_for_possible_decoding_options(trf_table_contents)

    return possible_groupings


def search_for_possible_decoding_options(trf_table_contents):
    line_grouping_range = range(600, 900)
    linac_state_codes_column_range = range(0, 20)

    possible_groupings = []

    for line_grouping in line_grouping_range:
        for linac_state_codes_column in linac_state_codes_column_range:
            try:
                decode_rows(
                    trf_table_contents,
                    input_line_grouping=line_grouping,
                    input_linac_state_codes_column=linac_state_codes_column,
                )
                possible_groupings.append([line_grouping, linac_state_codes_column])
            except ValueError:
                pass

    return possible_groupings
