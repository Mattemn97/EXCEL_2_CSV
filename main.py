from pathlib import Path
from typing import List, Tuple, Optional
import re
import pandas as pd
from tqdm import tqdm

# ============================================================
# COSTANTI E MAPPATURE
# ============================================================
IDENT_QUOTE = {"postgres": ("\"", "\""), "mysql": ("`", "`"), "sqlite": ("\"", "\""), "sqlserver": ("[", "]")}
TEXT_TYPE   = {"postgres": "TEXT", "mysql": "TEXT", "sqlite": "TEXT", "sqlserver": "NVARCHAR(MAX)"}
INT_TYPE    = {"postgres": "INTEGER", "mysql": "INT", "sqlite": "INTEGER", "sqlserver": "INT"}
FLOAT_TYPE  = {"postgres": "DOUBLE PRECISION", "mysql": "DOUBLE", "sqlite": "REAL", "sqlserver": "FLOAT"}
DECIMAL_TYPE= {"postgres": "NUMERIC", "mysql": "DECIMAL", "sqlite": "NUMERIC", "sqlserver": "DECIMAL"}
BOOLEAN_TYPE= {"postgres": "BOOLEAN", "mysql": "TINYINT(1)", "sqlite": "INTEGER", "sqlserver": "BIT"}

# ============================================================
# CLASSI DATI
# ============================================================
class ColumnSpec:
    HEADER = "Name,SQL_Type"
    def __init__(self, name: str, sql_type: str):
        self.name = name; self.sql_type = sql_type
    def ddl_str(self, dialect: str) -> str:
        left, right = IDENT_QUOTE[dialect]
        return f"    {left}{self.name}{right} {self.sql_type}"

class TableSQL:
    HEADER = "Table_Name,Columns_Count,Rows_Count"
    def __init__(self, table_name: str, columns: List[ColumnSpec], df: pd.DataFrame):
        self.table_name = table_name; self.columns = columns; self.df = df
    def quoted_name(self, dialect: str) -> str:
        left, right = IDENT_QUOTE[dialect]
        return f"{left}{self.table_name}{right}"
    def create_stmt(self, dialect: str) -> str:
        cols = ",\n".join([c.ddl_str(dialect) for c in self.columns])
        return f"CREATE TABLE {self.quoted_name(dialect)} (\n{cols}\n);\n\n"

# ============================================================
# UTILS
# ============================================================

def sanitize_identifier(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]", "_", name.strip())
    if s and s[0].isdigit(): s = "_" + s
    return (re.sub(r"_+", "_", s).strip("_")) or "col"


def dedup(names: List[str]) -> List[str]:
    seen = {}; out = []
    for n in names:
        if n not in seen: seen[n] = 0; out.append(n)
        else:
            seen[n] += 1; nn = f"{n}_{seen[n]}"
            while nn in seen:
                seen[n] += 1; nn = f"{n}_{seen[n]}"
            seen[nn] = 0; out.append(nn)
    return out


def looks_like_boolean(series: pd.Series) -> bool:
    vals = series.dropna()
    if vals.empty: return False
    valid_str = {"true","false","t","f","y","n","yes","no"}
    count = 0
    for v in vals:
        if isinstance(v, bool): count += 1; continue
        if isinstance(v, (int, float)) and v in (0,1): count += 1; continue
        if isinstance(v, str) and v.strip().lower() in valid_str: count += 1; continue
    return count == len(vals)


