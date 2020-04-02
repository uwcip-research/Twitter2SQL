import csv

from psycopg2 import sql
from collections import defaultdict


class sql_statement(object):

    def __init__(self):

        """ There's some repeated code in these sql_statements. Think about
            putting into a class.
        """

        return


def not_null_statement(table_name, where_col, select=None, distinct=None):

    """ Requires you to fill in the dates in a subsequent step.
        Think about how to do this in a simple way.
    """

    if select is None:
        select = sql.Identifier('*')
    elif type(select) is list:
        select = sql.SQL(', ').join([sql.Identifier(item) for item in select])
    else:
        select = sql.Identifier(select)
    
    if distinct is None:
        distinct = sql.SQL('')
    else:
        distinct = sql.SQL("""DISTINCT ON ({})""").format(
            sql.Identifier(distinct))

    sql_statement = sql.SQL("""
        SELECT {distinct} {select}
        FROM {table}
        WHERE {where_col} IS NOT NULL;
        """).format(select=select, table=sql.Identifier(table_name), 
                        where_col=sql.Identifier(where_col), distinct=distinct)

    return sql_statement


def in_statement(table_name, where_col, values, select=None, distinct=None):

    """ Requires you to fill in the dates in a subsequent step.
        Think about how to do this in a simple way.
    """

    if select is None:
        select = sql.Identifier('*')
    elif type(select) is list:
        select = sql.SQL(', ').join([sql.Identifier(item) for item in select])
    else:
        select = sql.Identifier(select)
    
    if distinct is None:
        distinct = sql.SQL('')
    else:
        distinct = sql.SQL("""DISTINCT ON ({})""").format(
            sql.Identifier(distinct))

    # This is a bit suspect.
    value_string = ''
    for item in values:
        value_string += '%s,'
    value_string = sql.SQL(value_string[:-1])

    sql_statement = sql.SQL("""
        SELECT {distinct} {select}
        FROM {table}
        WHERE {where_col} in ({values});
        """).format(select=select, table=sql.Identifier(table_name), 
                        values=value_string, 
                        where_col=sql.Identifier(where_col), 
                        distinct=distinct)

    return sql_statement


def filter_date_statement(table_name, date_column='created_ts', 
                            select=None, distinct=None):

    """ Requires you to fill in the dates in a subsequent step.
        Think about how to do this in a simple way.
    """

    if select is None:
        select = '*'
    
    if distinct is None:
        distinct = ''
    else:
        distinct = sql.SQL("""DISTINCT ON ({})""").format(
            sql.Identifier(distinct))

    sql_statement = sql.SQL("""
        SELECT {distinct} {select}
        FROM {table}
        WHERE {date} BETWEEN %s AND %s
        """).format(select=sql.Identifier(select), 
                        table=sql.Identifier(table_name), 
                        date=sql.Identifier(date_column), 
                        distinct=distinct)

    return sql_statement


def filter_statement():

    """Coming soon!
    """

    return


def table_permission_statement(table_name, admins):

    """ Grants all permissions to the list of users in admins.
    """

    sql_statement = sql.SQL("""GRANT ALL ON TABLE public.{table} 
        TO""").format(table=sql.Identifier(table_name))

    for idx, admin in enumerate(admins):
        sql_statement += sql.SQL('{user}').format(user=sql.Identifier(admin))
        if idx == len(admins) - 1:
            sql_statement += sql.SQL(';')
        else:
            sql_statement += sql.SQL(',')

    return sql_statement


def drop_table_statement(table_name):

    sql_statement = """DROP TABLE {}""".format(table_name)

    return sql_statement


def create_table_statement(input_schema, table_name):

    """ A generic table create. Schemes can be either Python 
    dicts or csv files.
    """

    create_statement = "CREATE TABLE IF NOT EXISTS {} (".format(table_name)
    
    if type(input_schema) is str:

        with open(input_schema, 'r') as readfile:
            reader = csv.reader(readfile, delimiter=',')
            next(reader)  # This line skips the header row.

            for row in reader:
                create_statement += ' '.join([row[0]] + row[2:4]) + ','

    elif type(input_schema) is dict:

        for column_header, data_type in input_schema.items():
            create_statement += ' '.join([column_header] + data_type) + ','

    else:
        print()

    create_statement = create_statement[:-1] + ')'  # Replace last comma with )
    create_statement += ";"

    return create_statement


