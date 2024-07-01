# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import wn

import garak.probes.base
import garak.probes.topic

TEST_LEXICON = "oewn:2023"
TEST_TERM = "abortion"
TEST_SYNSET_ID = "oewn-00231191-n"

w = wn.Wordnet(TEST_LEXICON)
s = w.synset(TEST_SYNSET_ID)


def test_topic_wordnet_load():
    p = garak.probes.topic.TopicExplorerWordnet()
    assert isinstance(p, garak.probes.base.Probe)


def test_topic_wordnet_version():
    p = garak.probes.topic.TopicExplorerWordnet()
    assert p.lexicon == TEST_LEXICON


def test_topic_wordnet_get_node_terms():
    p = garak.probes.topic.TopicExplorerWordnet()
    terms = p._get_node_terms(s)
    assert list(terms) == ["abortion"]


def test_topic_wordnet_get_node_children():
    p = garak.probes.topic.TopicExplorerWordnet()
    children = p._get_node_children(s)
    assert children == [wn.synset("oewn-00231342-n"), wn.synset("oewn-00232028-n")]


def test_topic_wordnet_get_node_id():
    p = garak.probes.topic.TopicExplorerWordnet()
    assert p._get_node_id(s) == TEST_SYNSET_ID


def test_topic_wordnet_get_initial_nodes():
    p = garak.probes.topic.TopicExplorerWordnet()
    p.target_topic = TEST_TERM
    initial_nodes = p._get_initial_nodes()
    assert initial_nodes == [
        s,
        wn.synset("oewn-07334252-n"),
        wn.synset("oewn-00231342-n"),
        wn.synset("oewn-00232028-n"),
    ]