def infer_numeric(series: pd.Series):
    """Ritorna (is_integer, is_float, decimal_spec)
    - is_integer: tutti i valori sono interi
    - is_float: valori numerici con parte decimale o scientifica
    - decimal_spec: (precision, scale) se adatto a DECIMAL/NUMERIC
    """
    vals = series.dropna()
    if vals.empty: return False, False, None
    num = pd.to_numeric(vals, errors='coerce')
    if num.isna().any(): return False, False, None
    is_int = all(float(x).is_integer() for x in num)
    if is_int: return True, False, None
    # calcolo precision/scale per DECIMAL
    max_scale, max_prec = 0, 0
    for x in num:
        s = f"{x}"
        if "e" in s.lower():
            return False, True, None
        parts = s.split(".")
        if len(parts) == 1:
            scale = 0; prec = len(parts[0].replace("-",""))
        else:
            int_part, frac_part = parts[0], parts[1]
            scale = len(frac_part.rstrip('0'))
            prec = len(int_part.replace("-","")) + scale
        max_scale = max(max_scale, scale); max_prec = max(max_prec, prec)
    if max_scale > 0:
        return False, False, (min(max_prec, 38), min(max_scale, 18))
    return False, True, None


def infer_text_len(series: pd.Series) -> int:
    vals = series.dropna().astype(str)
    return 0 if vals.empty else int(vals.map(len).max())


def infer_sql_type(series: pd.Series, dialect: str, varchar_threshold: int) -> str:
    # SOLO booleani/numerici; niente DATE/TIMESTAMP
    if looks_like_boolean(series):
        return BOOLEAN_TYPE[dialect]
    is_int, is_float, dec_spec = infer_numeric(series)
    if is_int:
        return INT_TYPE[dialect]
    if dec_spec:
        p, s = dec_spec; return f"{DECIMAL_TYPE[dialect]}({p},{s})"
    if is_float:
        return FLOAT_TYPE[dialect]
    max_len = infer_text_len(series)
    if max_len == 0:
        return TEXT_TYPE[dialect]
    return f"NVARCHAR({max_len})" if dialect == "sqlserver" else (f"VARCHAR({max_len})" if max_len <= varchar_threshold else TEXT_TYPE[dialect])


def format_value(value, col_type: str, dialect: str) -> str:
    # NESSUN parsing data: solo booleani/numerici, altrimenti testo
    if pd.isna(value): return "NULL"
    if col_type in (BOOLEAN_TYPE[dialect],):
        if isinstance(value, str):
            v = value.strip().lower()
            if v in {"true","t","y","yes"}: return "1" if dialect in {"mysql","sqlite","sqlserver"} else "TRUE"
            if v in {"false","f","n","no"}: return "0" if dialect in {"mysql","sqlite","sqlserver"} else "FALSE"
        if isinstance(value, (int,float)):
            iv = 1 if float(value) != 0.0 else 0
            return str(iv) if dialect in {"mysql","sqlite","sqlserver"} else ("TRUE" if iv == 1 else "FALSE")
        if isinstance(value, bool):
            return ("1" if value else "0") if dialect in {"mysql","sqlite","sqlserver"} else ("TRUE" if value else "FALSE")
        v = str(value).strip().lower()
        return "1" if v in {"true","t","y","yes","1"} else ("0" if v in {"false","f","n","no","0"} else "NULL")
    if col_type.startswith(DECIMAL_TYPE[dialect]) or col_type == INT_TYPE[dialect] or col_type == FLOAT_TYPE[dialect]:
        try:
            num = pd.to_numeric(value, errors='coerce')
            if pd.isna(num): return "NULL"
            return str(int(float(num))) if col_type == INT_TYPE[dialect] else str(num)
        except Exception:
            return "NULL"
    s = str(value).replace("'", "''")
    return f"'{s}'"

# ============================================================
# IO EXCEL + SCRITTURA SQL
# ============================================================

def read_excel_any(path: Path, header: bool) -> List[Tuple[str, pd.DataFrame]]:
    ext = path.suffix.lower()
    xl = pd.ExcelFile(path, engine=('openpyxl' if ext=='.xlsx' else 'xlrd'))
    sheets = []
    for name in xl.sheet_names:
        df = xl.parse(name, header=0 if header else None)
        if not header: df.columns = [f"col_{i+1}" for i in range(len(df.columns))]
        sheets.append((name, df))
    return sheets


