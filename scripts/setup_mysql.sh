#!/usr/bin/env bash
# Instala y arranca MySQL 8.4.10 (configuración por defecto) en Colab / Linux.
# Uso:  bash scripts/setup_mysql.sh
# Luego: export MYSQL_PORT=3306 MYSQL_PASSWORD=root
# Requiere pymysql (pip install -r requirements.txt) solo para la verificación final.
set -euo pipefail

DIR=/content/mysql
URL=https://downloads.mysql.com/archives/get/p/23/file/mysql-8.4.10-linux-glibc2.17-x86_64-minimal.tar.xz

apt-get -qq update >/dev/null 2>&1 || true
apt-get -qq install -y libnuma1 >/dev/null 2>&1 || true
apt-get -qq install -y libaio1 >/dev/null 2>&1 || apt-get -qq install -y libaio1t64 >/dev/null 2>&1 || true
# Ubuntu 24.04 renombró la librería; mysqld busca libaio.so.1
if [ ! -e /usr/lib/x86_64-linux-gnu/libaio.so.1 ] && [ -e /usr/lib/x86_64-linux-gnu/libaio.so.1t64 ]; then
  ln -s /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /usr/lib/x86_64-linux-gnu/libaio.so.1
fi

mkdir -p "$DIR"
if [ ! -x "$DIR/bin/mysqld" ]; then
  wget -q -O /tmp/mysql.tar.xz "$URL"
  tar -xJf /tmp/mysql.tar.xz -C "$DIR" --strip-components=1
fi

if [ ! -d "$DIR/data/mysql" ]; then
  "$DIR/bin/mysqld" --initialize-insecure --user=root --basedir="$DIR" --datadir="$DIR/data" >/dev/null 2>&1
fi

# root/root accesible por TCP; idempotente, se aplica en cada arranque
cat > "$DIR/init.sql" <<'SQL'
ALTER USER 'root'@'localhost' IDENTIFIED BY 'root';
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'root';
GRANT ALL ON *.* TO 'root'@'%' WITH GRANT OPTION;
SQL

if ! pgrep -x mysqld >/dev/null; then
  nohup "$DIR/bin/mysqld" --user=root --basedir="$DIR" --datadir="$DIR/data" \
    --port=3306 --bind-address=127.0.0.1 --socket=/tmp/mysql.sock \
    --init-file="$DIR/init.sql" >"$DIR/mysqld.log" 2>&1 &
fi

python3 - <<'PY'
import time, pymysql
for _ in range(90):
    try:
        con = pymysql.connect(host="127.0.0.1", port=3306, user="root", password="root")
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("MySQL no arrancó; revisar /content/mysql/mysqld.log")
with con.cursor() as c:
    c.execute("SELECT VERSION(), @@sql_mode")
    print("MySQL listo:", c.fetchone())
con.close()
PY
