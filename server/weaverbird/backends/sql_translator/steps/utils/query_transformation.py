import re
from typing import Dict

from weaverbird.backends.sql_translator.metadata import ColumnMetadata
from weaverbird.backends.sql_translator.types import SQLQuery
from weaverbird.pipeline.conditions import (
    ComparisonCondition,
    Condition,
    ConditionComboAnd,
    ConditionComboOr,
    InclusionCondition,
    MatchCondition,
    NullCondition,
)

SQL_COMPARISON_OPERATORS = {
    'eq': '=',
    'ne': '!=',
    'lt': '<',
    'le': '<=',
    'gt': '>',
    'ge': '>=',
}

SQL_NULLITY_OPERATORS = {
    'isnull': 'IS NULL',
    'notnull': 'IS NOT NULL',
}

SQL_MATCH_OPERATORS = {
    'matches': 'RLIKE',
    'notmatches': 'NOT RLIKE',
}

SQL_INCLUSION_OPERATORS = {
    'in': 'IN',
    'nin': 'NOT IN',
}


def apply_condition(condition: Condition, query: str) -> str:
    if isinstance(condition, ComparisonCondition):
        try:
            float(condition.value)
            query += f'{condition.column} {SQL_COMPARISON_OPERATORS[condition.operator]} {condition.value}'
        except ValueError:
            # just to escape single quotes from crashing the snowflakeSQL query
            if type(condition.value) == str:
                condition.value = condition.value.replace('"', '\\"').replace("'", "\\'")
            query += f"{condition.column} {SQL_COMPARISON_OPERATORS[condition.operator]} '{condition.value}'"
    elif isinstance(condition, NullCondition):
        query += f'{condition.column} {SQL_NULLITY_OPERATORS[condition.operator]}'
    elif isinstance(condition, MatchCondition):
        # just to escape single quotes from crashing the snowflakeSQL query
        if type(condition.value) == str:
            condition.value = condition.value.replace('"', '\\"').replace("'", "\\'")
        query += f"{condition.column} {SQL_MATCH_OPERATORS[condition.operator]} '{condition.value}'"
    elif isinstance(condition, InclusionCondition):
        query += f'{condition.column} {SQL_INCLUSION_OPERATORS[condition.operator]} {str(tuple(condition.value))}'
    elif isinstance(condition, ConditionComboAnd):
        query = apply_condition(condition.and_[0], query)
        for c in condition.and_[1:]:
            query = apply_condition(c, f'{query} AND ')
    elif isinstance(condition, ConditionComboOr):
        query = apply_condition(condition.or_[0], query)
        for c in condition.or_[1:]:
            query = apply_condition(c, f'{query} OR ')
    else:
        raise NotImplementedError('Only comparison conditions are implemented')
    return query


def build_selection_query(query_metadata: Dict[str, ColumnMetadata], query_name) -> str:
    names = []
    for _, metadata in query_metadata.items():
        alias = getattr(metadata, 'alias')
        if alias:
            names.append(alias)
        else:
            names.append(getattr(metadata, 'name'))
    return f"SELECT {', '.join(names)} FROM {query_name}"


def build_first_or_last_aggregation(aggregated_string, first_last_string, query, step):
    first_cols, last_cols = [], []
    for aggregation in [
        aggregation
        for aggregation in step.aggregations
        if aggregation.agg_function in ['first', 'last']
    ]:
        for col, new_col in zip(aggregation.columns, aggregation.new_columns):
            if aggregation.agg_function == 'first':
                first_cols.append((col, new_col))
            else:
                last_cols.append((col, new_col))
    if len(first_cols) and not len(last_cols):
        if len(step.on):
            firsts_query = (
                f"SELECT {', '.join([f'{col} AS {new_col}' for (col, new_col) in first_cols] + step.on + ['ROW_NUMBER()'])} OVER (PARTITION BY {', '.join(step.on)} "
                f"ORDER BY {', '.join([c[0] for c in first_cols])}) AS R FROM {query.query_name} QUALIFY R = 1"
            )
            first_last_string = f"SELECT {', '.join([f'{c[1]}' for c in first_cols] + step.on)} FROM ({firsts_query})"

        else:
            firsts_query = (
                f"SELECT {', '.join(step.on + [f'{col} AS {new_col}' for (col, new_col) in first_cols] + ['ROW_NUMBER()'])} OVER ("
                f"ORDER BY {', '.join([c[0] for c in first_cols])}) AS R FROM {query.query_name} QUALIFY R = 1"
            )

            first_last_string = (
                f"SELECT {', '.join([f'{c[1]}' for c in first_cols])} FROM ({firsts_query})"
            )
    if len(last_cols) and not len(first_cols):
        if len(step.on):
            lasts_query = (
                f"SELECT {', '.join([f'{col} AS {new_col}' for (col, new_col) in last_cols] + step.on + ['ROW_NUMBER()'])} OVER (PARTITION BY {', '.join(step.on)} "
                f"ORDER BY {', '.join([f'{c[0]} DESC' for c in last_cols])}) AS R FROM {query.query_name} QUALIFY R = 1"
            )
            first_last_string = (
                f"SELECT {', '.join([f'{c[1]}' for c in last_cols] + step.on)} FROM ({lasts_query})"
            )

        else:
            lasts_query = (
                f"SELECT {', '.join(step.on + [f'{col} AS {new_col}' for (col, new_col) in last_cols] + ['ROW_NUMBER()'])} OVER ("
                f"ORDER BY {', '.join([f'{c[0]} DESC' for c in last_cols])}) AS R FROM {query.query_name} QUALIFY R = 1"
            )
            first_last_string = (
                f"SELECT {', '.join([f'{c[1]}' for c in last_cols])} FROM ({lasts_query})"
            )
    if len(last_cols) and len(first_cols):
        if len(step.on):
            firsts_and_lasts_query = (
                f"SELECT {', '.join([f'{col} AS {new_col}' for (col, new_col) in first_cols] + [f'{col} AS {new_col}' for (col, new_col) in last_cols] + step.on + ['ROW_NUMBER()'])} OVER (PARTITION BY {', '.join(step.on)} "
                f"ORDER BY {', '.join([f'{c[0]}' for c in first_cols] + [f'{c[0]} DESC' for c in last_cols])}) AS R FROM {query.query_name} QUALIFY R = 1"
            )
            first_last_string = f"SELECT {', '.join([f'{c[1]}' for c in first_cols] + [f'{c[1]}' for c in last_cols] + step.on)} FROM ({firsts_and_lasts_query})"

        else:
            firsts_and_lasts_query = (
                f"SELECT {', '.join(step.on + [f'{col} AS {new_col}' for (col, new_col) in first_cols] + [f'{col} AS {new_col}' for (col, new_col) in last_cols] + ['ROW_NUMBER()'])} OVER ("
                f"ORDER BY {', '.join([f'{c[0]}' for c in first_cols] + [f'{c[0]} DESC' for c in last_cols])}) AS R FROM {query.query_name} QUALIFY R = 1"
            )
            first_last_string = f"SELECT {', '.join([f'{c[1]}' for c in first_cols] + [f'{c[1]}' for c in last_cols])} FROM ({firsts_and_lasts_query})"
    if len(aggregated_string) and len(first_last_string):
        if len(step.on):
            query_string = f"SELECT A.*, {', '.join([f'F.{c[1]}' for c in first_cols + last_cols])} FROM ({aggregated_string}) A INNER JOIN ({first_last_string}) F ON {' AND '.join([f'A.{s}=F.{s}' for s in step.on])}"
        else:
            query_string = f"SELECT A.*, {', '.join([f'F.{c[1]}' for c in first_cols + last_cols])} FROM ({aggregated_string}) A INNER JOIN ({first_last_string}) F"

    elif len(aggregated_string):
        query_string = aggregated_string
    else:
        query_string = first_last_string
    return query_string