def scrittura_sql(file_path: Path, lista_stmt: List[str]):
    with open(file_path, "w", encoding="utf-8") as f:
        print(f"Scrivendo: {file_path.name}")
        for s in lista_stmt: f.write(s)
    print(f"Scritto: {file_path.name}")

# ============================================================
# CORE
# ============================================================

def elabora_excel(excel_path: Path, out_sql: Path, dialect: str, varchar_threshold: int, batch_size: int, header: bool):
    sheets = read_excel_any(excel_path, header)
    total_rows = sum(len(df) for _, df in sheets)
    print(f"\n📊 Trovati {len(sheets)} fogli e {total_rows} righe totali.\n")
    all_statements: List[str] = []
    all_statements += [f"-- SQL generato da excel_to_sql_cantools_style.py\n",
                       f"-- Origine: {excel_path.name}\n",
                       f"-- Dialetto: {dialect}\n\n"]
    with tqdm(total=total_rows, desc="🔧 Conversione in corso", unit="riga", dynamic_ncols=True) as pbar:
        for sheet_name, df in sheets:
            if df.empty: continue
            san_names = dedup([sanitize_identifier(str(c) if c is not None else "col") for c in df.columns.tolist()])
            df.columns = san_names
            col_types = [infer_sql_type(df[c], dialect, varchar_threshold) for c in df.columns]
            columns = [ColumnSpec(name, typ) for name, typ in zip(df.columns, col_types)]
            table_name = sanitize_identifier(sheet_name)
            # CREATE
            left, right = IDENT_QUOTE[dialect]
            q_table = f"{left}{table_name}{right}"
            cols_lines = ",\n".join([c.ddl_str(dialect) for c in columns])
            all_statements.append(f"CREATE TABLE {q_table} (\n{cols_lines}\n);\n\n")
            # INSERT batch
            q_cols = ", ".join([f"{left}{c}{right}" for c in df.columns])
            rows = df.to_dict(orient='records')
            for i in range(0, len(rows), batch_size):
                chunk = rows[i:i+batch_size]
                values_sql = []
                for r in chunk:
                    vals = [format_value(r.get(c), col_types[idx], dialect) for idx, c in enumerate(df.columns)]
                    values_sql.append("(" + ", ".join(vals) + ")")
                all_statements.append(f"INSERT INTO {q_table} ({q_cols}) VALUES\n" + ",\n".join(values_sql) + ";\n\n")
            pbar.update(len(df))
    if all_statements: scrittura_sql(out_sql, all_statements)

# ============================================================
# MENU + MAIN
# ============================================================

def menu():
    excel_path = Path(input("👉 Inserisci il percorso completo del file .xlsx/.xls: ").strip())
    if not excel_path.is_file() or excel_path.suffix.lower() not in {".xlsx",".xls"}:
        print("❌ File Excel non valido."); return None
    dialect = (input("👉 Dialetto SQL (postgres/mysql/sqlite/sqlserver) [postgres]: ").strip().lower() or "postgres")
    if dialect not in {"postgres","mysql","sqlite","sqlserver"}:
        print("❌ Dialetto non valido."); return None
    try: varchar_threshold = int(input("👉 Soglia VARCHAR(n) [255]: ").strip() or 255)
    except ValueError: print("❌ Soglia non valida."); return None
    try: batch_size = int(input("👉 Dimensione batch INSERT [1000]: ").strip() or 1000)
    except ValueError: print("❌ Batch size non valida."); return None
    header_ans = (input("👉 La prima riga contiene intestazioni? (s/n) [s]: ").strip().lower() or "s")
    header = header_ans.startswith("s")
    out_sql = excel_path.parent / f"{excel_path.stem}_{dialect}.sql"
    return (excel_path, out_sql, dialect, varchar_threshold, batch_size, header)


def main():
    args = menu()
    if args is None: return
    elabora_excel(*args)

if __name__ == "__main__":
    main()