def create_col_statement(table_name, col_name, dtype="VARCHAR"):

    create_col_statement = sql.SQL("""ALTER TABLE {table}\n
        ADD COLUMN IF NOT EXISTS {col_name} {dtype};""").format(
        table=sql.Identifier(table_name),
        col_name=sql.Identifier(col_name),
        dtype=sql.SQL(dtype))

    return create_col_statement


def insert_statement(input_schema, table_name):

    """ A generic data insert. Schemes can be either Python 
    dicts or csv files.
    """

    insert_statement = sql.SQL("INSERT INTO {} (").format(
        sql.Identifier(table_name))

    if type(input_schema) is str:

        with open(input_schema, 'r') as readfile:
            reader = csv.reader(readfile, delimiter=',')
            next(reader)  # This line skips the header row.

            value_num = 0

            # This is a little broken.
            insert_values = None
            for row in reader:
                if insert_values is None:
                    insert_values = sql.Identifier(row[0])
                else:
                    insert_values += sql.Identifier(row[0])
                value_num += 1
            insert_statement += sql.SQL(",").join(insert_values.seq)

    elif type(input_schema) is dict:

        value_num = len(input_schema)
        for idx, (column_header, data_type) in enumerate(input_schema.items()):
            if idx == len(input_schema) - 1:
                insert_statement += sql.Identifier(column_header)
            else:
                insert_statement += sql.Identifier(column_header) + sql.SQL(',')

    else:
        raise ValueError("""Insert statements require either dict or str (.csv)
            as input.""")

    # Replace final comma with )
    insert_statement = insert_statement + sql.SQL(") VALUES (" )
    for i in range(value_num):
        if i == value_num - 1:
            insert_statement += sql.SQL('%s')
        else:
            insert_statement += sql.SQL('%s,')
    # Replace final comma with )
    insert_statement = insert_statement + sql.SQL(')')

    return insert_statement


def category_statement(input_table, input_schema, input_column,
                        output_column):

    sql_statement = sql.SQL("""UPDATE {table}\n""").format(
        table=sql.Identifier(input_table))

    if type(input_schema) is str:

        with open(input_schema, 'r') as readfile:
            reader = csv.reader(readfile, delimiter=',')

            category_dict = defaultdict(list)
            header = next(reader)

            for row in reader:
                for idx, item in enumerate(row):
                    category_dict[header[idx]] += [item]

    elif type(input_schema) is dict:
        raise ValueError("""Dict input not yet implemented.""")  

    else:
        raise ValueError("""Category statements require either dict or str (.csv)
            as input.""")   

    return_values = []
    for idx, (key, values) in enumerate(category_dict.items()):
        
        return_values += values
        value_string = ''
        for item in values:
            value_string += '%s,'
        value_string = sql.SQL(value_string[:-1])

        if idx == 0:
            sql_statement += sql.SQL("""SET {output} = CASE WHEN UPPER({input}) \
                IN ({values}) THEN {category}\n""").format(
                input=sql.SQL(input_column),
                output=sql.SQL(output_column),
                category=sql.Literal(key),
                values=value_string)  
        else:
            sql_statement += sql.SQL("""WHEN UPPER({input}) \
                IN ({values}) THEN {category}\n""").format(
                input=sql.SQL(input_column),
                output=sql.Identifier(output_column),
                category=sql.Literal(key),
                values=value_string)  
        
        if idx == len(header) - 1:
            sql_statement += sql.SQL("""ELSE \
                {category}\nEND""").format(
                input=sql.Identifier(input_column),
                output=sql.Identifier(output_column),
                category=sql.Literal('null'),
                values=value_string)  

    return sql_statement, return_values