def prepare_aggregation_query(aggregated_cols, aggregated_string, query, step):
    for agg in step.aggregations:  # TODO the front should restrict - usage in column names
        agg.new_columns = [x.replace('-', '_').replace(' ', '_') for x in agg.new_columns]
    for aggregation in [
        aggregation
        for aggregation in step.aggregations
        if aggregation.agg_function not in ['first', 'last']
    ]:
        for col, new_col in zip(aggregation.columns, aggregation.new_columns):
            if aggregation.agg_function == 'count distinct':
                aggregated_cols.append(f'COUNT(DISTINCT {col}) AS {new_col}')
            else:
                aggregated_cols.append(f'{aggregation.agg_function.upper()}({col}) AS {new_col}')
    if len(step.on) and len(aggregated_cols):
        aggregated_cols += step.on
        aggregated_string = f"SELECT {', '.join(aggregated_cols)} FROM {query.query_name} GROUP BY {', '.join(step.on)}"
    elif len(aggregated_cols):
        aggregated_string = f"SELECT {', '.join(aggregated_cols)} FROM {query.query_name}"
    return aggregated_string


def complete_fields(query: SQLQuery, columns=None) -> str:
    """
    We're going to complete missing field from the query
    """
    # TODO : changes the management columns on joins with duplicated columns
    query_keys = query.metadata_manager.query_metadata.keys()
    if columns:
        compiled_query = ', '.join(
            [
                k.strip().replace('-', '_').replace(' ', '').upper()
                for k in query_keys
                if k.upper() not in columns and k.lower() not in columns
            ]
        )
    else:
        compiled_query = ', '.join(query_keys)

    return compiled_query


def snowflake_date_format(input_format: str) -> str:
    """
    This method will format the standard sql format for dates into snowflake sql one
    """
    # we escape quotes here and construct our format
    # for a valid snowflake date format
    input_format = (
        None
        if input_format is None or input_format == ''
        else input_format.replace('"', '')
        .replace("'", '')
        .replace('%b', 'MON')
        .replace('%B', 'MMMM')
        .replace('%y', 'YYYY')
        .replace('%Y', 'YYYY')
        .replace('%M', 'MM')
        .replace('%m', 'MM')
        .replace('%D', 'DD')
        .replace('%d', 'DD')
    )
    input_format = '' if input_format is None or input_format == '' else f", '{input_format}'"

    return input_format


def handle_zero_division(formula: str) -> str:
    """
    Use regular expression replacement to detect '/' or '%' in formulas
    and substitute a 0 divisor by NULL
    For example in '1 % BLAAA / "BLA    BLA"'
    this r'(?<=%)\s*(\w+)' captures BLAAA and this r' NULLIF(\1, 0)' replaces it
    by NULLIF(BLAAA, 0).
    this r'(?<=/)\s*(\"?.*\"?)' captures "BLA    BLA" and this r'NULLIFF(\2, 0)' replaces it
    by NULLIF("BLA    BLA", 0).
    """
    if '/' not in formula and '%' not in formula:
        return formula
    if '/' in formula:
        formula = re.sub(r'(?<=/)\s*(\w+)|(?<=/)\s*(\"?.*\"?)', r' NULLIF(\1\2, 0)', formula)
    if '%' in formula:
        formula = re.sub(r'(?<=%)\s*(\w+)|(?<=%)\s*(\"?.*\"?)', r' NULLIF(\1\2, 0)', formula)
    return formula
