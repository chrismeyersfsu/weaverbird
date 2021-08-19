from distutils import log

from weaverbird.backends.sql_translator.steps.utils.query_transformation import (
    build_selection_query,
    snowflake_date_format,
)
from weaverbird.backends.sql_translator.types import (
    SQLPipelineTranslator,
    SQLQuery,
    SQLQueryDescriber,
    SQLQueryRetriever,
)
from weaverbird.pipeline.steps import ToDateStep


def translate_todate(
    step: ToDateStep,
    query: SQLQuery,
    index: int,
    sql_query_retriever: SQLQueryRetriever = None,
    sql_query_describer: SQLQueryDescriber = None,
    sql_translate_pipeline: SQLPipelineTranslator = None,
) -> SQLQuery:
    query_name = f'TODATE_STEP_{index}'

    log.debug(
        '############################################################'
        f'query_name: {query_name}\n'
        '------------------------------------------------------------'
        f'step.name: {step.name}\n'
        f'step.column: {step.column}\n'
        f'step.format: {step.format}\n'
        f'query.transformed_query: {query.transformed_query}\n'
        f'query.metadata_manager.query_metadata: {query.metadata_manager.retrieve_query_metadata()}\n'
    )
    step.format = snowflake_date_format(step.format)
    # we change the column type
    query.metadata_manager.update_query_metadata_column_type(step.column, 'date')

    completed_fields = query.metadata_manager.retrieve_query_metadata_columns_as_str(
        columns_filter=[step.column]
    )
    # we escape quotes here and construct our format
    step.format = None if step.format is None else step.format.replace('"', "").replace("'", "")
    step.format = "" if step.format is None else f", '{step.format}'"
    new_query = SQLQuery(
        query_name=query_name,
        transformed_query=f"""{query.transformed_query}, {query_name} AS"""
<<<<<<< HEAD
        f""" (SELECT {completed_fields},"""
        f""" TRY_TO_DATE({step.column}{step.format}) AS {step.column}"""
=======
        f""" (SELECT {complete_fields(columns=[step.column], query=query)},"""
        f""" TO_DATE({step.column}{step.format}) AS {step.column}"""
>>>>>>> feat(vqb): update utils on format date + adding tests
        f""" FROM {query.query_name}) """,
        selection_query=build_selection_query(
            query.metadata_manager.retrieve_query_metadata_columns(), query_name
        ),
        metadata_manager=query.metadata_manager,
    )

    log.debug(
        '------------------------------------------------------------'
        f'SQLquery: {new_query.transformed_query}'
        '############################################################'
    )

    return new_query
