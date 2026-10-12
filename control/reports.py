import csv
import io
import time
from datetime import date, datetime, time as day_time, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from .scopes import device_in_scope, require_group


def router(store, require):
    routes = APIRouter()

    @routes.get('/api/reports/connections')
    def report(start: date | None = None, end: date | None = None,
               search: str = Query('', max_length=100), device_id: str = '', group_id: str | None = None,
               kind: Literal['', 'opened', 'authorized', 'closed'] = '',
               page: int = Query(1, ge=1), export: bool = False, admin=Depends(require('audit.read'))):
        first = int(datetime.combine(start, day_time.min, timezone.utc).timestamp()) if start else 0
        last = int(datetime.combine(end, day_time.max, timezone.utc).timestamp()) if end else int(time.time())
        if last < first:
            raise HTTPException(422, 'End date must not precede start date')
        clauses, values = ['e.occurred>=?', 'e.occurred<=?'], [first, last]
        if group_id is not None:
            require_group(admin, group_id)
            clauses.append('e.group_id=?')
            values.append(group_id)
        if device_id:
            with store.connect() as db:
                device_in_scope(db, admin, device_id)
            clauses.append('e.device=?')
            values.append(device_id)
        if kind:
            clauses.append('e.kind=?')
            values.append(kind)
        if search:
            clauses.append("instr(lower(d.name||' '||e.peer_name||' '||e.peer_id||' '||e.peer_ip||' '||e.session_id),lower(?))>0")
            values.append(search)
        if admin['groups'] is not None:
            marks = ','.join('?' for _ in admin['groups']) or 'NULL'
            clauses.extend([f'e.group_id IN ({marks})', f'd.group_id IN ({marks})'])
            values.extend(admin['groups']); values.extend(admin['groups'])
        query = "SELECT e.*,d.name AS device_name,CASE WHEN e.kind='closed' THEN e.occurred-(SELECT MIN(a.occurred) FROM connection_events a WHERE a.device=e.device AND a.session_id=e.session_id AND a.group_id=e.group_id AND a.kind='authorized' AND a.occurred<=e.occurred) END AS duration_seconds FROM connection_events e JOIN devices d ON d.id=e.device WHERE " + ' AND '.join(clauses)
        if export:
            def rows():
                output = io.StringIO()
                writer = csv.writer(output)
                fields = ['occurred', 'device_name', 'kind', 'peer_name', 'peer_id', 'peer_ip', 'session_id', 'duration_seconds']
                yield '\ufeff'
                writer.writerow(fields)
                yield output.getvalue()
                with store.connect() as db:
                    for row in db.execute(query + ' ORDER BY e.id DESC', values):
                        output.seek(0); output.truncate(0)
                        cells = [row[key] for key in fields]
                        # Spreadsheet programs interpret untrusted peer names as formulas.
                        writer.writerow(["'" + cell if isinstance(cell, str) and cell.lstrip().startswith(('=', '+', '-', '@')) else cell for cell in cells])
                        yield output.getvalue()
            return StreamingResponse(rows(), media_type='text/csv; charset=utf-8', headers={'Content-Disposition': 'attachment; filename="connections.csv"'})
        with store.connect() as db:
            summary = dict(db.execute('SELECT COUNT(*) AS events,SUM(kind=\'authorized\') AS authorized,SUM(kind=\'closed\') AS closed,COALESCE(SUM(duration_seconds),0) AS duration_seconds FROM (' + query + ')', values).fetchone())
            events = [dict(r) for r in db.execute(query + ' ORDER BY e.id DESC LIMIT 100 OFFSET ?', (*values, (page - 1) * 100))]
        return {'summary': summary, 'events': events, 'page': page, 'pages': max(1, (summary['events'] + 99) // 100), 'timezone': 'UTC'}

    return routes
