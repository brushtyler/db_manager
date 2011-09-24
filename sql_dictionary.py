# sql keywords
keywords = [
"action", "add", "after", "all", "alter", "analyze", "and", "as", "asc", 
"before", "begin", "between", "by", "cascade", "case", "cast", "check", 
"collate", "column", "commit", "constraint", "create", "cross", "current_date", 
"current_time", "current_timestamp", "default", "deferrable", "deferred", 
"delete", "desc", "distinct", "drop", "each", "else", "end", "escape", 
"except", "exists", "for", "foreign", "from", "full", "group", "having", 
"ignore", "immediate", "in", "initially", "inner", "insert", "intersect", 
"into", "is", "isnull", "join", "key", "left", "like", "limit", "match", 
"natural", "no", "not", "notnull", "null", "of", "offset", "on", "or", "order", 
"outer", "primary", "references", "release", "restrict", "right", "rollback", 
"row", "savepoint", "select", "set", "table", "temporary", "then", "to", 
"transaction", "trigger", "union", "unique", "update", "using", "values", 
"view", "when", "where"
]

# sqlite keywords
sqlite_keywords = [
"abort", "attach", "autoincrement", "conflict", "database", "detach", 
"exclusive", "explain", "fail", "glob", "if", "index", "indexed", "instead", 
"plan", "pragma", "query", "raise", "regexp", "reindex", "rename", "replace", 
"temp", "vacuum", "virtual"
]

# postgresql keywords
postgresql_keywords = [
"absolute", "admin", "aggregate", "alias", "allocate", "analyse", "any", "are", 
"array", "asensitive", "assertion", "asymmetric", "at", "atomic", 
"authorization", "avg", "bigint", "binary", "bit", "bit_length", "blob", 
"boolean", "both", "breadth", "call", "called", "cardinality", "cascaded", 
"catalog", "ceil", "ceiling", "char", "character", "character_length", 
"char_length", "class", "clob", "close", "coalesce", "collation", "collect", 
"completion", "condition", "connect", "connection", "constraints", 
"constructor", "continue", "convert", "corr", "corresponding", "count", 
"covar_pop", "covar_samp", "cube", "cume_dist", "current", 
"current_default_transform_group", "current_path", "current_role", 
"current_transform_group_for_type", "current_user", "cursor", "cycle", "data", 
"date", "day", "deallocate", "dec", "decimal", "declare", "dense_rank", 
"depth", "deref", "describe", "descriptor", "destroy", "destructor", 
"deterministic", "diagnostics", "dictionary", "disconnect", "do", "domain", 
"double", "dynamic", "element", "end-exec", "equals", "every", "exception", 
"exec", "execute", "exp", "external", "extract", "false", "fetch", "filter", 
"first", "float", "floor", "found", "free", "freeze", "function", "fusion", 
"general", "get", "global", "go", "goto", "grant", "grouping", "hold", "host", 
"hour", "identity", "ilike", "indicator", "initialize", "inout", "input", 
"insensitive", "int", "integer", "intersection", "interval", "isolation", 
"iterate", "language", "large", "last", "lateral", "leading", "less", "level", 
"ln", "local", "localtime", "localtimestamp", "locator", "lower", "map", "max", 
"member", "merge", "method", "min", "minute", "mod", "modifies", "modify", 
"module", "month", "multiset", "names", "national", "nchar", "nclob", "new", 
"next", "none", "normalize", "nullif", "numeric", "object", "octet_length", 
"off", "old", "only", "open", "operation", "option", "ordinality", "out", 
"output", "over", "overlaps", "overlay", "pad", "parameter", "parameters", 
"partial", "partition", "path", "percentile_cont", "percentile_disc", 
"percent_rank", "placing", "position", "postfix", "power", "precision", 
"prefix", "preorder", "prepare", "preserve", "prior", "privileges", 
"procedure", "public", "range", "rank", "read", "reads", "real", "recursive", 
"ref", "referencing", "regr_avgx", "regr_avgy", "regr_count", "regr_intercept", 
"regr_r2", "regr_slope", "regr_sxx", "regr_sxy", "regr_syy", "relative", 
"result", "return", "returning", "returns", "revoke", "role", "rollup", 
"routine", "rows", "row_number", "schema", "scope", "scroll", "search", 
"second", "section", "sensitive", "sequence", "session", "session_user", 
"sets", "similar", "size", "smallint", "some", "space", "specific", 
"specifictype", "sql", "sqlcode", "sqlerror", "sqlexception", "sqlstate", 
"sqlwarning", "sqrt", "start", "state", "statement", "static", "stddev_pop", 
"stddev_samp", "structure", "submultiset", "substring", "sum", "symmetric", 
"system", "system_user", "tablesample", "terminate", "than", "time", 
"timestamp", "timezone_hour", "timezone_minute", "trailing", "translate", 
"translation", "treat", "trim", "true", "uescape", "under", "unknown", 
"unnest", "upper", "usage", "user", "value", "varchar", "variable", "varying", 
"var_pop", "var_samp", "verbose", "whenever", "width_bucket", "window", "with", 
"within", "without", "work", "write", "xml", "xmlagg", "xmlattributes", 
"xmlbinary", "xmlcomment", "xmlconcat", "xmlelement", "xmlforest", 
"xmlnamespaces", "xmlparse", "xmlpi", "xmlroot", "xmlserialize", "year", "zone"
]

# functions
functions = [
"abs", "changes", "coalesce", "glob", "ifnull", "hex", "last_insert_rowid", 
"length", "like", "lower", "ltrim", "max", "min", "nullif", "quote", "random", 
"randomblob", "replace", "round", "rtrim", "soundex", "total_change", "trim", 
"typeof", "upper", "zeroblob", "date", "datetime", "julianday", "strftime", 
"avg", "count", "group_concat", "sum", "total"
]

# constants
constants = [ "null", "false", "true" ]

def getSqlDictionary(db=None):
	k, c, f = list(keywords), list(constants), list(functions)

	if db == None: 
		db = ''
	db = unicode(db).lower()

	if db in ['sqlite', 'spatialite', 'sl']:
		k.extend( sqlite_keywords )

	elif db in ['postgres', 'postgresql', 'postgis', 'pg']:
		k.extend( postgresql_keywords )

	return { 'keyword' : k, 'constant' : c, 'function' : f }

