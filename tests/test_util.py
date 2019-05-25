from pyjolt.util import translate


def test_translate():
    assert translate(r'a-*.[]]\s?[0][!9][^d][\[aaa][') == r'(?ms)a\-(.*)\.[]]\\s.[0][^9][\^d][\\[aaa]\[\Z'


