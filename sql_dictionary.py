# sql keywords
keywords = [
"all", "and", "any", "as", "asc", "between", "by", "cast", "corresponding", "create", "cross", "delete", "desc", "distinct", "drop", "escape", "except", "exists", "from", "full", "global", "group", "having", "in", "inner", "insert", "intersect", "into", "is", "join", "left", "like", "limit", "local", "match", "natural", "not", "offset", "on", "or", "order", "outer", "right", "select", "set", "some", "table", "temporary", "union", "unique", "unknown", "update", "using", "values", "where" 
]

# functions
functions = [
"abs","changes","coalesce","glob","ifnull","hex","last_insert_rowid","length","like","lower","ltrim",
"max","min","nullif","quote","random","randomblob","replace","round","rtrim","soundex","total_change",
"trim","typeof","upper","zeroblob","date","datetime","julianday","strftime","avg","count","group_concat","sum","total"
]

# constants
constants = [ "null", "false", "true" ]

def getSqlDictionary():
	return { 'keyword' : keywords, 'constant' : constants, 'function' : functions }

