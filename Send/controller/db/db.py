#!/usr/bin/env python3
import os, sqlite3, json, datetime, hashlib
from typing import List, Optional, Dict, Any

class DB:
    def __init__(self, path: str):
        self.path = path
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "CREATE TABLE IF NOT EXISTS tokens ("
                " token_name TEXT PRIMARY KEY,"
                " token_hash TEXT NOT NULL,"
                " role TEXT NOT NULL,"
                " description TEXT,"
                " created_at TEXT,"
                " revoked INTEGER DEFAULT 0)"
            )
            c.execute(
                "CREATE TABLE IF NOT EXISTS agents ("
                " agent_name TEXT PRIMARY KEY,"
                " host TEXT,"
                " port INTEGER,"
                " status TEXT,"
                " capabilities_json TEXT,"
                " metadata_json TEXT,"
                " last_seen TEXT)"
            )
            c.execute(
                "CREATE TABLE IF NOT EXISTS scripts ("
                " script_id TEXT PRIMARY KEY,"
                " script_file TEXT NOT NULL,"
                " description TEXT,"
                " allowed_tags_json TEXT,"
                " required_approval_levels INTEGER DEFAULT 1)"
            )
            c.execute(
                "CREATE TABLE IF NOT EXISTS workflows ("
                " workflow_id TEXT PRIMARY KEY,"
                " script_id TEXT,"
                " targets_json TEXT,"
                " requestor TEXT,"
                " status TEXT,"
                " required_approval_levels INTEGER,"
                " approvals_json TEXT,"
                " notify_email TEXT,"
                " reason TEXT,"
                " created_at TEXT,"
                " expires_at TEXT,"
                " last_update TEXT)"
            )
            c.execute(
                "CREATE TABLE IF NOT EXISTS workflow_audit ("
                " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " workflow_id TEXT,"
                " action TEXT,"
                " actor TEXT,"
                " ts TEXT,"
                " note TEXT)"
            )
            conn.commit()

    # Token methods
    def create_token(self, token_name: str, token_plain: str, role: str, description: str = ""):
        now = datetime.datetime.utcnow().isoformat() + "Z"
        h = hashlib.sha256(token_plain.encode()).hexdigest()
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "REPLACE INTO tokens (token_name, token_hash, role, description, created_at, revoked)"
                " VALUES (?,?,?,?,?,0)",
                (token_name, h, role, description, now),
            )
            conn.commit()

    def revoke_token(self, token_name: str):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("UPDATE tokens SET revoked=1 WHERE token_name=?", (token_name,))
            conn.commit()

    def list_tokens(self):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("SELECT token_name, role, description, created_at, revoked FROM tokens")
            return [dict(r) for r in c.fetchall()]

    def validate_token(self, token_plain: str, required_roles: Optional[List[str]] = None) -> bool:
        h = hashlib.sha256(token_plain.encode()).hexdigest()
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("SELECT role FROM tokens WHERE token_hash=? AND revoked=0", (h,))
            row = c.fetchone()
            if not row:
                return False
            role = row["role"]
            if required_roles is None:
                return True
            return role in required_roles

    # Agents
    def register_or_update_agent(self, agent_name: str, host: str, port: int,
                                 capabilities: Dict[str, Any], metadata: Dict[str, Any], status: str = "online"):
        now = datetime.datetime.utcnow().isoformat() + "Z"
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "REPLACE INTO agents (agent_name, host, port, status, capabilities_json, metadata_json, last_seen)"
                " VALUES (?,?,?,?,?,?,?)",
                (agent_name, host, port, status, json.dumps(capabilities or {}), json.dumps(metadata or {}), now),
            )
            conn.commit()

    def heartbeat(self, agent_name: str, status: str, metadata: Dict[str, Any]):
        now = datetime.datetime.utcnow().isoformat() + "Z"
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE agents SET status=?, metadata_json=?, last_seen=? WHERE agent_name=?",
                (status, json.dumps(metadata or {}), now, agent_name),
            )
            if c.rowcount == 0:
                c.execute(
                    "INSERT INTO agents (agent_name, status, capabilities_json, metadata_json, last_seen)"
                    " VALUES (?,?,?,?,?)",
                    (agent_name, status, "{}", json.dumps(metadata or {}), now),
                )
            conn.commit()

    def list_agents(self):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM agents")
            return [dict(r) for r in c.fetchall()]

    # Scripts
    def add_script(self, script_id: str, script_file: str, description: str,
                   allowed_tags, required_approval_levels: int):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "REPLACE INTO scripts (script_id, script_file, description, allowed_tags_json, required_approval_levels)"
                " VALUES (?,?,?,?,?)",
                (script_id, script_file, description, json.dumps(allowed_tags or []), required_approval_levels),
            )
            conn.commit()

    def list_scripts(self):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM scripts")
            return [dict(r) for r in c.fetchall()]

    def get_script(self, script_id: str):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM scripts WHERE script_id=?", (script_id,))
            row = c.fetchone()
            return dict(row) if row else None

    # Workflows
    def create_workflow(self, workflow_id: str, script_id: str, targets,
                        requestor: str, required_levels: int, notify_email: str,
                        ttl_minutes: int, reason: str):
        now = datetime.datetime.utcnow()
        created_at = now.isoformat() + "Z"
        expires_at = (now + datetime.timedelta(minutes=ttl_minutes)).isoformat() + "Z"
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO workflows (workflow_id, script_id, targets_json, requestor, status,"
                " required_approval_levels, approvals_json, notify_email, reason, created_at, expires_at, last_update)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    workflow_id,
                    script_id,
                    json.dumps(targets or []),
                    requestor,
                    "pending",
                    required_levels,
                    "[]",
                    notify_email,
                    reason,
                    created_at,
                    expires_at,
                    created_at,
                ),
            )
            conn.commit()

    def get_workflow(self, workflow_id: str):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM workflows WHERE workflow_id=?", (workflow_id,))
            row = c.fetchone()
            return dict(row) if row else None

    def list_workflows(self, limit: int = 100):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM workflows ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(r) for r in c.fetchall()]

    def update_workflow_status(self, workflow_id: str, status: str):
        now = datetime.datetime.utcnow().isoformat() + "Z"
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE workflows SET status=?, last_update=? WHERE workflow_id=?",
                (status, now, workflow_id),
            )
            conn.commit()

    def add_approval(self, workflow_id: str, approver: str, level: int):
        wf = self.get_workflow(workflow_id)
        if not wf:
            return
        approvals = json.loads(wf.get("approvals_json") or "[]")
        if not any(a.get("approver") == approver for a in approvals):
            approvals.append(
                {
                    "approver": approver,
                    "level": level,
                    "ts": datetime.datetime.utcnow().isoformat() + "Z",
                }
            )
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE workflows SET approvals_json=?, last_update=? WHERE workflow_id=?",
                (json.dumps(approvals), datetime.datetime.utcnow().isoformat() + "Z", workflow_id),
            )
            conn.commit()

    def add_audit(self, workflow_id: str, action: str, actor: str, note: str = ""):
        ts = datetime.datetime.utcnow().isoformat() + "Z"
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO workflow_audit (workflow_id, action, actor, ts, note)"
                " VALUES (?,?,?,?,?)",
                (workflow_id, action, actor, ts, note),
            )
            conn.commit()

    def get_audit(self, workflow_id: str):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT action, actor, ts, note FROM workflow_audit WHERE workflow_id=? ORDER BY ts DESC",
                (workflow_id,),
            )
            return [dict(r) for r in c.fetchall()]

DB_FILE = os.environ.get("DB_FILE", "controller_data/controller.db")
os.makedirs(os.path.dirname(DB_FILE) or ".", exist_ok=True)
_db_instance = DB(DB_FILE)

def get_db() -> DB:
    return _db_instance
