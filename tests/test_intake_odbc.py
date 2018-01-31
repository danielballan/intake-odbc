import os
import pandas as pd
import intake_odbc as odbc
from .util import mssql, pg, df0


here = os.path.dirname(__file__)
os.environ['ODBCSYSINI'] = os.path.join(here, '..', 'examples')


def test_mssql_minimal(mssql):
    q = 'SELECT session_id, blocking_session_id FROM sys.dm_exec_requests'
    s = odbc.ODBCSource(
        uri=None, sql_expr=q,
        odbc_kwargs=mssql,
        metadata={})
    disc = s.discover()
    assert list(disc['dtype']) == ['session_id', 'blocking_session_id']
    data = s.read()
    assert len(data)


def test_mssql_part_minimal(mssql):
    args = mssql.copy()
    args.update(dict(index='session_id', npartitions=2))
    q = 'SELECT session_id, blocking_session_id FROM sys.dm_exec_requests'
    s = odbc.ODBCPartitionedSource(
        uri=None, sql_expr=q,
        odbc_kwargs=args,
        metadata={})
    disc = s.discover()
    assert list(disc['dtype']) == ['session_id', 'blocking_session_id']
    assert s.npartitions == 2
    data = s.read()
    assert len(data)
    part1, part2 = s.read_partition(0), s.read_partition(1)
    assert data.equals(pd.concat([part1, part2], ignore_index=True))
    assert data.equals(pd.concat(s.read_chunked(), ignore_index=True))


def test_engines(mssql, pg):
    for kwargs in [mssql, pg]:
        q = "SELECT * from testtable"
        with odbc.ODBCSource(uri=None, sql_expr=q, odbc_kwargs=kwargs,
                             metadata={}) as s:
            # needs auto-close if container might disappear on completion
            df = s.read()
            assert df.equals(df0.reset_index())


def test_pg_simple(pg):
    q = "SELECT * FROM pg_database"
    s = odbc.ODBCSource(uri=None, sql_expr=q, odbc_kwargs=pg,
                        metadata={})
    out = s.read()
    assert 'datname' in out.columns
