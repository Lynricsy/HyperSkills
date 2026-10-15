# #123 Run row drops committee badges past LIST_LIMIT without saying so

The run row shows at most `LIST_LIMIT` committee badges and, unlike the error
list, has no total beside it. Today there are 8 committees and the limit is 10,
so nothing is dropped. If the committee list ever outgrows the limit, badges
would vanish silently.

Not worth fixing now. Options when it matters: raise `LIST_LIMIT`, or add a
`committeesTotal` beside the list the way `errorsTotal` works.

Status: open since March, labelled `someday`.
