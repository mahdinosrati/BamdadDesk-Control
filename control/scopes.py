import json

from fastapi import HTTPException


def group_allowed(admin, group_id):
    return admin.get('groups') is None or group_id in admin['groups']


def require_group(admin, group_id):
    if not group_allowed(admin, group_id):
        raise HTTPException(404, 'Resource not found in your scope')


def require_global(admin):
    if admin.get('groups') is not None:
        raise HTTPException(403, 'Organization-wide administrator required')


def device_in_scope(db, admin, device_id):
    row = db.execute('SELECT * FROM devices WHERE id=?', (device_id,)).fetchone()
    if not row:
        raise HTTPException(404, 'Device not found')
    require_group(admin, row['group_id'])
    return dict(row)


def policy_in_scope(db, admin, scope):
    if scope == 'global':
        require_global(admin)
        return ''
    kind, _, target = scope.partition(':')
    if kind == 'device':
        return device_in_scope(db, admin, target)['group_id']
    if kind == 'group' and db.execute('SELECT 1 FROM groups WHERE id=?', (target,)).fetchone():
        require_group(admin, target)
        return target
    raise HTTPException(404, 'Policy scope not found')


def set_scope(db, identifier, groups, permissions):
    if groups is None:
        db.execute('DELETE FROM admin_scopes WHERE admin=?', (identifier,))
        return
    if len(groups) > 100 or len(groups) != len(set(groups)):
        raise HTTPException(422, 'Invalid group scope')
    if set(permissions) & {'admins.write', 'releases.write'}:
        raise HTTPException(422, 'Scoped administrators cannot manage administrators or organization-wide releases')
    for group in groups:
        if not db.execute('SELECT 1 FROM groups WHERE id=?', (group,)).fetchone():
            raise HTTPException(422, 'Unknown group in scope')
    db.execute('INSERT INTO admin_scopes VALUES (?,?) ON CONFLICT(admin) DO UPDATE SET groups_json=excluded.groups_json',
               (identifier, json.dumps(groups)))
