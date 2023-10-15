import logging

import aiodistbus

logger = logging.getLogger(__name__)

def test_tree_search():
    t = aiodistbus.Trie()
    t.insert("was")
    t.insert("word")
    t.insert("war")
    t.insert("what")
    t.insert("where")
    assert [k[0] for k in t.query("wh")] == ["what", "where"]
    logger.debug(t.query("wh"))
