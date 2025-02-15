from typing import Dict

from ..types import SQLStepTranslator
from .aggregate import translate_aggregate
from .convert import translate_convert
from .filter import translate_filter
from .formula import translate_formula
from .fromdate import translate_fromdate
from .ifthenelse import translate_ifthenelse
from .join import translate_join
from .lowercase import translate_lowercase
from .rename import translate_rename
from .replace import translate_replace
from .select import translate_select
from .sort import translate_sort
from .table import translate_table
from .text import translate_text
from .todate import translate_todate
from .top import translate_top
from .uniquegroups import translate_uniquegroups
from .unpivot import translate_unpivot
from .uppercase import translate_uppercase

sql_steps_translators: Dict[str, SQLStepTranslator] = {
    'domain': translate_table,  # type ignore # TODO to update
    'filter': translate_filter,
    'aggregate': translate_aggregate,
    'select': translate_select,
    'ifthenelse': translate_ifthenelse,
    'sort': translate_sort,
    'rename': translate_rename,
    'convert': translate_convert,
    'text': translate_text,
    'lowercase': translate_lowercase,
    'uppercase': translate_uppercase,
    'fromdate': translate_fromdate,
    'todate': translate_todate,
    'formula': translate_formula,
    'replace': translate_replace,
    'join': translate_join,
    'uniquegroups': translate_uniquegroups,
    'top': translate_top,
    'join': translate_join,
    'unpivot': translate_unpivot,
}
